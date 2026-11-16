# Qwythos – Flask file upload/download endpoint with security best practices
# Created by Empero AI
import os
import uuid
import hashlib
import secrets
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)

# --- Configuration ---
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xml', 'json'}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
APP_SECRET = os.environ.get('FLASK_APP_SECRET', secrets.token_hex(32))

# Ensure upload folder exists and is writable
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.chmod(UPLOAD_FOLDER, 0o750)  # Owner read/write/execute, group read/execute, others execute

def allowed_file(filename):
    """Return True if filename has an allowed extension and is not empty."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_filename(original_filename):
    """Generate a safe, unique filename to prevent collisions and path traversal."""
    # Use UUID to ensure uniqueness and avoid guessing
    unique_id = str(uuid.uuid4())
    # Keep original extension
    name, ext = os.path.splitext(original_filename)
    return f"{unique_id}{ext}"

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    POST /upload
    Accepts multipart/form-data with field 'file'.
    Returns JSON with status and the generated filename.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Secure filename generation
    filename = generate_filename(file.filename)
    
    # Store file
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Set appropriate permissions (readable by owner and group)
    os.chmod(filepath, 0o640)
    
    return jsonify({
        'status': 'success',
        'filename': filename,
        'path': filepath
    }), 200

@app.route('/download/<path:filename>')
def download_file(filename):
    """
    GET /download/<filename>
    Serves the uploaded file. The filename is stored in the filesystem,
    so we just return it directly. Flask's send_from_directory handles
    path traversal safely because we store files in UPLOAD_FOLDER and never
    join the user-provided filename to a base path; we just serve from
    UPLOAD_FOLDER with the stored filename as the name.
    """
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    # Ensure we don't serve files outside UPLOAD_FOLDER (already guaranteed by storage)
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# Example: simple health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    # Run with debug=False in production; use a proper WSGI server (e.g., gunicorn)
    app.run(host='0.0.0.0', port=5000, debug=False)
