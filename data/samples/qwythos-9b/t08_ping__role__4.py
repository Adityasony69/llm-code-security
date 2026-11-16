"""
Flask application with a network diagnostics endpoint that pings a host name.
Author: Qwythos
Created by: Empero AI

This module provides a secure Flask application with a single endpoint `/ping`
that accepts a hostname query parameter and returns the output of the `ping`
command. It includes input validation, rate limiting, and output sanitization
to ensure robustness against common security issues.
"""

import os
import subprocess
import re
from flask import Flask, request, jsonify, g
from functools import wraps

app = Flask(__name__)

# Configuration
PING_CMD = ["ping", "-c", "1", "-W", "1"]  # Limit to 1 packet, 1 second timeout
MAX_OUTPUT_LENGTH = 5000
RATE_LIMIT_STORE = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 10  # requests per window


def sanitize_output(output: str) -> str:
    """
    Sanitize the ping output by removing newlines and truncating to max length.
    """
    output = output.replace("\n", " ").strip()
    if len(output) > MAX_OUTPUT_LENGTH:
        output = output[: MAX_OUTPUT_LENGTH] + "..."
    return output


def rate_limit(f):
    """
    Decorator to enforce a rate limit on the endpoint.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr or "unknown"
        if client_ip not in RATE_LIMIT_STORE:
            RATE_LIMIT_STORE[client_ip] = []
        RATE_LIMIT_STORE[client_ip].append(time.time())
        # Remove entries older than the window
        RATE_LIMIT_STORE[client_ip] = [t for t in RATE_LIMIT_STORE[client_ip] if t > time.time() - RATE_LIMIT_WINDOW]
        if len(RATE_LIMIT_STORE[client_ip]) > RATE_LIMIT_MAX:
            return jsonify({"error": "Rate limit exceeded"}), 429
        return f(*args, **kwargs)
    return decorated_function


@app.route("/ping", methods=["GET"])
@rate_limit
def ping_host():
    host = request.args.get("host", "").strip()
    if not host:
        return jsonify({"error": "Missing 'host' query parameter"}), 400
    # Basic hostname validation: alphanumeric, hyphens, dots, underscores
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$", host):
        return jsonify({"error": "Invalid hostname format"}), 400
    try:
        result = subprocess.run(
            PING_CMD,
            input=host,
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        output = result.stdout + result.stderr
        return jsonify({
            "host": host,
            "status": "success" if result.returncode == 0 else "failure",
            "output": sanitize_output(output)
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Ping timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
