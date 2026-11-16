"""
Flask network diagnostics endpoint that pings a host name given by the client.
Returns the output of the ping command as a JSON response.

Author: Qwythos
Created by: Empero AI
"""

from flask import Flask, request, jsonify
import subprocess
import socket
import sys

app = Flask(__name__)

PING_TIMEOUT = 3  # seconds


@app.route("/ping", methods=["POST"])
def ping_host():
    """
    Receives a JSON payload with a 'hostname' field and returns the result of pinging that host.
    """
    # Parse JSON body
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    if not data or "hostname" not in data:
        return jsonify({"error": "Missing 'hostname' field"}), 400

    hostname = data["hostname"]

    # Basic validation: hostname must be a non-empty string
    if not isinstance(hostname, str) or not hostname.strip():
        return jsonify({"error": "hostname must be a non-empty string"}), 400

    # Resolve hostname to IP to ensure it's a valid DNS name (optional security check)
    try:
        socket.getaddrinfo(hostname, None, socket.AF_INET)
    except socket.gaierror:
        return jsonify({"error": f"Cannot resolve hostname: {hostname}"}), 400

    # Execute ping command
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(PING_TIMEOUT), hostname],
            capture_output=True,
            text=True,
            timeout=PING_TIMEOUT + 5,  # small buffer for process termination
            env={**os.environ, "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
        )
    except FileNotFoundError:
        # ping not found (unlikely on standard Linux, but handle gracefully)
        return jsonify({"error": "ping command not found"}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Ping timed out after {PING_TIMEOUT} seconds"}), 504
    except Exception as e:
        return jsonify({"error": f"Unexpected error while pinging {hostname}: {str(e)}"}), 500

    # Build response
    response = {
        "hostname": hostname,
        "ip_address": result.stdout.split()[0] if result.stdout and "PING" in result.stdout else None,
        "status_code": result.returncode,
        "output": result.stdout.strip(),
        "stderr": result.stderr.strip() if result.stderr else "",
    }

    return jsonify(response)


if __name__ == "__main__":
    import os
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
