from flask import Flask, request, send_from_directory, jsonify, abort
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Ensure the uploads directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    # If user does not select file, the browser submits an
    # empty part without a filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # Save the file to the uploads directory
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        return jsonify({"message": "File uploaded successfully"}), 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    # Check if the file exists
    if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        abort(404)

    # Return the file
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
