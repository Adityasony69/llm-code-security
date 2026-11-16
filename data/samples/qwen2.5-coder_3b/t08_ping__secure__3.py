from flask import Flask, request, jsonify
import subprocess
import os
import json
import re

app = Flask(__name__)

def ping_host(host):
    try:
        # Use subprocess to run the ping command
        result = subprocess.run(['ping', '-c', '4', host], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        # If ping fails, return an error message
        return f"Ping failed: {e.stderr}"

@app.route('/diagnostics', methods=['POST'])
def diagnostics():
    # Parse the JSON request
    data = request.get_json()
    host = data.get('host')

    # Validate the host input
    if not host or not re.match(r'^[a-zA-Z0-9.-]+$', host):
        return jsonify({'error': 'Invalid host name'}), 400

    # Ping the host
    output = ping_host(host)

    # Return the ping output as JSON
    return jsonify({'output': output})

if __name__ == '__main__':
    # Set environment variables for secure configuration
    app.secret_key = os.urandom(24)  # Use a secure secret key

    # Run the Flask application
    app.run(host='0.0.0.0', port=5000)
