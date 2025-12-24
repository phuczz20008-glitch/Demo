from flask import Flask, request, jsonify
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from datetime import datetime

app = Flask(__name__)

# ================= CONFIG =================

OB51xJWT = "https://steve-jwt-v3.vercel.app"
OB51xADD = "https://clientbp.ggpolarbear.com/RequestAddingFriend"
OB51xREMOVE = "https://clientbp.ggpolarbear.com/RemoveFriend"

# UID / PASS
DEFAULT_UID = "4357939535"
DEFAULT_PASS = "ngocduc_demo_P12L2"

# AES KEY / IV
xK = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
xV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

CREATED_BY = "@Convitduc1"

# ================= UTILS =================

def now_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def encrypt_data(plain_text):
    if isinstance(plain_text, str):
        plain_text = bytes.fromhex(plain_text)
    cipher = AES.new(xK, AES.MODE_CBC, xV)
    return cipher.encrypt(pad(plain_text, AES.block_size)).hex()

def encode_id(number):
    number = int(number)
    out = []
    while True:
        b = number & 0x7F
        number >>= 7
        if number:
            b |= 0x80
        out.append(b)
        if not number:
            break
    return bytes(out).hex()

def GeTxJwT(uid, password):
    try:
        r = requests.get(
            f"{OB51xJWT}/token?uid={uid}&password={password}",
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return data[0].get("token")
            return data.get("token")
    except:
        pass
    return None

def post_game_api(url, jwt, enc_hex):
    return requests.post(
        url,
        headers={
            "Authorization": f"Bearer {jwt}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB51",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0",
        },
        data=bytes.fromhex(enc_hex),
        timeout=10
    )

# ================= ROUTES =================

# -------- ADD FRIEND --------
@app.route('/add/<xID>', methods=['GET'])
@app.route('/add/<xID>/<uid>/<password>', methods=['GET'])
def add_friend(xID, uid=None, password=None):
    uid = uid or DEFAULT_UID
    password = password or DEFAULT_PASS

    jwt = GeTxJwT(uid, password)
    if not jwt:
        return jsonify({
            "success": False,
            "error": "JWT_ERROR",
            "created_by": CREATED_BY,
            "time": now_time(),
            "message": "Không lấy được JWT"
        }), 401

    payload = f"08a7c4839f1e10{encode_id(xID)}1801"
    enc_data = encrypt_data(payload)

    try:
        r = post_game_api(OB51xADD, jwt, enc_data)
        if r.status_code == 200:
            return jsonify({
                "success": True,
                "action": "add_friend",
                "player_id": xID,
                "using_uid": uid,
                "created_by": CREATED_BY,
                "time": now_time(),
                "message": "Gửi yêu cầu kết bạn thành công"
            })
        return jsonify({
            "success": False,
            "error": "PLAYER_NOT_FOUND",
            "created_by": CREATED_BY,
            "time": now_time(),
            "message": "Không tìm thấy người chơi"
        }), 400
    except:
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "created_by": CREATED_BY,
            "time": now_time(),
            "message": "Lỗi server"
        }), 500

# -------- REMOVE FRIEND --------
@app.route('/remove/<xID>', methods=['GET'])
@app.route('/remove/<xID>/<uid>/<password>', methods=['GET'])
def remove_friend(xID, uid=None, password=None):
    uid = uid or DEFAULT_UID
    password = password or DEFAULT_PASS

    jwt = GeTxJwT(uid, password)
    if not jwt:
        return jsonify({
            "success": False,
            "error": "JWT_ERROR",
            "created_by": CREATED_BY,
            "time": now_time(),
            "message": "Không lấy được JWT"
        }), 401

    payload = f"08a7c4839f1e10{encode_id(xID)}1802"
    enc_data = encrypt_data(payload)

    try:
        r = post_game_api(OB51xREMOVE, jwt, enc_data)
        if r.status_code == 200:
            return jsonify({
                "success": True,
                "action": "remove_friend",
                "player_id": xID,
                "using_uid": uid,
                "created_by": CREATED_BY,
                "time": now_time(),
                "message": "Đã xoá bạn thành công"
            })
        return jsonify({
            "success": False,
            "error": "PLAYER_NOT_FOUND",
            "created_by": CREATED_BY,
            "time": now_time(),
            "message": "Không tìm thấy người chơi"
        }), 400
    except:
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "created_by": CREATED_BY,
            "time": now_time(),
            "message": "Lỗi server"
        }), 500

# ================= RUN =================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)