from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

# Disable CORS for demonstration purposes
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

def ping_host(host_name):
    try:
        # Use subprocess to ping the host
        result = subprocess.run(['ping', '-c', '4', host_name], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@app.route('/ping', methods=['POST'])
def ping():
    data = request.get_json()
    if not data or 'host_name' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    host_name = data['host_name']
    response = ping_host(host_name)
    return jsonify({'output': response})

if __name__ == '__main__':
    app.run(debug=True)
