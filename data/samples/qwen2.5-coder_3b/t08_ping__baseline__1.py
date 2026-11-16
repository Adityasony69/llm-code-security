from flask import Flask, request, jsonify
import subprocess
app = Flask(__name__)
@app.route('/ping', methods=['POST'])
def ping_host():
    host_name = request.json['host_name']
    result = subprocess.run(['ping', host_name], capture_output=True, text=True)
    return jsonify({'output': result.stdout})
if __name__ == '__main__':
    app.run(debug=True)
