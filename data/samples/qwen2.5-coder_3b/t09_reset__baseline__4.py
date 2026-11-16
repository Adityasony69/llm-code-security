from flask import Flask, request, jsonify, redirect, url_for
from itsdangerous import URLSafeTimedSerializer, BadSignature
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for signing the token

# Simulated database to store users
users = {
    'user1': {
        'email': 'user1@example.com',
        'password': 'password1'
    },
    'user2': {
        'email': 'user2@example.com',
        'password': 'password2'
    }
}

# Secret key for token generation
secret_key = os.urandom(24)

# Serializer for token generation and verification
serializer = URLSafeTimedSerializer(secret_key)

# Route to generate a password reset link
@app.route('/reset-password', methods=['GET'])
def reset_password():
    email = request.args.get('email')
    user = users.get(email)
    if user:
        token = serializer.dumps(email, salt='email-reset')
        reset_url = url_for('reset_password_with_token', token=token, _external=True)
        # You can send an email with the reset_url here
        return jsonify({'message': 'Password reset link sent', 'reset_url': reset_url})
    else:
        return jsonify({'error': 'Email not found'}), 404

# Route to handle the password reset with the token
@app.route('/reset-password/<token>', methods=['POST'])
def reset_password_with_token(token):
    try:
        email = serializer.loads(token, salt='email-reset')
        new_password = request.json.get('new_password')
        if new_password:
            users[email]['password'] = new_password
            return jsonify({'message': 'Password reset successfully'})
        else:
            return jsonify({'error': 'New password is required'}), 400
    except BadSignature:
        return jsonify({'error': 'Invalid or expired token'}), 400

# Route to verify the token (for demonstration, this is a simple check)
@app.route('/verify-token/<token>', methods=['GET'])
def verify_token(token):
    try:
        email = serializer.loads(token, salt='email-reset')
        return jsonify({'message': 'Token verified', 'email': email})
    except BadSignature:
        return jsonify({'error': 'Invalid or expired token'}), 400

if __name__ == '__main__':
    app.run(debug=True)
