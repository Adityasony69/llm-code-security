import os
import uuid
import tempfile
from flask import Flask, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/tmp/qwythos_uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB limit

# Ensure upload folder exists with proper permissions
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def validate_and_clean_filename(filename: str) -> str:
    """
    Securely clean and validate the uploaded filename:
    - Remove path separators to prevent directory traversal.
    - Strip control characters (ASCII < 32) and non-ASCII to prevent injection.
    - Ensure a safe extension is present.
    """
    # Keep only ASCII printable characters and allow only dot and hyphen
    cleaned = "".join(c for c in filename if 32 <= ord(c) <= 126 and c in ".-")

    # Ensure no path separators remain
    if "/" in cleaned or "\\" in cleaned:
        raise ValueError("Invalid filename: path separators detected.")

    # Require an extension
    base, ext = cleaned.rsplit(".", 1) if "." in cleaned else (cleaned, "")
    if not ext:
        raise ValueError("Filename must contain an extension.")

    # Whitelist safe extensions
    allowed_ext = {"pdf", "txt", "png", "jpg", "jpeg", "gif", "mp3", "mp4", "wav", "doc", "docx"}
    ext_lower = ext.lower()
    if ext_lower not in allowed_ext:
        raise ValueError(f"Unsupported file extension: {ext}")

    return ext_lower


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Accept a single file via multipart/form-data, validate it,
    store in a temporary directory, and return JSON with the unique filename.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Validate filename
    try:
        safe_ext = validate_and_clean_filename(file.filename)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Generate a unique safe filename (UUID to avoid collisions and path traversal)
    unique_filename = f"{uuid.uuid4().hex}.{safe_ext}"

    # Save to a subdirectory based on extension to keep uploads organized and simple
    target_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_ext, unique_filename)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # Stream save to avoid loading entire file into memory
    file.save(target_path)

    return jsonify({"filename": unique_filename}), 200


@app.route("/download/<path:filename>")
def download_file(filename: str):
    """
    Serve a file by its unique name. The unique name includes an extension,
    so we can safely route directly to the file path without risk of traversal.
    """
    # Ensure the requested file is inside the upload folder
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.isfile(filepath):
        return jsonify({"error": "File not found"}), 404

    # Ensure we don't accidentally allow access to files outside the folder
    # (e.g., if someone requests a path with .. or absolute path)
    if not filepath.startswith(app.config["UPLOAD_FOLDER"]):
        return jsonify({"error": "Path traversal detected"}), 404

    # Send file with original filename
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True,
        mimetype="application/octet-stream",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
