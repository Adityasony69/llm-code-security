import os
import hashlib
import secrets
from flask import Flask, request, send_file, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Security-focused endpoints ---

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    filename = secure_filename(file.filename)
    # Generate unique filename to prevent overwrites and ensure uniqueness
    unique_filename = f"{filename}_{secrets.token_hex(4)}.tmp"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Save file
    file.save(filepath)
    
    # Compute SHA-256 hash for integrity verification
    file_hash = hashlib.sha256(file.read()).hexdigest()
    # Remove hash from file (already read into memory)
    filepath.seek(0)
    file.seek(0)
    
    return jsonify({
        'filename': filename,
        'saved_path': filepath,
        'hash': file_hash
    }), 201

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename: str):
    # Basic security: only allow alphanumeric filenames to prevent path traversal
    if not filename.replace('.', '').replace('_', '').isalnum():
        return jsonify({'error': 'Invalid filename'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/info/<path:filename>', methods=['GET'])
def file_info(filename: str):
    # Basic security: only allow alphanumeric filenames to prevent path traversal
    if not filename.replace('.', '').replace('_', '').isalnum():
        return jsonify({'error': 'Invalid filename'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    file_hash = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
    return jsonify({
        'filename': filename,
        'hash': file_hash,
        'size': os.path.getsize(filepath),
        'mimetype': os.path.splitext(filename)[1].lower()
    })

# --- Utility functions with security in mind ---

def get_upload_folder() -> str:
    return app.config['UPLOAD_FOLDER']

def get_max_upload_size() -> int:
    return app.config['MAX_CONTENT_LENGTH']

def is_file_allowed(filename: str) -> bool:
    return allowed_file(filename)

def is_filename_safe(filename: str) -> bool:
    # Only allow alphanumeric characters, dots, and underscores
    return filename.replace('.', '').replace('_', '').isalnum()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
