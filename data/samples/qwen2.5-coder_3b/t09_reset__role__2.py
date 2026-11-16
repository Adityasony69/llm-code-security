from flask import Flask, request, jsonify, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer, BadSignature
import os
from datetime import datetime, timedelta
import base64
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reset_password.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def generate_reset_token(self):
        token = serializer.dumps(self.id, salt='reset-password-salt')
        return base64.b64encode(token.encode()).decode()

    @staticmethod
    def verify_reset_token(token):
        try:
            user_id = base64.b64decode(token.encode()).decode()
            user_id = serializer.loads(user_id, salt='reset-password-salt', max_age=3600)
            return User.query.get(user_id)
        except BadSignature:
            return None

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            token = user.generate_reset_token()
            reset_url = url_for('reset_password', token=token, _external=True)
            # Send the reset URL to the user via email or any other method
            return jsonify({'message': f'Password reset link sent to {username} at {reset_url}'})
        else:
            return jsonify({'error': 'User not found'}), 404
    return render_template('reset.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        password = request.form.get('password')
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user:
            user.password = password
            db.session.commit()
            return jsonify({'message': 'Password reset successfully'})
        else:
            return jsonify({'error': 'User not found'}), 404
    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
