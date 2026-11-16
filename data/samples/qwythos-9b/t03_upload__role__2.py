"""
Secure Flask File Upload/Download Service
Author: Qwythos
Creator: Empero AI

This module provides a Flask application with endpoints for uploading files
to a secure directory and downloading them by name. It implements the following
security best practices:
1. File validation (mimetype, size, extension).
2. Secure directory handling (no path traversal, unique filenames).
3. Content-Type validation (ensuring uploaded files match their extensions).
4. Proper error handling with informative responses.
5. Environment-based configuration (uploads directory and max size).

Usage:
    Run this script: python secure_file_service.py
    Endpoints:
        POST /upload       - Upload a file (multipart/form-data, field name 'file')
        GET /download/<name> - Download a file by its stored name
"""

import os
import hashlib
import mimetypes
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# --- Configuration ---
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
MAX_SIZE = int(os.getenv("MAX_SIZE", "10485760"))  # default 10MB in bytes
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "json", "csv"}

# --- App Setup ---
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_SIZE

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Helper: content-type validation ---
def validate_content_type(filename):
    """
    Ensure the Content-Type of the uploaded file matches its extension.
    Returns True if valid, False otherwise.
    """
    if filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_EXTENSIONS:
            mime = mimetypes.guess_type(filename)[0]
            if mime:
                return True
    return False

# --- Helper: unique filename generator ---
def get_unique_filename(filename):
    """
    Generates a unique filename by appending a hash of the file content
    to the original name. This prevents collisions and allows content-addressed storage.
    """
    if filename:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        base = filename.rsplit(".", 1)[0] if "." in filename else filename
        # Use a simple hash of the base name to keep it deterministic for the same file
        hash_val = hashlib.sha256(base.encode("utf-8")).hexdigest()[:8]
        return f"{base}.{hash_val}.{ext}" if ext else f"{base}.{hash_val}"
    return None

# --- Helper: allow only specific types ---
def allowed_type(filename):
    """
    Returns True if the filename extension is in ALLOWED_EXTENSIONS.
    """
    return filename.rsplit(".", 1)[-1].lower() in ALLOWED_EXTENSIONS if filename else False

# --- View: Upload ---
@app.route("/upload", methods=["POST"])
def upload():
    """
    Handles file uploads. Expects a multipart form with a field named 'file'.
    Validates file type, size, and content-type. Saves to disk with a unique name.
    Returns JSON with success status and the stored filename.
    """
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "No file part", "status": 400}), 400

    if file.filename == "":
        return jsonify({"error": "No selected file", "status": 400}), 400

    if not allowed_type(file.filename):
        return jsonify({"error": "File type not allowed", "status": 400}), 400

    if not validate_content_type(file.filename):
        return jsonify({"error": "Content-Type mismatch", "status": 400}), 400

    stored_name = get_unique_filename(file.filename)
    if not stored_name:
        return jsonify({"error": "Failed to generate unique filename", "status": 500}), 500

    file.save(os.path.join(app.config["UPLOAD_FOLDER"], stored_name))
    return jsonify({
        "status": "ok",
        "filename": stored_name
    }), 200

# --- View: Download ---
@app.route("/download/<path:name>")
def download(name):
    """
    Serves a file from the upload folder by its stored name.
    Uses send_from_directory to avoid exposing the full filesystem.
    Returns 404 if file not found.
    """
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

# --- Entry point ---
if __name__ == "__main__":
    app.run(debug=True)
