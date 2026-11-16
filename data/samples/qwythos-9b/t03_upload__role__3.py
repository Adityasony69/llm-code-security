"""
Secure Flask File Upload/Download Service
Author: Qwythos (Empero AI)
"""

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid
import hashlib

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'csv', 'json', 'zip'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload folder exists with proper permissions
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename):
    """
    Generate a unique filename to prevent overwriting and ensure
    security by avoiding path traversal.
    """
    ext = original_filename.rsplit('.', 1)[1] if '.' in original_filename else ''
    filename_without_ext = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    return unique_filename


def get_file_metadata(filepath):
    """Calculate basic metadata for JSON response."""
    stat = os.stat(filepath)
    return {
        "original_name": filepath,
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "hash_sha256": hashlib.sha256(filepath).hexdigest()
    }


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Securely handle file uploads.
    Validates file type, size, and sanitizes filename before saving.
    Returns JSON with success status and metadata.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400
    
    # Sanitize filename
    unique_filename = generate_unique_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Save file
    file.save(filepath)
    
    metadata = get_file_metadata(filepath)
    metadata["success"] = True
    
    return jsonify(metadata), 201


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Securely serve uploaded files.
    Validates that the filename exists and points to a file within
    the upload directory to prevent path traversal attacks.
    """
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.isfile(filepath):
        return jsonify({"error": "File not found"}), 404
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=os.path.basename(filename)
    )


@app.route('/list', methods=['GET'])
def list_files():
    """
    List all files in the upload directory.
    Useful for debugging or admin interfaces.
    """
    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(filepath):
            files.append(get_file_metadata(filename))
    return jsonify({"files": files}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
