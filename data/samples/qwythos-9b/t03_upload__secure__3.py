import os
import uuid
import hashlib
import secrets
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Configure logging to avoid leaking stack traces to clients
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = Path(__file__).parent / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Store file metadata (name -> absolute path) in memory.
# For a production system, this would be a database.
FILE_REGISTRY = {}

def allowed_file(filename: str) -> bool:
    """Return True if the file extension is allowed and the filename is not empty."""
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in ALLOWED_EXTENSIONS

def generate_unique_path(base_folder: Path, original_filename: str) -> Path:
    """
    Generate a unique safe path for the uploaded file.
    Uses a UUID as suffix to avoid collisions and ensures no path traversal.
    """
    # Clean the original filename (remove non-alphanumeric and spaces)
    clean_name = secure_filename(original_filename)
    # Create a unique filename: clean_name + "_" + uuid4 + "." + extension
    ext = clean_name.rsplit(".", 1)[-1] if "." in clean_name else ""
    new_name = f"{clean_name}_{uuid.uuid4().hex}.{ext}"
    return base_folder / new_name

@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Accept a multipart/form-data request with a 'file' field.
    Validates file type, size, and safe filename before saving.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    uploaded = request.files["file"]
    if uploaded.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(uploaded.filename):
        return jsonify({"error": f"File type {uploaded.filename.rsplit('.', 1)[-1]} not allowed"}), 400

    # Read file content to enforce size limit and compute hash
    file_bytes = uploaded.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        uploaded.seek(0)
        return jsonify({"error": "File too large"}), 413
    uploaded.seek(0)

    # Compute a simple hash for integrity verification (optional)
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Generate a safe unique path
    safe_path = generate_unique_path(UPLOAD_FOLDER, uploaded.filename)

    # Save the file
    safe_path.write_bytes(file_bytes)

    # Register the file (store absolute path)
    FILE_REGISTRY[safe_path.name] = safe_path

    logger.info(f"Uploaded file: {safe_path.name} (hash: {file_hash[:8]}...)")

    return jsonify({
        "status": "success",
        "filename": safe_path.name,
        "hash": file_hash
    }), 201

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """
    Serve a file by its stored name.
    Uses send_from_directory with the absolute path from the registry.
    """
    # Resolve absolute path from relative registry entry
    abs_path = (UPLOAD_FOLDER / filename).resolve()
    if abs_path.is_dir():
        return jsonify({"error": "Path is a directory"}), 400
    if abs_path.stat().st_size == 0:
        return jsonify({"error": "File is empty"}), 404

    # Verify the file still exists on disk (defensive)
    if not abs_path.exists():
        logger.warning(f"File missing from disk: {filename}")
        return jsonify({"error": "File not found"}), 404

    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
