from flask import Flask, request, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
db = SQLAlchemy(app)
mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    reset_token = db.Column(db.String(128), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, token_length=64):
        self.reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=token_length))
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

    def is_token_valid(self, token):
        if self.reset_token and self.reset_token_expiry > datetime.utcnow():
            return token == self.reset_token
        return False

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            user.generate_reset_token()
            send_reset_email(user)
            flash('Password reset email sent. Check your inbox.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found. Please check your username.', 'danger')
    return render_template('reset_password.html')

def send_reset_email(user):
    token = user.reset_token
    msg = Message('Password Reset Request', sender='your-email@example.com', recipients=[user.username])
    msg.body = f'''To reset your password, visit the following link within the next hour:

{url_for('reset_token', token=token, _external=True)}

If you did not request a password reset, please ignore this email.
'''
    mail.send(msg)

@app.route('/reset-token/<token>', methods=['GET', 'POST'])
def reset_token(token):
    user = User.query.filter_by(reset_token=token).first()
    if user and user.is_token_valid(token):
        if request.method == 'POST':
            password = request.form['password']
            user.set_password(password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            flash('Password reset successful. You can now log in.', 'success')
            return redirect(url_for('login'))
        return render_template('reset_password_form.html')
    else:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('reset_password'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
