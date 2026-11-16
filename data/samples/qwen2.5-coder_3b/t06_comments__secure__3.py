from flask import Flask, request, render_template_string, redirect, url_for, flash
import secrets
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Securely store comments in a dictionary
comments = {}

def store_comment(username, comment):
    if not username or not comment:
        flash("Username and comment are required.")
        return False
    if len(username) > 50 or len(comment) > 500:
        flash("Username and comment must be between 1 and 50 characters.")
        return False
    if username.startswith('@'):
        flash("Username cannot start with '@'.")
        return False
    comments[username] = comment
    return True

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        comment = request.form.get('comment')
        if store_comment(username, comment):
            flash("Comment saved successfully.")
            return redirect(url_for('index'))
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Comments Page</title>
        </head>
        <body>
            <h1>Comments</h1>
            <form method="post">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
                <label for="comment">Comment:</label>
                <textarea id="comment" name="comment" required></textarea>
                <button type="submit">Submit</button>
            </form>
            {% for username, comment in comments.items() %}
                <h2>{{ username }}</h2>
                <p>{{ comment }}</p>
            {% endfor %}
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
