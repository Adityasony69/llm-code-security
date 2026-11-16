from flask import Flask, request, send_file, abort, jsonify
import os

app = Flask(__name__)

# Define the directory where uploaded files will be stored
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Define the maximum file size in bytes
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

# Set the maximum file size
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save the file to disk
    filename = file.filename
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    return jsonify({'message': 'File uploaded successfully', 'filename': filename}), 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    # Check if the file exists
    if not os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
        return jsonify({'error': 'File not found'}), 404
    
    # Send the file for download
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
