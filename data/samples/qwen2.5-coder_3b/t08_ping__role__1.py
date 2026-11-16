from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/ping', methods=['POST'])
def ping_host():
    try:
        # Extract the host name from the request data
        host = request.json.get('host', None)
        
        if not host:
            return jsonify({'error': 'No host provided'}), 400
        
        # Use subprocess to execute the ping command
        result = subprocess.run(['ping', '-c', '4', host], capture_output=True, text=True)
        
        # Check if the ping was successful
        if result.returncode == 0:
            return jsonify({'status': 'success', 'output': result.stdout})
        else:
            return jsonify({'status': 'failure', 'output': result.stderr}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
