from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/ping', methods=['POST'])
def ping_host():
    data = request.get_json()
    host = data.get('host', 'localhost')  # Default to localhost if not provided

    try:
        # Use subprocess to run the ping command
        result = subprocess.run(['ping', host], capture_output=True, text=True, check=True)
        output = result.stdout
        return jsonify({'status': 'success', 'output': output})

    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
