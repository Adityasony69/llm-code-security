from flask import Flask, request, render_template, redirect, url_for
import secrets
import os
import json

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)

# In-memory store for comments
comments = []

def store_comment(comment):
    with open('comments.json', 'w') as f:
        json.dump(comments, f)

def load_comments():
    try:
        with open('comments.json', 'r') as f:
            comments.extend(json.load(f))
    except FileNotFoundError:
        pass

load_comments()

@app.route('/')
def index():
    return render_template('index.html', comments=comments)

@app.route('/add_comment', methods=['POST'])
def add_comment():
    comment = request.form['comment']
    if not comment:
        return "Comment cannot be empty", 400
    
    comments.append(comment)
    store_comment(comments)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
