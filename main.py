from flask import Flask, render_template, request, jsonify, redirect, session, url_for from datetime import datetime, timedelta import random, string, base64 from Crypto.Cipher import AES from Crypto.Util.Padding import unpad

app = Flask(name) app.secret_key = 'Hr857#hcj@9-_tuhbku@54'

Security constraints

ALLOWED_IP = "110.225.83.116" ALLOWED_DEVICE_ID = "445f2fab2411a480" ENCRYPTION_KEY = b"Hr857#hcj@9-_tuhbku@54"[:32]

Admin credentials

ADMIN_USERNAME = "adminv2" ADMIN_PASSWORD = "myp@ssword"

Key storage

KEYS = { 'QLBSL81ZBYTB': {"type": "1M", "devices": 1, "expires": datetime.now() + timedelta(days=30), "used_devices": [], "blocked": False}, 'VPU77IJI0BXL': {"type": "1M", "devices": 1, "expires": datetime.now() + timedelta(days=30), "used_devices": [], "blocked": False}, }

active_sessions = [] blocked_devices = []

def generate_new_key(): while True: key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12)) if key not in KEYS: KEYS[key] = {"type": "1M", "devices": 1, "expires": datetime.now() + timedelta(days=30), "used_devices": [], "blocked": False} return key

def decrypt_payload(encrypted_b64): try: encrypted_data = base64.b64decode(encrypted_b64) iv = encrypted_data[:16] cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv) decrypted_data = unpad(cipher.decrypt(encrypted_data[16:]), AES.block_size) return eval(decrypted_data.decode()) except Exception: return None

@app.route('/login', methods=['GET', 'POST']) def login(): if request.method == 'POST': data = request.get_json() if data['username'] == ADMIN_USERNAME and data['password'] == ADMIN_PASSWORD: session['logged_in'] = True return jsonify({"success": True}) return jsonify({"success": False, "error": "Invalid credentials"}) return render_template("login.html")

@app.route('/') def index(): if not session.get('logged_in'): return redirect(url_for('login')) return render_template("dashboard.html")

@app.route('/mobile-dashboard') def mobile_dashboard(): if not session.get('logged_in'): return redirect(url_for('login')) return render_template("mobile_dashboard.html")

@app.route('/status') def status(): active = sum(1 for s in active_sessions) activated = len({s['key'] for s in active_sessions}) return jsonify({"active_users": active, "activated_keys": activated})

@app.route('/user-details') def user_details(): return jsonify(active_sessions)

@app.route('/blocked-devices') def get_blocked(): return jsonify({'blocked': blocked_devices})

@app.route('/activate', methods=['POST']) def activate(): encrypted = request.get_json().get("data") decrypted = decrypt_payload(encrypted) if not decrypted: return jsonify({'error': 'Decryption failed'}), 400

if request.remote_addr != ALLOWED_IP or decrypted['device_id'] != ALLOWED_DEVICE_ID:
    return jsonify({'error': 'Access Denied'}), 403

key = decrypted['key']
device_id = decrypted['device_id']
if device_id in blocked_devices:
    return jsonify({'error': 'This device is blocked'}), 403
if key not in KEYS:
    return jsonify({'error': 'Invalid key'}), 400

key_data = KEYS[key]
if key_data['blocked']:
    return jsonify({'error': 'This key is blocked'}), 400

if device_id not in key_data['used_devices']:
    if len(key_data['used_devices']) < key_data['devices']:
        key_data['used_devices'].append(device_id)
    else:
        return jsonify({'error': 'Device limit reached'}), 403

active_sessions.append({
    'key': key,
    'device_id': device_id,
    'ip': decrypted['ip'],
    'country': decrypted['country'],
    'phone': decrypted['phone'],
    'os': decrypted['os'],
    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'status': 'Online'
})
return jsonify({'message': 'Key activated successfully'})

@app.route('/disconnect', methods=['POST']) def disconnect(): device_id = request.get_json()['device_id'] global active_sessions key_to_remove = None active_sessions = [s for s in active_sessions if not (s['device_id'] == device_id and (key_to_remove := s['key']))] if key_to_remove and device_id in KEYS[key_to_remove]['used_devices']: KEYS[key_to_remove]['used_devices'].remove(device_id) return jsonify({'message': f'Device {device_id} disconnected'})

@app.route('/block-device', methods=['POST']) def block_device(): device_id = request.get_json()['device_id'] key_to_block = None global active_sessions active_sessions = [s for s in active_sessions if not (s['device_id'] == device_id and (key_to_block := s['key']))] if device_id not in blocked_devices: blocked_devices.append(device_id) if key_to_block and key_to_block in KEYS: del KEYS[key_to_block] new_key = generate_new_key() return jsonify({'message': f'Device {device_id} blocked. New key: {new_key}'})

@app.route('/unblock-device', methods=['POST']) def unblock_device(): device_id = request.get_json()['device_id'] if device_id in blocked_devices: blocked_devices.remove(device_id) return jsonify({'message': f'Device {device_id} unblocked'}) return jsonify({'error': 'Device not found'}), 404

if name == 'main': app.run(host='0.0.0.0', port=3000)

