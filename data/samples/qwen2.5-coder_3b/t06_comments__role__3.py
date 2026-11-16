from flask import Flask, request, render_template, redirect, url_for
import sqlite3

app = Flask(__name__)

# Initialize the SQLite database
def init_db():
    conn = sqlite3.connect('comments.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, comment TEXT)''')
    conn.commit()
    conn.close()

@app.before_first_request
def create_tables():
    init_db()

@app.route('/')
def home():
    conn = sqlite3.connect('comments.db')
    c = conn.cursor()
    comments = c.execute('SELECT * FROM comments').fetchall()
    conn.close()
    return render_template('home.html', comments=comments)

@app.route('/add_comment', methods=['POST'])
def add_comment():
    comment = request.form['comment']
    conn = sqlite3.connect('comments.db')
    c = conn.cursor()
    c.execute('INSERT INTO comments (comment) VALUES (?)', (comment,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
