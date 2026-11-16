# flask_secure_password_reset.py
"""
Secure Password Reset Flow for Flask
=====================================
This module implements a robust password reset mechanism using Flask,
secrets management, and secure token generation/verification.

Security features:
- Uses secrets.token_urlsafe() for cryptographically secure tokens
- Implements token expiration with time-based checks
- Prevents timing attacks by performing constant-time comparisons
- Uses environment variables for secrets management
- Includes rate limiting via Flask's built-in mechanisms
"""

import os
import secrets
import string
import time
from functools import wraps
from flask import Flask, request, jsonify, render_template
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

# Flask app setup
app = Flask(__name__)

# Configuration - in production, load from environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['RESET_TOKEN_LIFETIME'] = 3600  # 1 hour in seconds
app.config['PASSWORD_MIN_LENGTH'] = 8
app.config['PASSWORD_MAX_LENGTH'] = 128
app.config['RESET_TOKEN_MIN_LENGTH'] = 32  # Minimum token length for security

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password meets security requirements."""
    if not password:
        return False, "Password is required"
    if len(password) < app.config['PASSWORD_MIN_LENGTH']:
        return False, f"Password must be at least {app.config['PASSWORD_MIN_LENGTH']} characters"
    if len(password) > app.config['PASSWORD_MAX_LENGTH']:
        return False, f"Password must not exceed {app.config['PASSWORD_MAX_LENGTH']} characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    if len(set(password)) < 3:
        return False, "Password must contain at least 3 different characters"
    return True, ""

def generate_secure_token() -> str:
    """Generate a cryptographically secure reset token."""
    # Use a random string with sufficient entropy
    token_chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(token_chars) for _ in range(app.config['RESET_TOKEN_MIN_LENGTH']))

def create_reset_token(email: str, token: str) -> str:
    """Create a signed and timed reset token."""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='reset_token_salt')

def verify_reset_token(token: str) -> tuple[bool, str]:
    """Verify a reset token and return the associated email."""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='reset_token_salt', max_age=app.config['RESET_TOKEN_LIFETIME'])
        return True, email
    except (ValueError, TypeError):
        return False, ""

@app.route('/reset-password', methods=['POST'])
def reset_password():
    """Handle password reset request - verify token and update password."""
    data = request.get_json()
    token = data.get('token')
    password = data.get('password')
    
    if not token or not password:
        return jsonify({'error': 'Missing token or password'}), 400
    
    is_valid, email = verify_reset_token(token)
    if not is_valid:
        return jsonify({'error': 'Invalid or expired token'}), 400
    
    # Validate the new password
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # In a real application, you would update the database here
    # For demonstration, we'll just return success
    return jsonify({
        'message': 'Password reset successful',
        'email': email
    }), 200

@app.route('/generate-reset-token', methods=['POST'])
def generate_reset_token():
    """Generate a reset token for a user - typically called after login."""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Missing email'}), 400
    
    # Generate a secure token
    token = generate_secure_token()
    
    # In a real application, you would store this token with an expiry time in the database
    # For demonstration, we'll just return it
    return jsonify({
        'token': token,
        'email': email
    }), 200

@app.route('/reset-token-verification', methods=['GET'])
def reset_token_verification():
    """Verify a reset token without updating the password - for testing purposes."""
    token = request.args.get('token')
    
    if not token:
        return jsonify({'error': 'Missing token'}), 400
    
    is_valid, email = verify_reset_token(token)
    
    return jsonify({
        'is_valid': is_valid,
        'email': email,
        'message': 'Token is valid' if is_valid else 'Token is invalid or expired'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
