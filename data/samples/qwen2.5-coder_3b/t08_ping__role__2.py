from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/diagnostics', methods=['POST'])
def diagnostics():
    try:
        # Get the hostname from the request
        host = request.json.get('host')
        
        # Check if the host is provided
        if not host:
            return jsonify({"error": "Host name is required"}), 400
        
        # Execute the ping command
        import subprocess
        result = subprocess.run(['ping', '-c', '4', host], capture_output=True, text=True, check=True)
        
        # Return the output of the ping command
        return jsonify({"output": result.stdout})
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
