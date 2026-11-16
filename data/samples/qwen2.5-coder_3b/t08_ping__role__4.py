from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/ping', methods=['POST'])
def ping_host():
    try:
        # Get the host name from the request
        host = request.json.get('host', '')

        # Use subprocess to ping the host
        result = subprocess.run(['ping', host], capture_output=True, text=True)

        # Parse the output
        lines = result.stdout.splitlines()
        response = {
            'host': host,
            'status': 'success',
            'results': []
        }

        for line in lines:
            # Extract relevant information from the ping output
            parts = line.split()
            if parts and parts[0] == 'Reply':
                response['results'].append({
                    'ip': parts[4],
                    'time': parts[2]
                })

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
