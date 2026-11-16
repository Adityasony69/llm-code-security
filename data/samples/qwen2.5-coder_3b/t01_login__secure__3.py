from flask import Flask, request, jsonify, redirect, url_for, render_template_string
import sqlite3
import os
import bcrypt

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure secret key for session management

# Database setup
DATABASE = 'users.db'

def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_tables()

# Helper function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Helper function to check password
def check_password(stored_hash, password):
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    # Validate inputs
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # Hash password
    password_hash = hash_password(password)

    # Insert user into database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Validate inputs
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # Connect to database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()

    if result and check_password(result[0], password):
        # Login successful
        conn.close()
        return redirect(url_for('dashboard'))
    else:
        conn.close()
        return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/dashboard')
def dashboard():
    return render_template_string('<h1>Welcome to the Dashboard</h1>')

if __name__ == '__main__':
    app.run(debug=True)
