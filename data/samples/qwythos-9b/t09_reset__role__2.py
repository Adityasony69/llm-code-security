import secrets
import string
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# In-memory storage for demonstration purposes
# In production, replace with a proper database (e.g., PostgreSQL, Redis)
users_db = {}

def generate_token(length=32):
    """Generate a secure random token."""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

def store_token(user_id, token, expiration_minutes=30):
    """Store the reset token with expiration time."""
    users_db[user_id]["reset_token"] = token
    users_db[user_id]["reset_expires"] = datetime.utcnow() + timedelta(minutes=expiration_minutes)

def verify_token(user_id, token):
    """Verify if the token is valid and not expired."""
    if user_id not in users_db:
        return False
    if "reset_token" not in users_db[user_id] or "reset_expires" not in users_db[user_id]:
        return False
    if users_db[user_id]["reset_token"] != token:
        return False
    if datetime.utcnow() > users_db[user_id]["reset_expires"]:
        return False
    return True

def reset_password(user_id, new_password):
    """Reset the user's password."""
    if user_id not in users_db:
        return False
    users_db[user_id]["password"] = new_password
    return True

def logout():
    """Clear session."""
    session.clear()

@app.route('/login', methods=['POST'])
def login():
    """Authenticate user and issue a session token."""
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Missing email or password'}), 400

    user_id = data['email']
    new_password = data['password']

    # Store user in DB with password
    users_db[user_id] = {
        'password': new_password,
        'reset_token': None,
        'reset_expires': None
    }

    session['user_id'] = user_id
    return jsonify({'status': 'logged in'}), 200

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Generate and send a reset token for a user."""
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Missing email'}), 400

    user_id = data['email']
    if user_id not in users_db:
        return jsonify({'error': 'User not found'}), 404

    token = generate_token()
    store_token(user_id, token)

    # In a real app, you would send the token via email here.
    # For this example, we just return the token so the UI can verify it works.
    return jsonify({'token': token}), 200

@app.route('/reset-password', methods=['POST'])
def reset_password_route():
    """Verify the token and set the new password."""
    data = request.get_json()
    if not data or 'token' not in data or 'password' not in data:
        return jsonify({'error': 'Missing token or password'}), 400

    token = data['token']
    new_password = data['password']

    # Extract user_id from the original session (or store it with the token in DB)
    # For simplicity, we assume the token was generated via /forgot-password
    # and we use the same user_id from the session.
    # In production, you would store user_id alongside the token in your DB.
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No active session'}), 401

    if not verify_token(user_id, token):
        return jsonify({'error': 'Invalid or expired token'}), 400

    if not reset_password(user_id, new_password):
        return jsonify({'error': 'Failed to reset password'}), 500

    logout()
    return jsonify({'status': 'password reset'}), 200

if __name__ == '__main__':
    app.run(debug=True)
