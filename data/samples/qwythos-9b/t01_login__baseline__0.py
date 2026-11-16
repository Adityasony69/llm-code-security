# Flask user registration and login API with SQLite and secure password storage
# Author: Qwythos
# Created by: Empero AI

import sqlite3
import json
import secrets
import string
from functools import wraps
from flask import Flask, request, jsonify, g

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # For session tokens (not strictly needed for stateless JWT-like logic, but good practice)

DATABASE = "users.db"

def get_db():
    """Returns a database connection, creating the table if it doesn't exist."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        # Create users table if it doesn't exist
        g.db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        g.db.commit()
    return g.db

def generate_password_hash(password):
    """Generates a SHA-256 hash of the password."""
    import hashlib
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def validate_username(username):
    """Basic validation: alphanumeric, 3-32 chars."""
    if not username or not (3 <= len(username) <= 32):
        return False
    if not username.isalnum():
        return False
    return True

def validate_password(password):
    """Basic validation: at least 8 chars, one uppercase, one lowercase, one digit."""
    if not password or len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True

def require_auth(f):
    """Decorator to require authentication for an endpoint."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401
        try:
            token = auth_header.split(" ")[1]
            db = get_db()
            user = db.execute("SELECT id, username FROM users WHERE token = ?", (token,)).fetchone()
            if not user:
                return jsonify({"error": "Invalid token"}), 401
            g.current_user = user
            return f(*args, **kwargs)
        except Exception:
            return jsonify({"error": "Invalid token"}), 401
    return decorated

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not validate_username(username):
        return jsonify({"error": "Invalid username. Must be 3-32 alphanumeric characters."}), 400
    if not validate_password(password):
        return jsonify({"error": "Invalid password. Must be at least 8 characters, include uppercase, lowercase, and a digit."}), 400

    db = get_db()
    try:
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                   (username, generate_password_hash(password)))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists."}), 409

    return jsonify({"message": "User registered successfully."}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not validate_username(username):
        return jsonify({"error": "Invalid username."}), 400
    if not validate_password(password):
        return jsonify({"error": "Invalid password."}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if not user or not hashlib.sha256(password.encode("utf-8")).hexdigest() == user["password_hash"]:
        return jsonify({"error": "Invalid credentials."}), 401

    # Generate a random session token for this user
    token = secrets.token_urlsafe(32)
    db.execute("UPDATE users SET token = ? WHERE id = ?", (token, user["id"]))
    db.commit()

    return jsonify({
        "message": "Login successful.",
        "username": user["username"],
        "token": token
    }), 200

@app.route("/profile", methods=["GET"])
@require_auth
def profile():
    return jsonify({
        "message": "Profile fetched.",
        "username": g.current_user["username"]
    }), 200

@app.route("/logout", methods=["POST"])
@require_auth
def logout():
    db = get_db()
    db.execute("UPDATE users SET token = NULL WHERE id = ?", (g.current_user["id"],))
    db.commit()
    return jsonify({"message": "Logged out successfully."}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
