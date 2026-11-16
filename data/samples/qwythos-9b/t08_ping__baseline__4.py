# network_diagnostics.py
# A Flask application that provides an endpoint to ping a given hostname and return the output.

import sys
import socket
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Define the commands to run based on the operating system
# We use 'ping -c 1 <host>' on Unix-like systems and 'ping -n 1 <host>' on Windows.
ping_cmd = {
    "linux": ["ping", "-c", "1", "{host}"],
    "darwin": ["ping", "-c", "1", "{host}"],  # macOS
    "windows": ["ping", "-n", "1", "{host}"]
}

# Function to detect the OS and select the appropriate command
def get_ping_command(host: str) -> list:
    system = sys.platform
    cmd = ping_cmd.get(system)
    if cmd is None:
        # Fallback for unknown systems (e.g., WSL on Linux reporting 'win32')
        # Try Windows ping syntax first, then fall back to Linux if that fails.
        return ping_cmd["windows"]
    return cmd

# Function to execute the ping command and return the output
def ping_host(host: str) -> str:
    cmd = get_ping_command(host)
    try:
        # Run the command without capturing stdout/stderr initially to see raw output
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            # If the command fails (e.g., host unreachable), return the error message
            return f"Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Ping timed out"
    except Exception as e:
        return f"Error: {str(e)}"

# Flask endpoint for network diagnostics
@app.route("/ping", methods=["GET", "POST"])
def ping_endpoint():
    # Accept either a JSON body with a "host" key or a query parameter "host"
    # Priority is given to JSON body, then query parameter.
    host = request.json.get("host") if request.is_json else request.args.get("host")
    
    if not host:
        return jsonify({
            "status": "error",
            "message": "Missing required parameter 'host'"
        }), 400

    # Validate that the host is a string and not empty
    if not isinstance(host, str) or not host.strip():
        return jsonify({
            "status": "error",
            "message": "Invalid 'host' value. Must be a non-empty string."
        }), 400

    # Perform the ping
    output = ping_host(host)

    # Construct the response
    response_data = {
        "status": "success",
        "host": host,
        "output": output
    }

    return jsonify(response_data), 200

if __name__ == "__main__":
    # Run the Flask app. Adjust debug=True as needed for your environment.
    app.run(debug=True)
