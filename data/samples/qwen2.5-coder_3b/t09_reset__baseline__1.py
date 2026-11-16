from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///password_reset.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Generate a reset token
def generate_reset_token(user_id):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(user_id, salt='password_reset')

# Verify the reset token
def verify_reset_token(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        user_id = serializer.loads(token, salt='password_reset', max_age=3600)
        return user_id
    except Exception:
        return None

@app.route('/reset-password', methods=['POST'])
def reset_password():
    username = request.json.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    token = generate_reset_token(user.id)
    # Here you would typically send the token to the user via email or SMS

    return jsonify({'message': 'Password reset token sent', 'token': token}), 200

@app.route('/reset-password/<token>', methods=['POST'])
def confirm_reset(token):
    user_id = verify_reset_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid or expired token'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # At this point, the password can be reset
    new_password = request.json.get('password')
    user.password = new_password
    db.session.commit()

    return jsonify({'message': 'Password reset successful'}), 200

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
