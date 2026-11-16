from flask import Flask, render_template, request

app = Flask(__name__)

# In-memory storage for comments
comments = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_comment():
    comment = request.form['comment']
    comments.append(comment)
    return render_template('index.html', comments=comments)

if __name__ == '__main__':
    app.run(debug=True)
