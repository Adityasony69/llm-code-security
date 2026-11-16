# flask_secure_upload.py
# A minimal, secure Flask app demonstrating file upload and download with basic validation.
# Run with: flask run --host=0.0.0.0 --port=5000
# (You can also use: python flask_secure_upload.py)

from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Return True if filename has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Accept a multipart/form-data POST request with a 'file' field.
    Validates file type and size, then saves to disk.
    Returns JSON with the original filename, secure name, and size.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed: {list(ALLOWED_EXTENSIONS)}'}), 400

    # Check file size
    stream = file.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0, os.SEEK_SET)
    if size > MAX_FILE_SIZE:
        return jsonify({'error': f'File size exceeds maximum of {MAX_FILE_SIZE / (1024*1024):.1f} MB'}), 413

    # Secure filename: original name with extension, plus a unique suffix
    # to avoid collisions and prevent directory traversal issues.
    original_filename = file.filename
    _, ext = os.path.splitext(original_filename)
    secure_filename = f"{uuid.uuid4().hex}{ext}"

    # Save the file
    file_path = os.path.join(UPLOAD_FOLDER, secure_filename)
    file.save(file_path)

    return jsonify({
        'message': 'File uploaded successfully',
        'original_name': original_filename,
        'secure_name': secure_filename,
        'size_bytes': size
    }), 200

@app.route('/download/<path:filename>')
def download_file(filename):
    """
    Serve a file from the uploads folder if it exists.
    The filename is expected to be the exact stored name (including extension).
    Returns 404 if the file is not found.
    """
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.isfile(file_path):
        abort(404, description='File not found')
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
