import socket
import json
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# Security: Do not use pickle or eval with untrusted data.
# Security: Use a fixed, well-known base URL for the local network only (SSRF protection).
# Security: Ensure only localhost/internal IPs are allowed to be pinged.
ALLOWED_BASE_URLS = ["http://127.0.0.1", "http://localhost"]
ALLOWED_SCHEMES = {"http"}

def is_safe_url(url: str) -> bool:
    """
    Validate that the URL is safe to resolve (SSRF protection).
    - Must start with an allowed scheme (http only).
    - Must resolve to an internal IP (loopback, link-local, private, or IPv6 local).
    """
    try:
        # Parse the URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_SCHEMES:
            return False
        host = parsed.hostname or parsed.netloc
        if not host:
            return False

        # Resolve to IP
        try:
            resolved = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror:
            return False

        for _, _, _, _, sockaddr, _ in resolved:
            ip = sockaddr[0]
            # Check for internal IPs
            if ip.startswith(("127.", "::1", "0:",)):
                return True
            if ip.startswith(("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.", "169.254.")):
                return True
        return False
    except Exception:
        return False

def safe_ping(host: str) -> tuple[bool, str]:
    """
    Ping a host safely.
    Returns (success, message).
    """
    try:
        socket.setdefaulttimeout(3)
        result = socket.gethostbyname(host)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((result, 0))
        sock.close()
        return True, f"Ping successful: {result}"
    except socket.gaierror as e:
        return False, f"DNS resolution failed: {e.strerror}"
    except socket.timeout:
        return False, "Ping timed out"
    except socket.error as e:
        return False, f"Socket error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

@app.route("/diagnostics/ping", methods=["GET"])
def ping_endpoint():
    # Extract host from query parameter; avoid path traversal by using only the parameter
    host = request.args.get("host", "").strip()
    if not host:
        return jsonify({"error": "Missing required parameter 'host'"}), 400

    # Security: Validate URL scheme (prevent SSRF)
    if not is_safe_url(f"http://{host}"):
        return jsonify({"error": "Host resolved to an external IP; access denied"}), 403

    # Perform the ping
    success, message = safe_ping(host)
    if success:
        return jsonify({"status": "ok", "message": message}), 200
    else:
        return jsonify({"status": "error", "message": message}), 502

@app.route("/diagnostics/health", methods=["GET"])
def health_check():
    """Simple health endpoint to verify the service is running."""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    # Serve only on localhost to avoid exposing the endpoint externally unless desired
    app.run(host="127.0.0.1", port=5000, debug=False)
