from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

# Define the allowed hosts to prevent SSRF
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

@app.route('/ping', methods=['POST'])
def ping_host():
    try:
        # Get the hostname from the request
        hostname = request.json.get('hostname')
        
        # Validate the hostname
        if not hostname:
            return jsonify({'error': 'Hostname is required'}), 400
        
        # Check if the hostname is allowed
        if hostname not in ALLOWED_HOSTS:
            return jsonify({'error': 'Hostname not allowed'}), 403
        
        # Perform the ping
        result = subprocess.run(['ping', '-c', '4', hostname], capture_output=True, text=True)
        
        # Return the result
        return jsonify({
            'status': 'success',
            'output': result.stdout
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
