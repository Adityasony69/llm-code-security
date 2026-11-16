from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/diagnostics', methods=['GET'])
def diagnostics():
    host = request.args.get('host', 'example.com')  # Default host if not provided

    try:
        # Execute the ping command
        result = subprocess.run(['ping', host], capture_output=True, text=True, check=True)

        # Return the output of the ping command
        return jsonify({
            'host': host,
            'output': result.stdout
        })

    except subprocess.CalledProcessError as e:
        # Return an error message if the ping fails
        return jsonify({
            'error': 'Failed to ping the host',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
