"""
Flask network diagnostics endpoint for pinging a host name.
Author: Qwythos
Created by: Empero AI

Security considerations:
- Input validation: Ensure the hostname is a non-empty string.
- Rate limiting: Use Flask-Limiter to prevent abuse.
- Error handling: Return structured JSON responses with appropriate status codes.
- Dependencies: Flask, Flask-Limiter, requests, dnspython.
"""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from dns import resolver, exceptions as dns_exceptions
import socket

app = Flask(__name__)

# Initialize rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)

# Configuration
PING_TIMEOUT = 5  # seconds
PING_COUNT = 1
PING_SIZE = 56  # bytes (standard ping size)

@app.route("/ping", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def ping_host():
    # Parse hostname from query param or JSON body
    hostname = request.args.get("hostname")
    if not hostname:
        if request.is_json:
            data = request.get_json(silent=True)
            hostname = data.get("hostname")
        else:
            return jsonify({"error": "Missing 'hostname' parameter"}), 400

    if not isinstance(hostname, str) or not hostname.strip():
        return jsonify({"error": "Hostname must be a non-empty string"}), 400

    hostname = hostname.strip()

    try:
        # Resolve hostname to IP (handles DNS)
        resolver.reset()
        try:
            addr_info = resolver.resolve(hostname, "A")
            ip = addr_info[0].address
        except dns_exceptions.NXDOMAIN:
            return jsonify({"error": f"DNS resolution failed: {hostname} not found"}), 404
        except dns_exceptions.DNSException as e:
            return jsonify({"error": f"DNS resolution error: {str(e)}"}), 500

        # Perform ICMP ping via subprocess (requires 'ping' CLI tool)
        # Note: For pure Python without external tools, we could use socket,
        # but ICMP requires raw sockets and OS-specific handling.
        # We assume the environment has 'ping' available (common on Linux/macOS).
        import subprocess
        result = subprocess.run(
            ["ping", "-c", str(PING_COUNT), "-W", str(PING_TIMEOUT), "-s", str(PING_SIZE), ip],
            capture_output=True,
            text=True,
            timeout=PING_TIMEOUT + 1,
        )

        # Parse output (simplified; adjust regex if needed)
        lines = result.stdout.splitlines()
        output_lines = []
        for line in lines:
            line = line.strip()
            if line:
                output_lines.append(line)

        return jsonify({
            "hostname": hostname,
            "ip": ip,
            "output": output_lines,
            "status_code": result.returncode,
        }), 200

    except FileNotFoundError:
        return jsonify({"error": "Ping utility not found. Ensure 'ping' is installed and in PATH."}), 501
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Ping timed out."}), 504
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
