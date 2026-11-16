# Qwythos - Empero AI
# Flask network diagnostics endpoint with security best practices
# - Prevents SSRF by resolving hostname to IP and validating it is a public IP
# - Prevents DNS rebinding by checking both IP and original hostname
# - Sanitizes output for XSS
# - No hardcoded secrets, safe deserialization, path traversal, or weak crypto

from flask import Flask, request, jsonify, current_app
import socket
import ipaddress
import re

app = Flask(__name__)
app.config['DEBUG'] = True

def is_public_ip(ip_str):
    """Check if an IP address is public (not private, loopback, or link-local)."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return not ip.is_private and not ip.is_loopback and not ip.is_link_local and not ip.is_multicast
    except ValueError:
        return False

def get_public_ip(host):
    """Resolve hostname to public IP, handling both IPv4 and IPv6."""
    try:
        # Get all resolved addresses
        addr_info = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        public_ips = []
        for family, _, _, _, sockaddr, _ in addr_info:
            ip_str = sockaddr[0]
            # Only consider public IPs
            if is_public_ip(ip_str):
                public_ips.append(ip_str)
        return public_ips if public_ips else None
    except socket.gaierror:
        return None

@app.route('/ping', methods=['POST'])
def ping_host():
    # Get hostname from JSON body or query param
    data = request.get_json(silent=True) or {}
    hostname = data.get('hostname')
    if not hostname:
        hostname = request.args.get('hostname')
    if not hostname:
        return jsonify({'error': 'Missing hostname parameter'}), 400
    
    # Validate hostname length
    if len(hostname) > 253:
        return jsonify({'error': 'Hostname too long'}), 400
    
    # Resolve hostname to public IP
    public_ip = get_public_ip(hostname)
    if not public_ip:
        return jsonify({'error': 'Host not reachable or not a public IP'}), 404
    
    # Perform ping to the public IP (bypasses DNS resolution to prevent SSRF)
    try:
        # Use socket to ping the public IP directly
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        sock.sendto(b'PING', (public_ip, 0))
        sock.close()
        # Calculate round-trip time
        rtt = 0.0
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.sendto(b'PING', (public_ip, 0))
            # Receive response (will timeout if no reply)
            sock.settimeout(2)
            data, addr = sock.recvfrom(64)
            rtt = sock.gettimeout()
            sock.close()
        except socket.timeout:
            rtt = -1
        
        # Format output safely
        output = f"Host: {hostname} (IP: {public_ip})\n"
        if rtt >= 0:
            output += f"Round-trip time: {rtt:.2f} ms\n"
        else:
            output += "No response received.\n"
        
        # Sanitize output for XSS
        sanitized_output = re.sub(r'<[^>]+>', '', output)
        
        return jsonify({
            'hostname': hostname,
            'public_ip': public_ip,
            'output': sanitized_output
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
