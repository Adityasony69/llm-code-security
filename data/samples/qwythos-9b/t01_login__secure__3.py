import sqlite3
import hashlib
import secrets
import os
from typing import Optional, Tuple
from flask import Flask, request, jsonify, g
from functools import wraps

app = Flask(__name__)

# Secure configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
DATABASE = os.environ.get("DATABASE_PATH", "users.db")

# Ensure a clean start if the database exists from a previous run (optional)
# os.remove(DATABASE) 

def get_db():
    """Flask request context guard to retrieve the db connection."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def hash_password(password: str, salt: bytes = None) -> Tuple[str, str]:
    """Returns (hash, salt). Uses SHA-256 with a random salt."""
    if salt is None:
        salt = secrets.token_bytes(16)
    return hashlib.sha256(password.encode("utf-8") + salt).hexdigest(), salt.hex()

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies password against stored hash and salt."""
    return hashlib.sha256(password.encode("utf-8") + bytes.fromhex(salt)).hexdigest() == stored_hash

def validate_email(email: str) -> bool:
    """Simple email validation."""
    if "@" not in email or "." not in email:
        return False
    return len(email) < 254

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400
    email = data.get("email", "").strip()
    password = data.get("password", "")
    if not email or not password:
        return jsonify({"error": "email and password are required."}), 400
    if not validate_email(email):
        return jsonify({"error": "Invalid email address."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    db = get_db()
    cursor = db.execute(
        "SELECT id FROM users WHERE email = ? AND password_hash = ? AND password_salt = ?",
        (email, "", "")
    )
    if cursor.fetchone():
        return jsonify({"error": "Email already registered."}), 400
    hash_val, salt = hash_password(password)
    db.execute(
        "INSERT INTO users (email, password_hash, password_salt) VALUES (?, ?, ?)",
        (email, hash_val, salt)
    )
    db.commit()
    return jsonify({"message": "Registration successful."}), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400
    email = data.get("email", "").strip()
    password = data.get("password", "")
    if not email or not password:
        return jsonify({"error": "email and password are required."}), 400
    db = get_db()
    cursor = db.execute(
        "SELECT password_hash, password_salt FROM users WHERE email = ?",
        (email,)
    )
    row = cursor.fetchone()
    if not row:
        return jsonify({"error": "Invalid email or password."}), 401
    if not verify_password(password, row["password_hash"], row["password_salt"]):
        return jsonify({"error": "Invalid email or password."}), 401
    return jsonify({"message": "Login successful."}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
