import socket
import subprocess
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# Define the ping command to execute
# Using 'ping -c 1' on Linux/macOS for a single packet; '-n' on Windows
PING_CMD_TEMPLATE = "ping -c 1 {}"

@app.route('/diagnostics/ping', methods=['GET', 'POST'])
def ping_host():
    """
    Endpoint to ping a given hostname or IP address.
    
    Accepts the target in the query parameter 'host' (GET) or JSON body 'host' (POST).
    Returns a JSON response with the raw command output and a status message.
    """
    # Determine the target host from the request
    host = None
    
    if request.method == 'GET':
        host = request.args.get('host')
    else:
        # Try to parse JSON body
        try:
            data = request.get_json()
            host = data.get('host')
        except Exception:
            pass

    if not host:
        return jsonify({
            "error": "Missing 'host' parameter. Provide it via query string (?host=example.com) or JSON body {\"host\": \"example.com\"}."
        }), 400

    if not isinstance(host, str) or not host.strip():
        return jsonify({
            "error": "'host' must be a non-empty string."
        }), 400

    # Validate that it looks like a hostname or IP
    if not socket.gethostbyname(host):
        return jsonify({
            "error": f"Invalid hostname or IP address: {host}"
        }), 400

    try:
        # Run the ping command, capturing standard output and error
        cmd = PING_CMD_TEMPLATE.format(host)
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        
        output = result.stdout
        error = result.stderr
        returncode = result.returncode

        # Construct a human-readable status
        if returncode == 0:
            status_msg = "Host responded successfully."
        else:
            status_msg = f"Ping failed with exit code {returncode}."

        return jsonify({
            "host": host,
            "status": status_msg,
            "return_code": returncode,
            "stdout": output,
            "stderr": error,
            "raw_output": output + error
        }), 200

    except subprocess.TimeoutExpired:
        return jsonify({
            "host": host,
            "error": "Ping timed out (host unreachable or no response within 5 seconds)."
        }), 504

    except Exception as e:
        return jsonify({
            "host": host,
            "error": f"Internal server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
