from flask import Flask, request, jsonify
import subprocess
import os
import base64

app = Flask(__name__)

# Secure the endpoint by using a secret key to hash the request
secret_key = os.urandom(16)

@app.route('/ping', methods=['POST'])
def ping_host():
    # Check for secret key in headers
    auth_header = request.headers.get('Authorization')
    if auth_header is None or auth_header != f'Bearer {base64.b64encode(secret_key).decode()}':
        return jsonify({"error": "Unauthorized"}), 401

    # Extract host from request body
    host = request.json.get('host')
    if host is None or not isinstance(host, str) or len(host.strip()) == 0:
        return jsonify({"error": "Invalid host"}), 400

    # Prepare the ping command
    command = ['ping', '-c', '4', host]  # Using ping to test connectivity

    # Execute the command
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output = result.stdout
    except subprocess.CalledProcessError as e:
        output = f"Error: {e.stderr}"

    # Return the output
    return jsonify({"output": output})

if __name__ == '__main__':
    # Ensure the secret key is stored securely
    with open('secret_key.txt', 'wb') as key_file:
        key_file.write(secret_key)
    
    app.run(debug=True)
