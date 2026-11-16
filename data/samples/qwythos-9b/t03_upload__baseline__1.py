"""
Flask file upload and download endpoints.
Saves uploaded files to the current working directory and allows
retrieval by filename.
"""

import os
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

UPLOAD_FOLDER = '.'

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filename = file.filename
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return jsonify({'message': f'File "{filename}" uploaded successfully', 'filename': filename}), 200

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': f'File "{filename}" not found'}), 404
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
