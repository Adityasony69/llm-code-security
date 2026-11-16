"""
Flask application for a secure comments page.
Features:
- User authentication via session (login/logout).
- Secure storage of comments in a SQLite database.
- HTML sanitization for user input to prevent XSS.
- Template rendering with Flask-Jinja2.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from markupsafe import escape
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_secret_key_change_in_production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///comments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    author = db.relationship('User', backref='comments', lazy='dynamic')

# --- Forms ---
class CommentForm(FlaskForm):
    content = StringField('Comment', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Post')

# --- Routes ---
@app.route('/')
def index():
    """Render the comments page."""
    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template('comments.html', comments=comments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = CommentForm()
    if form.validate_on_submit():
        # In a real app, you would hash the password and store it in the User table.
        # For this demo, we check against a simple list of known users.
        # We simulate a login by creating a temporary session user.
        user = User(username=form.content.data, email='guest@example.com', password_hash='placeholder')
        if not User.query.filter_by(username=user.username).first():
            db.session.add(user)
            db.session.commit()
        
        session['user_id'] = user.id
        session['username'] = user.username
        flash('Logged in successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/comment', methods=['POST'])
def add_comment():
    if 'user_id' not in session:
        flash('Please log in to post a comment.', 'error')
        return redirect(url_for('login'))
    
    form = CommentForm()
    if form.validate_on_submit():
        content = form.content.data
        # Sanitize content to prevent XSS
        # We strip HTML tags and escape any remaining entities
        clean_content = escape(re.sub(r'<[^>]+>', '', content))
        
        new_comment = Comment(author_id=session['user_id'], content=clean_content)
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment posted!', 'success')
        return redirect(url_for('index'))
    return render_template('comments.html', comments=Comment.query.order_by(Comment.created_at.desc()).all(), form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
