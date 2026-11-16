from flask import Flask, request, jsonify
import socket
import subprocess
import threading
import queue

app = Flask(__name__)

# Thread-safe queue to hold ping results
ping_queue = queue.Queue()

@app.route('/ping', methods=['POST'])
def ping_host():
    """
    Endpoint to ping a host name or IP address.
    Accepts JSON body: {"host": "example.com"}
    Returns JSON with result details.
    """
    data = request.get_json()
    if not data or 'host' not in data:
        return jsonify({'error': 'Missing required field "host"'}), 400

    host = data['host']
    if not host or not isinstance(host, str):
        return jsonify({'error': 'Invalid host value'}), 400

    # Perform ping in a background thread to avoid blocking the request
    def ping_worker():
        try:
            # Use socket-level ping with a short timeout (1 second per attempt)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            sock.sendto(b'', (host, 0))
            sock.close()
            
            # Capture output from the system ping command
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', host],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse response
            output = result.stdout if result.returncode == 0 else result.stderr
            ping_queue.put({
                'host': host,
                'success': result.returncode == 0,
                'output': output,
                'status_code': result.returncode
            })
        except Exception as e:
            ping_queue.put({
                'host': host,
                'success': False,
                'output': str(e),
                'status_code': -1
            })
    
    thread = threading.Thread(target=ping_worker)
    thread.start()

    # Wait for result with a reasonable timeout (10 seconds)
    try:
        result = ping_queue.get(timeout=10)
    except queue.Empty:
        result = {
            'host': host,
            'success': False,
            'output': 'Ping timed out',
            'status_code': -2
        }

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
