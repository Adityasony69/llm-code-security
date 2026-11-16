from flask import Flask, request, render_template

app = Flask(__name__)

# In-memory storage for comments
comments = []

@app.route('/')
def comments_page():
    return render_template('comments.html', comments=comments)

@app.route('/submit', methods=['POST'])
def submit_comment():
    comment = request.form['comment']
    comments.append(comment)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
