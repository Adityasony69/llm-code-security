from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/ping', methods=['POST'])
def ping_host():
    try:
        host = request.json.get('host')
        if not host:
            return jsonify({'error': 'Host name is required'}), 400

        # Ping the host
        result = subprocess.run(['ping', host], capture_output=True, text=True, timeout=5)

        # Check if the ping was successful
        if result.returncode == 0:
            output = result.stdout
        else:
            output = result.stderr

        return jsonify({'output': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
