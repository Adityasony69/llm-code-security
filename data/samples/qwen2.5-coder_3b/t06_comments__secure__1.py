from flask import Flask, request, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Secret key for CSRF protection and hashing passwords
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///comments.db'  # SQLite database URI
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

# Comment model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

@app.route('/')
def index():
    comments = Comment.query.all()
    return render_template('index.html', comments=comments)

@app.route('/add', methods=['GET', 'POST'])
def add_comment():
    form = CommentForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_comment = Comment(content=form.comment.data, password=hashed_password)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html', form=form)

class CommentForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Add Comment')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
