from flask import Flask, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import uuid

app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///password_reset.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@example.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'

db = SQLAlchemy(app)
mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    reset_token = db.Column(db.String(120), nullable=True)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            reset_token = str(uuid.uuid4())
            user.reset_token = reset_token
            db.session.commit()
            
            send_password_reset_email(user.email, reset_token)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email not found', 'danger')
            return redirect(url_for('reset_password'))
    
    return '''
        <form method="post">
            <p><input type=text name=email placeholder=email></p>
            <p><input type=submit value=Reset Password></p>
        </form>
    '''

def send_password_reset_email(email, reset_token):
    msg = Message('Password Reset Request', sender='your_email@example.com', recipients=[email])
    msg.body = f'''
    To reset your password, visit the following link in your web browser:
    {url_for('reset_password_confirm', token=reset_token, _external=True)}
    '''
    mail.send(msg)

@app.route('/reset-password-confirm/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if user and request.method == 'POST':
        new_password = request.form['password']
        user.password = generate_password_hash(new_password)
        user.reset_token = None
        db.session.commit()
        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return '''
        <form method="post">
            <p><input type=password name=password placeholder=new password></p>
            <p><input type=submit value=Reset Password></p>
        </form>
    '''

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
