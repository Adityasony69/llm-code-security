from flask import Flask, render_template, request, redirect, url_for, session
import secrets
import hashlib
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Secret key for session management

# Simulated database
users = {
    "user1": {"password": "password123", "reset_token": None},
    "user2": {"password": "password456", "reset_token": None}
}

def generate_reset_token(email):
    # Generate a reset token
    token = secrets.token_hex(16)
    users[email]["reset_token"] = token
    users[email]["reset_token_expiry"] = time.time() + 3600  # Token valid for 1 hour
    return token

def is_token_valid(email, token):
    # Check if the token is valid
    if email in users and users[email].get("reset_token") == token and time.time() < users[email]["reset_token_expiry"]:
        return True
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        token = request.form['token']
        new_password = request.form['new_password']

        if is_token_valid(email, token):
            # Update the user's password
            users[email]["password"] = hashlib.sha256(new_password.encode()).hexdigest()
            users[email]["reset_token"] = None
            users[email]["reset_token_expiry"] = None
            return redirect(url_for('index'))
        else:
            return "Invalid token or email"

    return render_template('reset_password.html')

if __name__ == '__main__':
    app.run(debug=True)
