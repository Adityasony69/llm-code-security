import socket
import threading
from flask import Flask, request, jsonify
from urllib.parse import urlparse

app = Flask(__name__)

# Rate limiting simple lock to prevent DoS
ping_lock = threading.Lock()
max_pings_per_ip = 10
ip_pings_count = {}

def is_safe_hostname(hostname: str) -> bool:
    # Prevent SSRF by resolving to a public IP
    parsed = urlparse(hostname)
    host = parsed.hostname
    if not host:
        return False
    # Allow only standard hostnames, no userinfo, no ports that might be misused
    if any(ch in host for ch in ":/?#[]@"):
        return False
    try:
        ip = socket.gethostbyname(host)
        # Block private IP ranges (RFC1918) and loopback to avoid SSRF
        if ip.startswith(("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.",
                         "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
                         "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.",
                         "127.", "169.254.")):
            return False
        return True
    except socket.gaierror:
        return False

@app.route("/ping", methods=["GET", "POST"])
def ping_endpoint():
    # Extract hostname from query param or JSON body
    hostname = request.args.get("host")
    if not hostname:
        # Try JSON body if query param missing
        data = request.get_json(silent=True)
        hostname = data.get("host")
    if not hostname:
        return jsonify({"error": "Missing required 'host' parameter"}), 400

    hostname = str(hostname).strip()
    if not hostname:
        return jsonify({"error": "Host name cannot be empty"}), 400

    # Validate hostname to avoid SSRF
    if not is_safe_hostname(hostname):
        return jsonify({"error": "Invalid or unsafe hostname"}), 400

    # Simple rate limiting
    client_ip = request.remote_addr
    with ping_lock:
        if client_ip not in ip_pings_count:
            ip_pings_count[client_ip] = 0
        if ip_pings_count[client_ip] >= max_pings_per_ip:
            return jsonify({"error": "Rate limit exceeded"}), 429
        ip_pings_count[client_ip] += 1

    try:
        # Resolve hostname to IP first (already done in validation, but we ping the resolved IP)
        ip = socket.gethostbyname(hostname)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        result = sock.connect_ex((ip, 8))
        sock.close()
        if result == 0:
            # Check for ICMP echo via socket (requires ICMP support; simple ping check)
            # For broader compatibility we just report TCP port 8 (or 21/80/443) as reachable
            # and optionally try ICMP if available.
            # Since socket module doesn't have a direct ICMP ping without extra libs,
            # we will use socket to send an ICMP echo if the OS supports it.
            try:
                icmp_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                icmp_sock.settimeout(3.0)
                icmp_sock.sendto(b"\x00" * 8, (ip, 0))
                icmp_sock.setblocking(1)
                _, addr = icmp_sock.recvfrom(1500)
                icmp_sock.close()
                response_time = addr[1] if isinstance(addr, tuple) else 0
                return jsonify({
                    "status": "up",
                    "hostname": hostname,
                    "ip": ip,
                    "response_time_ms": round(response_time * 1000, 2)
                })
            except Exception:
                # ICMP not supported or timed out; rely on TCP probe
                return jsonify({
                    "status": "up",
                    "hostname": hostname,
                    "ip": ip,
                    "note": "ICMP not available; TCP probe succeeded",
                    "tcp_port": 8
                })
        else:
            return jsonify({
                "status": "down",
                "hostname": hostname,
                "ip": ip,
                "error": "Port 8 not reachable (or ICMP not supported)"
            })
    except socket.timeout:
        return jsonify({
            "status": "timeout",
            "hostname": hostname,
            "error": "No response within timeout"
        })
    except socket.gaierror as e:
        return jsonify({
            "status": "error",
            "hostname": hostname,
            "error": f"DNS resolution failed: {e.strerror if hasattr(e, 'strerror') else str(e)}"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "hostname": hostname,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
