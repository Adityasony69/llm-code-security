from flask import Flask, request, send_from_directory, abort, jsonify
import os
import uuid

app = Flask(__name__)

# Define a directory to store uploaded files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Secure function to generate a safe filename
def safe_filename(filename):
    # Remove characters that are not allowed in filenames
    return ''.join(c for c in filename if c.isalnum() or c.isspace())

# Endpoint to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        abort(400, "No file part")

    file = request.files['file']
    if file.filename == '':
        abort(400, "No selected file")

    # Generate a unique filename
    filename = safe_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Save the file to disk
    file.save(filepath)

    return jsonify({"message": f"File {filename} uploaded successfully"}), 201

# Endpoint to download files by name
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Check if the file exists
    if not os.path.isfile(filepath):
        abort(404, "File not found")

    # Send the file to the client
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
