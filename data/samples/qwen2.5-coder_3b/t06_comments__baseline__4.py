from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# In-memory storage for comments
comments = []

@app.route('/')
def index():
    return render_template('index.html', comments=comments)

@app.route('/add', methods=['POST'])
def add_comment():
    comment = request.form['comment']
    if comment:
        comments.append(comment)
        return redirect(url_for('index'))
    return "Comment cannot be empty"

if __name__ == '__main__':
    app.run(debug=True)
