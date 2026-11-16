from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///password_reset.db'
app.config['SECRET_KEY'] = 'dev-secret-key'
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    reset_token = db.Column(db.String(64), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

# In-memory user store (replace with real DB logic in production)
users_db = {}

def init_db():
    with app.app_context():
        db.create_all()
        # Seed a test user
        users_db['testuser'] = {
            'id': 1,
            'username': 'testuser',
            'password_hash': 'hashed_password_here',
            'reset_token': None,
            'reset_token_expires': None
        }

init_db()

# HTML templates for simplicity (in production use real templates)
RESET_REQUEST_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Request Password Reset</title></head>
<body>
  <h2>Request Password Reset</h2>
  <form method="POST">
    <label>Username:</label><br>
    <input type="text" name="username" required>
    <button type="submit">Request Reset</button>
  </form>
</body>
</html>
"""

RESET_TOKEN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Reset Password</title></head>
<body>
  <h2>Reset Your Password</h2>
  <form method="POST">
    <label>New Password:</label><br>
    <input type="password" name="password" required>
    <button type="submit">Reset</button>
  </form>
</body>
</html>
"""

RESET_SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Password Reset Complete</title></head>
<body>
  <h2>Password Reset Successful!</h2>
  <p>You can now log in with your new password.</p>
</body>
</html>
"""

ERROR_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Error</title></head>
<body>
  <h2>Error</h2>
  <p>{{ error_message }}</p>
</body>
</html>
"""

@app.route('/reset/request', methods=['GET', 'POST'])
def request_reset():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            return render_template_string(ERROR_TEMPLATE, error_message="Username is required."), 400
        user = users_db.get(username)
        if not user:
            return render_template_string(ERROR_TEMPLATE, error_message="User not found."), 404
        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=1)
        user['reset_token'] = token
        user['reset_token_expires'] = expires
        return render_template_string(
            RESET_TOKEN_TEMPLATE,
            token=token,
            expires=expires.strftime('%Y-%m-%d %H:%M:%S')
        ), 200
    return render_template_string(RESET_REQUEST_TEMPLATE), 200

@app.route('/reset/<string:token>', methods=['GET', 'POST'])
def reset_token(token):
    # Find user with matching reset token
    for user in users_db.values():
        if user['reset_token'] == token:
            if user['reset_token_expires'] and user['reset_token_expires'] < datetime.utcnow():
                user['reset_token'] = None
                user['reset_token_expires'] = None
                return render_template_string(ERROR_TEMPLATE, error_message="Reset token expired or already used."), 410
            # Invalidate token
            user['reset_token'] = None
            user['reset_token_expires'] = None
            if request.method == 'POST':
                new_password = request.form.get('password', '').strip()
                if not new_password:
                    return render_template_string(ERROR_TEMPLATE, error_message="New password is required."), 400
                # Here you would hash the password and store it
                user['password_hash'] = new_password  # placeholder
                return render_template_string(RESET_SUCCESS_TEMPLATE), 200
            return render_template_string(RESET_TOKEN_TEMPLATE, token=token, expires=token), 200
    return render_template_string(ERROR_TEMPLATE, error_message="Invalid or expired reset token."), 410

@app.route('/reset', methods=['POST'])
def api_reset():
    data = request.get_json()
    username = data.get('username')
    token = data.get('token')
    new_password = data.get('password')
    if not username or not token or not new_password:
        return jsonify({'error': 'Missing required fields'}), 400
    user = users_db.get(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if user['reset_token'] != token:
        return jsonify({'error': 'Invalid token'}), 400
    user['reset_token'] = None
    user['reset_token_expires'] = None
    user['password_hash'] = new_password
    return jsonify({'success': True}), 200

if __name__ == '__main__':
    app.run(debug=True)
