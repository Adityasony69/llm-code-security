# Password Reset Flow Implementation
# Author: Qwythos
# Created by: Empero AI

import secrets
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# In-memory database for demonstration (in production, use a real DB like SQLite, PostgreSQL, etc.)
# Initialize the database with a users table and reset_tokens table
def init_db():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # Insert a dummy user for testing
    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                   ('demo_user', 'password123'))
    conn.commit()
    conn.close()

# Initialize the DB when the module is imported
init_db()

def get_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_username(username):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(user) if user else None

def generate_reset_token():
    return secrets.token_urlsafe(32)

def save_reset_token(user_id, token, expires_delta):
    conn = get_db()
    conn.execute(
        "INSERT INTO reset_tokens (user_id, token, expires_at, used) VALUES (?, ?, ?, 0)",
        (user_id, token, datetime.utcnow() + expires_delta)
    )
    conn.commit()
    conn.close()

def verify_reset_token(token):
    conn = get_db()
    row = conn.execute(
        "SELECT user_id, expires_at, used FROM reset_tokens WHERE token = ? AND used = 0",
        (token,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    expires_at = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
    if expires_at < datetime.utcnow():
        return None
    conn.execute("UPDATE reset_tokens SET used = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return row['user_id']

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and user['password_hash'] == password:
            flash('Login successful. Redirecting...')
            return redirect(url_for('forgot_password'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        user = get_user_by_username(username)
        if not user:
            flash('User not found. Redirecting to login...', 'error')
            return redirect(url_for('index'))
        
        token = generate_reset_token()
        expires_delta = timedelta(hours=1)
        save_reset_token(user['id'], token, expires_delta)
        
        flash('Password reset link sent to your email (demo). Redirecting...', 'success')
        return redirect(url_for('reset_password_page', token=token))
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_page(token):
    user_id = verify_reset_token(token)
    if not user_id:
        flash('Reset link expired or invalid. Redirecting to forgot password...', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form['password']
        conn = get_db()
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_password, user_id)
        )
        conn.commit()
        conn.close()
        flash('Password reset successful! Redirecting to login...', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.context_processor
def utility_processor():
    return dict(current_year=datetime.utcnow().year)

if __name__ == '__main__':
    app.run(debug=True)
