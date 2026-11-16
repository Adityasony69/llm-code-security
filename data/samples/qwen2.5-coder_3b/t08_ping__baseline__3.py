from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/ping', methods=['POST'])
def ping_host():
    try:
        # Get the host name from the request data
        host = request.json.get('host')
        
        # Check if the host is provided
        if not host:
            return jsonify({'error': 'Host name is required'}), 400
        
        # Ping the host using the subprocess module
        response = subprocess.run(['ping', '-c', '4', host], capture_output=True, text=True)
        
        # Return the response
        return jsonify({'host': host, 'output': response.stdout})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
