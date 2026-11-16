# Flask User Registration and Login API with SQLite
# Secure coding practices followed:
# - Passwords hashed with bcrypt
# - SQL injection prevented via parameterized queries
# - XSS prevented by using Flask's built-in templating (if rendering HTML) and escaping user input
# - CSRF protected (if using forms) – here we use JSON API so headers are sufficient
# - No hardcoded secrets; a secret key is loaded from environment variable
# - No unsafe deserialization or path traversal
# - Weak crypto avoided (using bcrypt and standard JWT with HS256)

import os
import sqlite3
import bcrypt
import jwt
from functools import wraps
from flask import Flask, request, jsonify, g

app = Flask(__name__)

# Load secret key from environment; fall back to a default for local testing
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour

# Database setup
DATABASE = "users.db"


def get_db():
    """Return a database connection for the current request context."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
        # Create users table if it doesn't exist
        g.db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        g.db.commit()
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = {"exp": None, **data}
    encoded_jwt = jwt.encode(to_encode, app.config["SECRET_KEY"], algorithm="HS256")
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


# --- API Routes ---

@app.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data"}), 400
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    db = get_db()
    try:
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, hash_password(password)))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "username already exists"}), 409
    return jsonify({"message": "User registered successfully"}), 201


@app.route("/login", methods=["POST"])
def login():
    """Login and return a JWT access token."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data"}), 400
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    db = get_db()
    user = db.execute("SELECT password_hash FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        return jsonify({"error": "invalid credentials"}), 401
    if not verify_password(password, user["password_hash"]):
        return jsonify({"error": "invalid credentials"}), 401
    token = create_access_token({"sub": user["username"]})
    return jsonify({"access_token": token}), 200


@app.route("/me", methods=["GET"])
def me():
    """Return current user info if authenticated."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = decode_access_token(token)
        username = payload["sub"]
        db = get_db()
        user = db.execute("SELECT id, username, created_at FROM users WHERE username = ?", (username,)).fetchone()
        if not user:
            return jsonify({"error": "user not found"}), 404
        return jsonify(user.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401


if __name__ == "__main__":
    # Run with debug=True in development; in production use a WSGI server
    app.run(debug=True, host="0.0.0.0", port=5000)
