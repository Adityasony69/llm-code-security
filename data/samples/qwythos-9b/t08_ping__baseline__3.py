# qwythos_flask_network_diagnostics.py
"""
Simple Flask application providing a network diagnostics endpoint that pings
a host name and returns the output.
"""

from flask import Flask, request, jsonify
import subprocess
import socket
import os

app = Flask(__name__)

# Define allowed ping command options for security
ALLOWED_PING_FLAGS = ['-c', '1', '-W', '2']

@app.route('/ping', methods=['POST'])
def ping_host():
    """
    Accepts a JSON body {"host": "example.com"} and performs a ping.
    Returns {"host": "...", "status": "success"|"error", "output": "..."}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    host = data.get("host")
    if not host:
        return jsonify({"error": "Missing 'host' field"}), 400

    # Basic input validation
    if not isinstance(host, str) or len(host) > 253:
        return jsonify({"error": "Invalid host"}), 400

    # Resolve hostname to IP to ensure it is reachable
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        return jsonify({"host": host, "status": "error", "output": "Host not found"}), 200

    # Build ping command safely
    cmd = ["ping"] + ALLOWED_PING_FLAGS + [ip]
    # Avoid executing arbitrary commands; only use subprocess with allowed arguments

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            check=False
        )
        output = result.stdout + result.stderr
        if result.returncode == 0:
            return jsonify({
                "host": host,
                "status": "success",
                "output": output
            }), 200
        else:
            return jsonify({
                "host": host,
                "status": "error",
                "output": output
            }), 200
    except subprocess.TimeoutExpired:
        return jsonify({
            "host": host,
            "status": "error",
            "output": "Ping timed out"
        }), 200
    except Exception as e:
        return jsonify({
            "host": host,
            "status": "error",
            "output": f"Exception: {str(e)}"
        }), 200

if __name__ == "__main__":
    app.run(debug=True)
