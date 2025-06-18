import os
import requests
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, static_folder='static', template_folder='templates')

# Configuration for the robot arm's IP address.
# You can set an environment variable ROBOT_IP, or it will default to 192.168.1.1.
ROBOT_IP = os.environ.get("ROBOT_IP", "192.168.1.1")
ROBOT_URL = f"http://{ROBOT_IP}"

@app.route('/')
def index():
    """Serves the main page of the web UI."""
    return render_template('index.html')

@app.route('/api/command')
def command():
    """
    Proxies a JSON command to the robot arm.
    This avoids CORS issues in the browser.
    """
    json_str = request.args.get('json', '{}')
    try:
        # The robot expects a raw JSON string in the 'json' query parameter.
        url = f"{ROBOT_URL}/js?json={json_str}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        # The robot arm's response might not have the correct JSON content type.
        # We'll try to parse it as JSON, but fall back to returning plain text if that fails.
        try:
            return jsonify(response.json())
        except json.JSONDecodeError:
            return response.text, 200, {'Content-Type': 'text/plain'}
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to connect to robot at {ROBOT_URL}. Error: {e}"}), 500

if __name__ == '__main__':
    # Running on 0.0.0.0 makes the server accessible on the local network.
    app.run(host='0.0.0.0', port=5000, debug=True) 