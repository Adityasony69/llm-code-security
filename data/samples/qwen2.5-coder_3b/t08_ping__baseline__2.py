from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/ping', methods=['POST'])
def ping_host():
    host = request.json.get('host')
    if not host:
        return jsonify({'error': 'Host name is required'}), 400

    try:
        # Use subprocess to run the ping command
        response = subprocess.run(['ping', '-c', '4', host], capture_output=True, text=True, check=True)
        output = response.stdout
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Ping failed: {e.stderr}'}), 500

    return jsonify({'output': output})

if __name__ == '__main__':
    app.run(debug=True)
