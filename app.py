from flask import Flask, request, jsonify
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

app = Flask(__name__)

# --- Cấu hình API ---
# Cập nhật API JWT mới theo yêu cầu
JWT_SERVICE_URL = "https://communityayabot.spcfy.eu/get/token"
API_ADD_FRIEND = "https://clientbp.ggpolarbear.com/RequestAddingFriend"
API_REMOVE_FRIEND = "https://clientbp.ggpolarbear.com/RemoveFriend"

# Key và IV cho AES
AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# --- Hàm hỗ trợ ---

def encrypt_data(plain_text):
    if isinstance(plain_text, str):
        plain_text = bytes.fromhex(plain_text)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
    return cipher_text.hex()

def encode_id(number):
    number = int(number)
    encoded_bytes = []
    while True:
        byte = number & 0x7F
        number >>= 7
        if number:
            byte |= 0x80
        encoded_bytes.append(byte)
        if not number:
            break
    return bytes(encoded_bytes).hex()

def get_jwt_token(uid, password):
    try:
        # Sử dụng cấu trúc acc={uid}:{password} như yêu cầu
        params = {'acc': f"{uid}:{password}"}
        response = requests.get(JWT_SERVICE_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Trả về token từ JSON (hỗ trợ cả dạng list hoặc dict)
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("BearerAuth")
            return data.get("BearerAuth")
        return None
    except Exception as e:
        print(f"Lỗi kết nối API JWT: {e}")
        return None

def process_friend_action(api_url, xID, jwt_token, is_add=True):
    enc_id = encode_id(xID)
    # 1801 cho Add, 1802 cho Remove
    suffix = "1801" if is_add else "1802"
    payload = f"08a7c4839f1e10{enc_id}{suffix}"
    enc_data = encrypt_data(payload)
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB51",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; Android 9)",
        "Connection": "Keep-Alive"
    }
    
    try:
        resp = requests.post(api_url, headers=headers, data=bytes.fromhex(enc_data), timeout=10)
        return resp.status_code == 200
    except:
        return False

# --- Routes ---

@app.route('/api/add/<xID>/<uid>/<password>', methods=['GET'])
def add_friend(xID, uid, password):
    token = get_jwt_token(uid, password)
    if not token:
        return jsonify({"status": "failed", "reason": "Lấy Token thất bại"}), 401
    
    if process_friend_action(API_ADD_FRIEND, xID, token, is_add=True):
        return jsonify({
            "status": "success",
            "message": "Đã gửi lời mời kết bạn",
            "target_id": xID
        })
    return jsonify({"status": "failed", "reason": "Không thể gửi yêu cầu"}), 400

@app.route('/api/remove/<xID>/<uid>/<password>', methods=['GET'])
def remove_friend(xID, uid, password):
    token = get_jwt_token(uid, password)
    if not token:
        return jsonify({"status": "failed", "reason": "Lấy Token thất bại"}), 401
    
    if process_friend_action(API_REMOVE_FRIEND, xID, token, is_add=False):
        return jsonify({
            "status": "success",
            "message": "Đã xóa bạn bè thành công",
            "target_id": xID
        })
    return jsonify({"status": "failed", "reason": "Không thể thực hiện xóa"}), 400
