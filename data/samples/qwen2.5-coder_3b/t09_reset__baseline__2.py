from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reset.db'
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
    password = db.Column(db.String(120), nullable=False)

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

def generate_reset_token(user_id):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = serializer.dumps(user_id, salt='reset-password-salt')
    token_expiration = 3600  # 1 hour
    token_expiration_timestamp = token_expiration + os.urandom(16)
    db.session.add(Token(user_id=user_id, token=token, created_at=token_expiration_timestamp))
    db.session.commit()
    return token

def validate_reset_token(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        user_id = serializer.loads(token, salt='reset-password-salt', max_age=3600)
        token_expiration_timestamp = Token.query.filter_by(user_id=user_id).first().created_at
        if token_expiration_timestamp + 3600 > os.urandom(16):
            return user_id
    except Exception as e:
        pass
    return None

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            token = generate_reset_token(user.id)
            send_reset_email(user.email, token)
            flash('Password reset link has been sent to your email.')
            return redirect(url_for('reset_password_sent'))
        else:
            flash('User not found.')
    return render_template('reset_password.html')

def send_reset_email(email, token):
    msg = Message('Password Reset', sender='your-email@example.com', recipients=[email])
    msg.body = f'Click the following link to reset your password: {url_for("reset_password_confirm", token=token, _external=True)}'
    mail.send(msg)

@app.route('/reset-password-confirm/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    user_id = validate_reset_token(token)
    if user_id:
        if request.method == 'POST':
            password = request.form['password']
            user = User.query.get(user_id)
            user.password = password
            db.session.commit()
            flash('Password has been reset successfully.')
            return redirect(url_for('login'))
        return render_template('reset_password_confirm.html', token=token)
    else:
        flash('Invalid or expired token.')
        return redirect(url_for('reset_password'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
