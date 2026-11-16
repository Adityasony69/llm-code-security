from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# In-memory storage for comments
comments = []

@app.route('/')
def home():
    return render_template('index.html', comments=comments)

@app.route('/submit', methods=['POST'])
def submit_comment():
    comment = request.form['comment']
    comments.append(comment)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
