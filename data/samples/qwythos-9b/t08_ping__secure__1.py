from flask import Flask, request, jsonify
import socket
import re
from functools import wraps

app = Flask(__name__)

# Security: Whitelist allowed domains to prevent SSRF
ALLOWED_DOMAINS = {
    "example.com",
    "localhost",
    "127.0.0.1",
    "::1",
}

# Security: Validate hostname format (prevent injection via URL encoding or control chars)
HOSTNAME_PATTERN = re.compile(r"^[a-zA-Z0-9.-]+$")


def validate_hostname(hostname: str) -> bool:
    """
    Returns True if the hostname is safe to use for network operations.
    Checks:
      - No control characters or whitespace.
      - Matches allowed alphanumeric/dot/hyphen pattern.
      - Is in the allowed domain list (or is a literal IP address in allowed set).
    """
    if not hostname:
        return False

    # Reject control characters, whitespace, and common URL-encoding artifacts
    if any(ord(c) < 32 or c in (" ", "\t", "\n", "\r") for c in hostname):
        return False

    # Ensure it matches a safe pattern
    if not HOSTNAME_PATTERN.fullmatch(hostname):
        return False

    # Normalize and check against allowed domains
    normalized = hostname.lower()
    if normalized in ALLOWED_DOMAINS:
        return True

    # Allow literal IPv4/IPv6 addresses that are in the allowed set
    if normalized in ("127.0.0.1", "::1"):
        return True

    return False


@app.route("/ping", methods=["GET", "POST"])
def ping_endpoint():
    # Extract hostname from query parameter (GET) or JSON body (POST)
    hostname = request.args.get("host")
    if not hostname:
        hostname = request.json.get("host")

    if not hostname:
        return jsonify({"error": "Missing required parameter: host"}), 400

    if not validate_hostname(hostname):
        return jsonify({"error": "Invalid hostname: not a safe domain"}), 400

    try:
        # Resolve hostname to IP (prevents SSRF by using allowed domain list)
        resolved_ip = socket.gethostbyname(hostname)
        # Perform ping with timeout (avoid hanging)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        sock.connect((resolved_ip, 0))  # connect to any port to verify reachability
        sock.close()

        return jsonify({
            "host": hostname,
            "resolved_ip": resolved_ip,
            "reachable": True,
            "message": "Host is reachable."
        }), 200

    except socket.gaierror as e:
        return jsonify({
            "error": "Hostname resolution failed",
            "details": str(e)
        }), 404

    except socket.timeout:
        return jsonify({
            "error": "Connection timed out",
            "host": hostname
        }), 504

    except Exception as e:
        # Catch any unexpected errors, log internally (in production use proper logging)
        return jsonify({
            "error": "Internal diagnostic error",
            "host": hostname,
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
