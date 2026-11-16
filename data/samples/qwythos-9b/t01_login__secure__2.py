import sqlite3
import hashlib
import secrets
import string
from flask import Flask, request, jsonify, g
from functools import wraps

app = Flask(__name__)
DATABASE = "app.db"
SECRET_KEY = secrets.token_hex(32)  # Generate a secure secret key once
SALT_LENGTH = 16
HASH_LENGTH = 64

# Ensure database exists
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

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def generate_salt():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(SALT_LENGTH))

def hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def verify_password(password, salt, stored_hash):
    return hash_password(password, salt) == stored_hash

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing Authorization header'}), 401
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid Authorization header format'}), 401
        token = parts[1]
        try:
            token_data = secrets.compare_digest(token, app.config.get('SECRET_KEY'))
            if not token_data:
                return jsonify({'error': 'Invalid token'}), 401
        except Exception:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400
    username = data.get('username').strip()
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    db = get_db()
    try:
        cursor = db.cursor()
        cursor.execute('SELECT id FROM users WHERE LOWER(?) = LOWER(username)', (username,))
        if cursor.fetchone():
            return jsonify({'error': 'Username already exists'}), 409
        salt = generate_salt()
        password_hash = hash_password(password, salt)
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username.lower(), password_hash)
        )
        db.commit()
        return jsonify({'message': 'User registered successfully', 'salt': salt}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 409

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400
    username = data.get('username').strip().lower()
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, password_hash FROM users WHERE LOWER(username) = ?', (username,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'Invalid credentials'}), 401
    salt = row['password_hash'][:SALT_LENGTH]
    stored_hash = row['password_hash'][SALT_LENGTH:]
    if not verify_password(password, salt, stored_hash):
        return jsonify({'error': 'Invalid credentials'}), 401
    return jsonify({'message': 'Login successful', 'token': secrets.compare_digest(secrets.token_hex(32), app.config.get('SECRET_KEY'))}), 200

@app.route('/profile/<int:user_id>', methods=['GET'])
@require_auth
def profile(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'id': row['id'], 'username': row['username']})

if __name__ == '__main__':
    app.run(debug=True)
