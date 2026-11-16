from flask import Flask, request, jsonify, redirect, url_for
import secrets
import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# In-memory storage for reset tokens
reset_tokens = {}

def generate_reset_token(email):
    token = secrets.token_urlsafe(32)
    reset_tokens[token] = {
        'email': email,
        'expiry': datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    }
    return token

def verify_reset_token(token):
    if token in reset_tokens:
        reset_info = reset_tokens[token]
        if reset_info['expiry'] > datetime.utcnow():
            del reset_tokens[token]
            return reset_info['email']
    return None

@app.route('/reset-password', methods=['POST'])
def reset_password_request():
    email = request.json.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    token = generate_reset_token(email)
    reset_link = url_for('reset_password', token=token, _external=True)
    return jsonify({'message': f'Password reset link sent to {email}. Click the link to reset your password.', 'reset_link': reset_link}), 200

@app.route('/reset-password/<token>', methods=['GET'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        return jsonify({'error': 'Invalid or expired token'}), 400

    # Logic to reset the password here
    # For demonstration purposes, we'll just print the email
    print(f'Password reset requested for email: {email}')

    return jsonify({'message': 'Password reset link is valid. You can now reset your password.'}), 200

if __name__ == '__main__':
    app.run(debug=True)
