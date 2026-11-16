"""
Secure Flask file upload and download endpoints.
- Enforces file type restrictions.
- Validates file size.
- Generates safe storage paths to prevent directory traversal.
- Uses Content-Disposition header for downloads.
"""

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'json', 'xml'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_safe_filename(filename):
    """Extract a safe filename from the request, handling directory traversal."""
    base_name = os.path.basename(filename)
    if not base_name:
        logger.warning("No filename provided in request")
        return None
    safe_name = secure_filename(base_name)
    if not safe_name:
        logger.warning(f"Filename is empty after sanitization: {filename}")
        return None
    return safe_name


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads with size and type validation."""
    if 'file' not in request.files:
        logger.warning("No file part in request")
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning("Empty file name")
        return jsonify({'error': 'Empty file name'}), 400

    if not allowed_file(file.filename):
        logger.warning(f"File type not allowed: {file.filename}")
        return jsonify({'error': f'File type not allowed. Allowed: {ALLOWED_EXTENSIONS}'}), 400

    # Read content for size check
    content = file.read()
    if len(content) > MAX_FILE_SIZE:
        logger.warning(f"File too large: {len(content)} bytes")
        return jsonify({'error': 'File too large'}), 413

    # Get safe filename and write to disk
    safe_name = get_safe_filename(file.filename)
    if safe_name is None:
        return jsonify({'error': 'Could not determine safe filename'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, safe_name)
    with open(file_path, 'wb') as f:
        f.write(content)

    logger.info(f"Saved file: {file_path}")
    return jsonify({
        'message': 'File uploaded successfully',
        'name': safe_name,
        'size': len(content)
    }), 201


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Serve a file from the upload folder securely."""
    safe_name = get_safe_filename(filename)
    if safe_name is None:
        return jsonify({'error': 'Invalid filename'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, safe_name)
    if not os.path.isfile(file_path):
        logger.warning(f"File not found: {file_path}")
        return jsonify({'error': 'File not found'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=safe_name
    )


if __name__ == '__main__':
    app.run(debug=True, port=5000)
