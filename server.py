from flask import Flask, jsonify, send_from_directory, request
from datetime import datetime, timezone, timedelta

app = Flask(__name__, static_folder='static')

online_users = {}
TIMEOUT_SECONDS = 30

@app.before_request
def track_user():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    now = datetime.now(timezone.utc)
    online_users[ip] = now

@app.route('/online')
def online():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=TIMEOUT_SECONDS)

    ips_to_delete = [ip for ip, last_seen in online_users.items() if last_seen < cutoff]
    for ip in ips_to_delete:
        del online_users[ip]

    count = len(online_users)
    return jsonify({'count': count})

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
