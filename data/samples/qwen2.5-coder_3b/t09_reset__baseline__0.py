from flask import Flask, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reset_password.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class ResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(120), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

def generate_reset_token(user_id):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    expiration = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    token = serializer.dumps(user_id, salt='reset-password-token')
    reset_token = ResetToken(user_id=user_id, token=token, expires_at=expiration)
    db.session.add(reset_token)
    db.session.commit()
    return token

def verify_reset_token(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        user_id = serializer.loads(token, salt='reset-password-token', max_age=3600)  # Token expires in 1 hour
        reset_token = ResetToken.query.filter_by(user_id=user_id).first()
        if reset_token and reset_token.expires_at > datetime.utcnow():
            return user_id
    except BadSignature:
        pass
    return None

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        return '''
        <h1>Reset Password</h1>
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="submit" value="Reset Password">
        </form>
        '''
    elif request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            token = generate_reset_token(user.id)
            return redirect(url_for('reset_password_confirm', token=token))
        return 'User not found', 404

@app.route('/reset-password/confirm/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    user_id = verify_reset_token(token)
    if user_id:
        if request.method == 'GET':
            return '''
            <h1>Confirm Password Reset</h1>
            <form method="post">
                <input type="password" name="new_password" placeholder="New Password" required>
                <input type="submit" value="Reset Password">
            </form>
            '''
        elif request.method == 'POST':
            new_password = request.form['new_password']
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user = User.query.filter_by(id=user_id).first()
            user.password_hash = hashed_password
            db.session.commit()
            return 'Password reset successful', 200
    else:
        return 'Invalid or expired token', 400

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
