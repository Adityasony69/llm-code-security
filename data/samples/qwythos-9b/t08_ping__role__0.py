import socket
import threading
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor, TimeoutError

app = Flask(__name__)

# Configuration
MAX_CONCURRENT_PINGS = 10
PING_TIMEOUT_SECONDS = 5

def ping_host(host: str, timeout: int) -> dict:
    """
    Perform a TCP ping (connection test) to a host with the given timeout.
    Returns a dictionary with the result details.
    """
    result = {
        "host": host,
        "status": "unknown",
        "message": "",
        "ip_address": None
    }
    
    try:
        # Resolve hostname to IP
        ip = socket.gethostbyname(host)
        result["ip_address"] = ip
        
        # Attempt connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, 80))  # Ping port 80 (HTTP)
        sock.close()
        
        result["status"] = "up"
        result["message"] = f"Host {host} is reachable."
        
    except socket.timeout:
        result["status"] = "timeout"
        result["message"] = f"Connection to {host} timed out."
    except socket.gaierror as e:
        result["status"] = "error"
        result["message"] = f"DNS resolution failed for {host}: {str(e)}"
    except socket.herror as e:
        result["status"] = "error"
        result["message"] = f"DNS lookup error for {host}: {str(e)}"
    except ConnectionRefusedError:
        result["status"] = "down"
        result["message"] = f"Connection refused by {host}."
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Unexpected error pinging {host}: {str(e)}"
    
    return result

@app.route('/api/diagnostics/ping', methods=['GET', 'POST'])
def ping_endpoint():
    """
    Network diagnostics endpoint.
    
    Accepts either:
      - GET with query parameter ?host=example.com
      - POST with JSON body {"host": "example.com"}
      
    Returns a JSON object with a "results" array containing the ping status for each host.
    """
    # Parse host from request
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if not data or 'host' not in data:
            return jsonify({"error": "Missing 'host' in request body"}), 400
        host = data['host']
    else:  # GET
        host = request.args.get('host')
        if not host:
            return jsonify({"error": "Missing 'host' query parameter"}), 400
    
    # Basic validation (prevent empty or overly long hosts)
    if not isinstance(host, str) or not host.strip():
        return jsonify({"error": "Host must be a non-empty string"}), 400
    
    # Normalize host
    host = host.strip()
    
    # Execute ping in a thread to avoid blocking the Flask request
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(ping_host, host, PING_TIMEOUT_SECONDS)
        try:
            result = future.result(timeout=PING_TIMEOUT_SECONDS + 2)
            return jsonify({"results": [result]})
        except TimeoutError:
            return jsonify({"error": "Ping request timed out"}), 504
        except Exception as e:
            return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
