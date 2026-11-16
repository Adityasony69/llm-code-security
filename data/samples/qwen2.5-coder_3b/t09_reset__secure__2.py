from flask import Flask, request, jsonify, redirect, url_for, flash
import secrets
import uuid
import hashlib
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reset_password.db'
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
db = SQLAlchemy(app)
mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    reset_token = db.Column(db.String(128), nullable=True)

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = serializer.dumps(email, salt='email-confirm')
    return token

def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=expiration)
        return email
    except Exception:
        return None

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(email)
            user.reset_token = token
            db.session.commit()
            send_password_reset_email(email, token)
            flash('An email has been sent with instructions to reset your password.')
            return redirect(url_for('login'))
        else:
            flash('Email not found.')
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        password = request.form['password']
        user = User.query.filter_by(reset_token=token).first()
        if user:
            user.password_hash = generate_password_hash(password)
            user.reset_token = None
            db.session.commit()
            flash('Password reset successfully.')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired token.')
    return render_template('reset_password.html')

def generate_password_hash(password):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000).hex()

def send_password_reset_email(email, token):
    msg = Message('Password Reset Request',
                  sender='your-email@example.com',
                  recipients=[email])
    msg.body = (f'Click the link below to reset your password:\n'
                f'{url_for("reset_password", token=token, _external=True)}')
    mail.send(msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password_hash == generate_password_hash(password):
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/home')
def home():
    return 'Welcome to the home page!'

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
