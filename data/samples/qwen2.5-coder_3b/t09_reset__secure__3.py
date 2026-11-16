from flask import Flask, request, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reset_token.db'
app.config['SECRET_KEY'] = os.urandom(24)
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
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    reset_token = db.Column(db.String(128), nullable=True)

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(128), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.id)
            send_reset_email(user.email, token)
            return redirect(url_for('token_verification', token=token))
        return 'Email not found.'
    return render_template_string('''
        <form method="post">
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" required>
            <button type="submit">Reset Password</button>
        </form>
    ''')

@app.route('/token-verification/<token>')
def token_verification(token):
    try:
        user_id = serializer.loads(token, max_age=3600)
        user = User.query.get(user_id)
        if user:
            return render_template_string('''
                <form method="post">
                    <label for="password">New Password:</label>
                    <input type="password" id="password" name="password" required>
                    <button type="submit">Reset Password</button>
                </form>
            ''')
        return 'Token is invalid.'
    except BadSignature:
        return 'Invalid token.'

@app.route('/reset-password/<token>', methods=['POST'])
def reset_password_with_token(token):
    try:
        user_id = serializer.loads(token, max_age=3600)
        user = User.query.get(user_id)
        if user:
            new_password = request.form['password']
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            return 'Password has been reset.'
        return 'Token is invalid.'
    except BadSignature:
        return 'Invalid token.'

def generate_reset_token(user_id):
    token = serializer.dumps(user_id, salt='reset-password')
    return token

def send_reset_email(email, token):
    msg = MIMEMultipart()
    msg['From'] = app.config['MAIL_USERNAME']
    msg['To'] = email
    msg['Subject'] = 'Password Reset'
    msg.attach(MIMEText(f'Click here to reset your password: {url_for("token_verification", token=token, _external=True)}', 'plain'))

    server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
    server.starttls()
    server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
    text = msg.as_string()
    server.sendmail(app.config['MAIL_USERNAME'], email, text)
    server.quit()

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
