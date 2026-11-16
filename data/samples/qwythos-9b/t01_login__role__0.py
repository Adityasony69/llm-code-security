# Flask User Registration and Login API with SQLite and Password Storage
# Built by Empero AI - Model: Qwythos

import sqlite3
import hashlib
import os
from functools import wraps
from flask import Flask, request, jsonify, g

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
DATABASE = 'users.db'

def get_db():
    """Get database connection, creating if necessary."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        cursor = g.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        g.db.commit()
    return g.db

def hash_password(password):
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash."""
    return hash_password(password) == password_hash

def token_required(f):
    """Decorator to require a valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'error': 'Missing token'}), 401
        # For simplicity in this demo, we trust the token passed in the header
        # In production, validate JWT signature here.
        return f(token, *args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data'}), 400
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not all([username, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password too short'}), 400
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, hash_password(password))
        )
        db.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'error': 'Username or email already exists'}), 409
        return jsonify({'error': 'Database error'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data'}), 400
    username = data.get('username')
    password = data.get('password')
    if not all([username, password]):
        return jsonify({'error': 'Missing required fields'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, username, email, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if not user or not verify_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid credentials'}), 401
    # Simple JWT-like token (in production use a proper library like PyJWT)
    token = hashlib.sha256(f"{user['id']}:{user['username']}:{password}".encode()).hexdigest()
    return jsonify({'token': token, 'user': {'id': user['id'], 'username': user['username'], 'email': user['email']}}), 200

@app.route('/api/user', methods=['GET'])
@token_required
def get_user(token):
    # In real implementation, decode JWT to get user ID
    # For this demo, we assume the token is just a hash and we return a dummy user
    return jsonify({'token': token, 'user': {'id': 1, 'username': token[:8], 'email': 'demo@example.com'}}), 200

if __name__ == '__main__':
    app.run(debug=True)
