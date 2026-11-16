"""
Flask network diagnostics endpoint that pings a host name given by the client.
Returns the raw output of the ping command.

Requirements:
- Flask
- subprocess

Usage:
    POST /diagnostics/ping with JSON body {"host": "example.com"}
    Response: JSON {"status": "success", "output": "..."} or {"status": "error", "message": "..."}
"""

import subprocess
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

PING_TIMEOUT_SECONDS = 5  # Adjust as needed for the environment

@app.route('/diagnostics/ping', methods=['POST'])
def ping_host():
    data = request.get_json()
    if not data or 'host' not in data:
        return jsonify({"status": "error", "message": "Missing 'host' in request body"}), 400

    host = data['host']
    try:
        # Use ping with a short timeout; fallback to 'ping -c 1' on Windows
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(PING_TIMEOUT_SECONDS), host],
            capture_output=True,
            text=True,
            timeout=PING_TIMEOUT_SECONDS + 2
        )
    except FileNotFoundError:
        # ping not found (e.g., Windows without ping installed)
        return jsonify({
            "status": "error",
            "message": "ping command not found"
        }), 501
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error",
            "message": "ping timed out"
        }), 504

    return jsonify({
        "status": "success",
        "output": result.stdout + result.stderr
    })

if __name__ == "__main__":
    app.run(debug=True)
