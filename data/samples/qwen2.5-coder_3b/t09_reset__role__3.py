from flask import Flask, render_template, request, redirect, url_for, session
import secrets
import string
import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Simulated user database
users = {
    'user1': 'password1',
    'user2': 'password2',
    'user3': 'password3'
}

def generate_reset_token():
    """Generate a random token for password reset."""
    return secrets.token_hex(16)

def is_token_valid(token):
    """Check if the token is valid and hasn't expired."""
    if 'token' not in session:
        return False
    token_time = session['token_time']
    current_time = datetime.now()
    return token == session['token'] and current_time - token_time < timedelta(hours=1)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        token = request.form.get('token')
        new_password = request.form.get('new_password')

        if is_token_valid(token):
            # Update user's password in the database
            users[request.form['username']] = new_password
            session.pop('token', None)
            session.pop('token_time', None)
            return "Password reset successful. You can now log in."
        else:
            return "Invalid or expired token. Please try again."

    if request.method == 'GET':
        token = request.args.get('token')
        if token:
            session['token'] = token
            session['token_time'] = datetime.now()
            return render_template('reset_password.html', token=token)
        return "Invalid token. Please try again."

    return render_template('reset_password.html')

if __name__ == '__main__':
    app.run(debug=True)
