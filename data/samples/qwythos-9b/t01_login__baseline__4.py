# -*- coding: utf-8 -*-
"""
Flask user registration and login API backed by SQLite.
- User model with password hashing (bcrypt).
- Endpoints: POST /register, POST /login, GET /users (list), GET /user/<id> (detail).
- SQLite database created automatically on first run.
- Single file: install dependencies via pip, then run this script.
"""

import os
import sqlite3
import bcrypt
from flask import Flask, request, jsonify, g

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
DATABASE = "users.db"


def get_db():
    """Return a database connection, reusing one per request thread."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables if they do not exist."""
    with app.app_context():
        db = get_db()
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.commit()


def create_user(email: str, password: str) -> dict:
    """Register a new user. Returns the created user dict."""
    db = get_db()
    # Hash password with bcrypt (cost 12)
    pwd_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    cursor = db.execute(
        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
        (email, pwd_hash),
    )
    db.commit()
    return {
        "id": cursor.lastrowid,
        "email": email,
        "created_at": db.execute(
            "SELECT created_at FROM users WHERE id = ?", (cursor.lastrowid,).fetchone()[0],
        ),
    }


def find_user(email: str) -> dict | None:
    """Look up a user by email. Returns row dict or None."""
    db = get_db()
    row = db.execute(
        "SELECT id, email, password_hash, created_at FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    return dict(row) if row else None


def check_password(password: str, stored_hash: bytes) -> bool:
    """Return True if password matches stored hash."""
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
    email = data.get("email").strip().lower()
    password = data.get("password", "").strip()
    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400
    existing = find_user(email)
    if existing:
        return jsonify({"error": "email already registered"}), 409
    user = create_user(email, password)
    return jsonify({"message": "user created", "user": user}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400
    user = find_user(email)
    if not user:
        return jsonify({"error": "user not found"}), 404
    if not check_password(password, user["password_hash"]):
        return jsonify({"error": "invalid password"}), 401
    # Return minimal user info (no password hash)
    return jsonify({"message": "login successful", "user": {"id": user["id"], "email": user["email"]}}), 200


@app.route("/users", methods=["GET"])
def list_users():
    db = get_db()
    rows = db.execute(
        "SELECT id, email, password_hash, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    users = []
    for row in rows:
        users.append(
            {
                "id": row["id"],
                "email": row["email"],
                "created_at": row["created_at"],
            }
        )
    return jsonify({"users": users}), 200


@app.route("/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    row = get_db().execute(
        "SELECT id, email, password_hash, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if not row:
        return jsonify({"error": "user not found"}), 404
    return jsonify(
        {
            "id": row["id"],
            "email": row["email"],
            "created_at": row["created_at"],
        }
    ), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
