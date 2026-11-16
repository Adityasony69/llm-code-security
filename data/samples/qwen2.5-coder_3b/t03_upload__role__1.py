from flask import Flask, request, send_file, abort, jsonify
import os

app = Flask(__name__)

# Define the directory where uploaded files will be stored
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Route to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        abort(400, description="No file part in the request")
    file = request.files['file']
    if file.filename == '':
        abort(400, description="No selected file")

    # Save the file to the upload directory
    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # Return a success message with the filename
    return jsonify({'message': 'File uploaded successfully', 'filename': filename}), 201

# Route to handle file downloads
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        abort(404, description="File not found")
    
    # Send the file to the client
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
