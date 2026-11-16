"""
Flask User Authentication API with SQLite backend.
Includes secure password hashing (bcrypt) and session-based login.
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session, g

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a secure secret key
DATABASE = 'users.db'

# Ensure database exists with proper schema
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Decorator to check if user is authenticated
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Helper to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Helper to verify passwords
def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

# Register a new user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    
    username = data['username'].strip()
    password = data['password']
    
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                       (username, hash_password(password)))
        conn.commit()
        user_id = cursor.lastrowid
        return jsonify({
            'message': 'Registration successful',
            'user_id': user_id,
            'username': username
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 409
    finally:
        conn.close()

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    
    username = data['username'].strip()
    password = data['password']
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Invalid credentials'}), 401
    if not verify_password(row[1], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Set session with expiry
    session['user_id'] = row[0]
    session['username'] = username
    session['logged_in_at'] = datetime.utcnow().isoformat()
    session.permanent = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    
    return jsonify({
        'message': 'Login successful',
        'user_id': row[0],
        'username': username
    })

# Get current user profile
@app.route('/api/user', methods=['GET'])
@login_required
def get_user_profile():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, created_at FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user[0],
        'username': user[1],
        'created_at': user[2]
    })

# Logout endpoint
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
