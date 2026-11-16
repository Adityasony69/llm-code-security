from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_user, logout_user, current_user, login_required, confirm_reset_request, reset_password
from flask_security.utils import generate_password_hash, verify_password_hash
from flask_mail import Mail, Message
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECURITY_PASSWORD_SALT'] = 'your_salt'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['MAIL_SERVER'] = 'your_mail_server'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email'
app.config['MAIL_PASSWORD'] = 'your_password'

db = SQLAlchemy(app)
mail = Mail(app)

# Define models
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        email = request.form['email']
        user = user_datastore.find_user(email=email)
        if user:
            token = user_datastore.generate_reset_token(user)
            msg = Message('Password Reset', sender='noreply@example.com', recipients=[user.email])
            msg.body = f"Click the following link to reset your password: {url_for('reset_confirm', token=token, _external=True)}"
            mail.send(msg)
            flash('An email has been sent with instructions to reset your password.')
            return redirect(url_for('login'))
        else:
            flash('User not found.', 'error')
    return render_template('reset.html')

@app.route('/reset_confirm/<token>', methods=['GET', 'POST'])
def reset_confirm(token):
    if request.method == 'POST':
        new_password = request.form['new_password']
        user = user_datastore.find_user_by_reset_token(token)
        if user:
            user_datastore.confirm_reset_token(user)
            user_datastore.set_password(user, new_password)
            db.session.commit()
            flash('Password reset successfully.')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired token.', 'error')
    return render_template('reset_confirm.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = user_datastore.find_user(email=email)
        if user and verify_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
