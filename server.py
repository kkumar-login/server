from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)
app.secret_key = 'secret-key-123'

# Activation Keys Setup
KEYS = {
    'QLBSL81ZBYTB': {"type": "1M", "devices": 1, "expires": datetime.now() + timedelta(days=30), "used_devices": [], "blocked": False},
    'VPU77IJI0BXL': {"type": "1M", "devices": 1, "expires": datetime.now() + timedelta(days=30), "used_devices": [], "blocked": False},
    '561CKCJMMK3A': {"type": "1M", "devices": 1, "expires": datetime.now() + timedelta(days=30), "used_devices": [], "blocked": False},
    '9OUJYYCR5ALL': {"type": "1M", "devices": 1, "expires": datetime.now() + timedelta(days=30), "used_devices": [], "blocked": False},
    'XGPLAD02K96R': {"type": "1M", "devices": 1, "expires": datetime.now() + timedelta(days=30), "used_devices": [], "blocked": False},
    'GAEOQNXJQI9J': {"type": "2M", "devices": 3, "expires": datetime.now() + timedelta(days=60), "used_devices": [], "blocked": False},
    '43VYB5VJYLM9': {"type": "2M", "devices": 3, "expires": datetime.now() + timedelta(days=60), "used_devices": [], "blocked": False},
    '9R45OIJKZ71Q': {"type": "2M", "devices": 3, "expires": datetime.now() + timedelta(days=60), "used_devices": [], "blocked": False},
    'T16CIBJ4AL79': {"type": "2M", "devices": 3, "expires": datetime.now() + timedelta(days=60), "used_devices": [], "blocked": False},
    'SP7U5AVLNM5H': {"type": "2M", "devices": 3, "expires": datetime.now() + timedelta(days=60), "used_devices": [], "blocked": False},
    'D578B8LNI61D': {"type": "3M", "devices": 5, "expires": datetime.now() + timedelta(days=90), "used_devices": [], "blocked": False},
    'I35OF878G4ES': {"type": "3M", "devices": 5, "expires": datetime.now() + timedelta(days=90), "used_devices": [], "blocked": False},
    'WM7LIP73XR09': {"type": "3M", "devices": 5, "expires": datetime.now() + timedelta(days=90), "used_devices": [], "blocked": False},
    'PC9ZLK2VITSI': {"type": "3M", "devices": 5, "expires": datetime.now() + timedelta(days=90), "used_devices": [], "blocked": False},
    'G4F2FO6CUSA2': {"type": "3M", "devices": 5, "expires": datetime.now() + timedelta(days=90), "used_devices": [], "blocked": False},
}

active_sessions = []
blocked_devices = []

def generate_new_key():
    while True:
        key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        if key not in KEYS:
            KEYS[key] = {
                "type": "1M",
                "devices": 1,
                "expires": datetime.now() + timedelta(days=30),
                "used_devices": [],
                "blocked": False
            }
            return key

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/status')
def status():
    active = sum(1 for s in active_sessions)
    activated = len({s['key'] for s in active_sessions})
    return jsonify({"active_users": active, "activated_keys": activated})

@app.route('/user-details')
def user_details():
    return jsonify(active_sessions)

@app.route('/blocked-devices')
def get_blocked():
    return jsonify({'blocked': blocked_devices})

@app.route('/activate', methods=['POST'])
def activate():
    data = request.get_json()
    key = data['key']
    device_id = data['device_id']

    if device_id in blocked_devices:
        return jsonify({'error': 'This device is blocked'}), 403

    if key not in KEYS:
        return jsonify({'error': 'Invalid key'}), 400

    key_data = KEYS[key]

    if key_data['blocked']:
        return jsonify({'error': 'This key is blocked'}), 400

    if device_id not in key_data["used_devices"]:
        if len(key_data["used_devices"]) < key_data["devices"]:
            key_data["used_devices"].append(device_id)
        else:
            return jsonify({'error': 'Device limit reached'}), 403

    active_sessions.append({
        'key': key,
        'device_id': device_id,
        'ip': data['ip'],
        'country': data['country'],
        'phone': data['phone'],
        'os': data['os'],
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'Online'
    })

    return jsonify({'message': 'Key activated successfully'})

@app.route('/disconnect', methods=['POST'])
def disconnect():
    data = request.get_json()
    device_id = data['device_id']
    global active_sessions
    key_to_remove = None
    active_sessions = [s for s in active_sessions if not (s['device_id'] == device_id and (key_to_remove := s['key']))]
    if key_to_remove and device_id in KEYS[key_to_remove]["used_devices"]:
        KEYS[key_to_remove]["used_devices"].remove(device_id)
    return jsonify({'message': f'Device {device_id} disconnected'})

@app.route('/block-device', methods=['POST'])
def block_device():
    data = request.get_json()
    device_id = data['device_id']
    key_to_block = None

    global active_sessions
    active_sessions = [s for s in active_sessions if not (
        s['device_id'] == device_id and (key_to_block := s['key'])
    )]

    if device_id not in blocked_devices:
        blocked_devices.append(device_id)

    if key_to_block:
        # Remove the old key entirely
        if key_to_block in KEYS:
            del KEYS[key_to_block]

        # Add new key
        new_key = generate_new_key()

        return jsonify({
            'message': f'Device {device_id} blocked. Key {key_to_block} removed. New key: {new_key}'
        })

    return jsonify({'message': f'Device {device_id} blocked'})

@app.route('/unblock-device', methods=['POST'])
def unblock_device():
    device_id = request.get_json()['device_id']
    if device_id in blocked_devices:
        blocked_devices.remove(device_id)
        return jsonify({'message': f'Device {device_id} unblocked'})
    return jsonify({'error': 'Device not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)