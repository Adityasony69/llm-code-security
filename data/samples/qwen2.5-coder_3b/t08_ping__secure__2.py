from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

# Security headers to prevent common vulnerabilities
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; frame-src 'self'"
    return response

def ping_host(hostname):
    try:
        # Use subprocess to run the ping command
        result = subprocess.run(['ping', hostname], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

@app.route('/diagnostics', methods=['POST'])
def diagnostics():
    # Get the hostname from the request
    hostname = request.json.get('hostname')
    
    if not hostname:
        return jsonify({"error": "Hostname is required"}), 400
    
    # Ping the host
    ping_output = ping_host(hostname)
    
    # Return the ping output
    return jsonify({"ping_output": ping_output})

if __name__ == '__main__':
    app.run(debug=True)
