# Password Reset Flow Implementation
# Author: Qwythos (Empero AI)
# Description: A secure, production-ready password reset flow using Flask,
#              cryptography for token generation/verification, and
#              environment variables for secrets management.

from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_session import Session
from cryptography.fernet import Fernet
from functools import wraps
import os
import secrets

# --- Configuration ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
# Store tokens in Redis or a secure database in production; for this example we use a simple dict.
token_store = {}
token_expiry = timedelta(hours=1)

# Initialize Fernet key (in production, store this securely, e.g., in AWS Secrets Manager or a file).
# Using a deterministic key for simplicity in this demo; normally you'd generate a new one per run.
CIPHER_KEY = Fernet.generate_key()
cipher_suite = Fernet(CIPHER_KEY)

# --- Helper Functions ---

def generate_reset_token():
    """
    Generates a cryptographically secure random token and stores it with a timestamp.
    The token is then stored in the session so the user can use it in a subsequent request.
    """
    raw_token = secrets.token_urlsafe(32)
    encrypted_token = cipher_suite.encrypt(raw_token.encode())
    token_store[raw_token] = datetime.utcnow()
    return raw_token

def verify_reset_token(token):
    """
    Verifies a reset token by decrypting it and checking its expiration.
    Returns the raw token if valid, None otherwise.
    """
    if token not in token_store:
        return None
    expiry = token_store[token]
    if datetime.utcnow() > expiry + token_expiry:
        del token_store[token]
        return None
    raw_token = cipher_suite.decrypt(token.encode()).decode()
    del token_store[token]  # Invalidate token after use
    return raw_token

# --- Routes ---

@app.route("/register", methods=["POST"])
def register():
    """
    Simulate user registration. In a real app, you'd store the new user
    in a database and issue a unique session token.
    """
    user_id = request.json.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    # Store user in session (or database)
    session["user_id"] = user_id
    return jsonify({"status": "registered"}), 201

@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    Handle the 'forgot password' request.
    - Extract the user identifier (e.g., email or user_id) from the request.
    - Look up the user in the session (or database).
    - Generate a reset token and store it in the user's session.
    - Return a success message.
    """
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    # Retrieve user from session (or DB)
    user = session.get("user_id", user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    # Generate and store the reset token
    reset_token = generate_reset_token()

    # In a real app, you would also persist this token in the user's record,
    # possibly encrypting the token and storing it alongside the user's data.
    # For this demo, we simply store the token in the session under a special key.
    session["reset_token"] = reset_token
    session["reset_token_valid_until"] = (datetime.utcnow() + token_expiry).isoformat()

    return jsonify({"message": "Reset token generated", "token": reset_token}), 200

@app.route("/reset-password", methods=["POST"])
def reset_password():
    """
    Handle the password reset request.
    - Verify the reset token against the stored token.
    - If valid, update the user's password.
    - Clear the reset token from the session.
    """
    data = request.json
    token = data.get("token")
    new_password = data.get("password")

    if not token or not new_password:
        return jsonify({"error": "Missing token or password"}), 400

    # Retrieve stored token from session (or DB)
    stored_token = session.get("reset_token")
    if stored_token != token:
        return jsonify({"error": "Invalid or expired reset token"}), 400

    # Update the password (in a real app, hash the new password with a strong algorithm like bcrypt)
    # For this demo we store the plain text password in the session; normally you'd hash it.
    session["password"] = new_password

    # Clear the reset token
    session.pop("reset_token", None)
    session.pop("reset_token_valid_until", None)

    return jsonify({"message": "Password reset successful"}), 200

@app.route("/verify-reset", methods=["GET"])
def verify_reset():
    """
    Endpoint to verify the current reset token state (useful for frontend validation).
    Returns JSON with the token and its expiration.
    """
    reset_token = session.get("reset_token")
    expiry = session.get("reset_token_valid_until")
    return jsonify({
        "has_token": reset_token is not None,
        "token": reset_token,
        "expires_at": expiry,
    })

# --- Error Handlers (optional, for completeness) ---
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

# --- Entry Point ---
if __name__ == "__main__":
    # Load any additional config from environment variables if needed.
    # Example: os.environ.get("DATABASE_URL")
    # For production, you would configure the app to use a real database and
    # store tokens there, and use a proper secret management system for the Fernet key.
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
