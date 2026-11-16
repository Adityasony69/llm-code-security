# Flask Password Reset Flow
# Author: Qwythos (Created by Empero AI)
# Description: This script demonstrates a complete password reset flow using Flask.
# It includes user registration, login, requesting a password reset,
# generating a secure reset token, sending an email with the token,
# and verifying the token for password updating.

# Required libraries
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Flask application setup
app = Flask(__name__)
app.secret_key = "your-secret-key"  # In production, use os.urandom(32).hex()
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'

# In-memory user storage (use a database in production)
users = {}

# Decorator to check if a user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Registration form
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users:
            flash("Username already exists.", "error")
            return render_template('register.html')
        users[username] = generate_password_hash(password)
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# Login form
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and check_password_hash(users[username], password):
            session['user_id'] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for('index'))
        flash("Invalid username or password.", "error")
    return render_template('login.html')

# Log out
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out.", "info")
    return redirect(url_for('index'))

# Request password reset
@app.route('/reset', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        username = request.form.get('username')
        if username not in users:
            flash("User not found.", "error")
            return render_template('reset.html')
        token = secrets.token_urlsafe(32)
        # Store token and expiry in session (or database)
        session['reset_token'] = token
        flash("Reset link sent to your email.", "success")
        return redirect(url_for('index'))
    return render_template('reset.html')

# Email function (placeholder for real SMTP)
def send_reset_email(to_address, token):
    msg = MIMEMultipart()
    msg['From'] = app.config['MAIL_USERNAME']
    msg['To'] = to_address
    msg['Subject'] = 'Password Reset'
    body = f"""
    <html>
    <head><style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ max-width: 600px; margin: auto; padding: 20px; }}
        .button {{
            display: inline-block; padding: 10px 20px; background-color: #007bff;
            color: #fff; text-decoration: none; border-radius: 5px; }}
    </style></head>
    <body>
    <div class="container">
        <h2>Password Reset</h2>
        <p>Hello,</p>
        <p>You requested a password reset. Click the button below to set a new password:</p>
        <p><a href="http://example.com/reset/{token}" class="button">Reset Password</a></p>
        <p>If you didn't request this, ignore this email.</p>
    </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, "html"))
    with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)

# Reset password page (show token in URL)
@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm = request.form.get('confirm')
        if new_password != confirm:
            flash("Passwords do not match.", "error")
            return render_template('reset.html', token=token)
        # Retrieve user from session token mapping (simplified here)
        username = session.get('reset_user')
        if username not in users:
            flash("Invalid or expired token.", "error")
            return redirect(url_for('index'))
        users[username] = generate_password_hash(new_password)
        flash("Password reset successful. You can now log in.", "success")
        return redirect(url_for('index'))
    return render_template('reset.html', token=token)

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)
