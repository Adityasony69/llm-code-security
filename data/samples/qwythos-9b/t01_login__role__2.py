import sqlite3
import hashlib
import secrets
import string
from flask import Flask, request, jsonify, g
from functools import wraps

app = Flask(__name__)
DATABASE = 'auth.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(password, hashed):
    return hashlib.sha256(password.encode('utf-8')).hexdigest() == hashed

def generate_token():
    return secrets.token_urlsafe(32)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Missing token'}), 401
        db = get_db()
        user = db.execute('SELECT id, username FROM users WHERE token = ?', (token,)).fetchone()
        if not user:
            return jsonify({'error': 'Invalid token'}), 401
        g.user = user
        return f(*args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    username = data['username'].strip()
    password = data['password'].strip()
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    db = get_db()
    existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        return jsonify({'error': 'Username already exists'}), 409
    hashed_pw = hash_password(password)
    db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, hashed_pw))
    db.commit()
    token = generate_token()
    db.execute('INSERT INTO tokens (user_id, token, expires_at) VALUES (?, ?, ?)', 
                (db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()[0], token, '2099-12-31'))
    db.commit()
    return jsonify({'message': 'User registered', 'token': token}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    username = data['username'].strip()
    password = data['password'].strip()
    db = get_db()
    user = db.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,)).fetchone()
    if not user or not verify_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = generate_token()
    db.execute('INSERT INTO tokens (user_id, token, expires_at) VALUES (?, ?, ?)', 
                (user['id'], token, '2099-12-31'))
    db.commit()
    return jsonify({'message': 'Login successful', 'token': token}), 200

@app.route('/profile', methods=['GET'])
@requires_auth
def profile():
    return jsonify({'username': g.user['username']}), 200

@app.route('/logout', methods=['POST'])
@requires_auth
def logout():
    db = get_db()
    db.execute('DELETE FROM tokens WHERE user_id = ? AND token = ?', 
                (g.user['id'], request.headers.get('Authorization', '').replace('Bearer ', '')))
    db.commit()
    return jsonify({'message': 'Logged out'}), 200

if __name__ == '__main__':
    app.run(debug=True)
