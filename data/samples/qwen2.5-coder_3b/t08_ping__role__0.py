from flask import Flask, request, jsonify
import subprocess
import re

app = Flask(__name__)

def ping_host(hostname):
    try:
        # Run the ping command using subprocess
        result = subprocess.run(['ping', hostname], capture_output=True, text=True, check=True)
        # Extract the output and parse the ping statistics
        lines = result.stdout.split('\n')
        if lines:
            for line in lines:
                if re.match(r'PING\s+(.+?)\s+with\s+\d+\s+data bytes', line):
                    host = line.split()[1]
                elif re.match(r'Time\s+to\s+live=\s+(\d+)', line):
                    ttl = line.split()[3]
                elif re.match(r'Received\s+\d+\s+packets;\s+\d+\s+sent,\s+\d+\s+received,\s+\d+\s+lost', line):
                    received = line.split()[2]
                    sent = line.split()[1]
                    lost = line.split()[4]
                    return {
                        'host': host,
                        'ttl': ttl,
                        'received': received,
                        'sent': sent,
                        'lost': lost
                    }
    except subprocess.CalledProcessError as e:
        return str(e)
    except Exception as e:
        return str(e)

@app.route('/ping', methods=['POST'])
def ping():
    data = request.json
    if not data or 'hostname' not in data:
        return jsonify({'error': 'Hostname is required'}), 400
    
    hostname = data['hostname']
    response = ping_host(hostname)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
