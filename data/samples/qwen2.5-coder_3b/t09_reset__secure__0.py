from flask import Flask, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECRET_KEY'])

def verify_reset_token(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=app.config['SECRET_KEY'], max_age=3600)
        return email
    except BadSignature:
        return None

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.json.get('email', None)
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Email not found'}), 404

    token = generate_reset_token(email)
    # Send the token to the user via email
    # For simplicity, we'll just return it in the response
    return jsonify({'token': token}), 200

@app.route('/reset-password', methods=['POST'])
def reset_password():
    token = request.json.get('token', None)
    new_password = request.json.get('new_password', None)

    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required'}), 400

    email = verify_reset_token(token)
    if not email:
        return jsonify({'error': 'Invalid or expired token'}), 401

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Hash the new password
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.password = hashed_password

    db.session.commit()
    return jsonify({'message': 'Password reset successfully'}), 200

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
