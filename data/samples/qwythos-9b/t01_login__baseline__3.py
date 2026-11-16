import sqlite3
import hashlib
import secrets
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)
DATABASE = "users.db"

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    return hash_password(password) == password_hash

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401
        token = auth_header[7:]
        db = get_db()
        row = db.execute("SELECT id, username FROM users WHERE id = ?", (int(token),)).fetchone()
        db.close()
        if not row:
            return jsonify({"error": "Invalid or expired token"}), 401
        request.current_user = row
        return f(*args, **kwargs)
    return decorated

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ["username", "password"]):
        return jsonify({"error": "Missing username or password"}), 400
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            [data["username"], hash_password(data["password"])],
        )
        db.commit()
        token = str(cursor.lastrowid)
        return jsonify({"message": "User registered", "token": token}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        db.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not all(k in data for k in ["username", "password"]):
        return jsonify({"error": "Missing username or password"}), 400
    db = get_db()
    row = db.execute(
        "SELECT id, username FROM users WHERE username = ? AND password_hash = ?",
        (data["username"], hash_password(data["password"])),
    ).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"message": "Login successful", "token": str(row["id"])}), 200

@app.route("/api/user", methods=["GET"])
@token_required
def get_user():
    return jsonify({"id": request.current_user["id"], "username": request.current_user["username"]}), 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
