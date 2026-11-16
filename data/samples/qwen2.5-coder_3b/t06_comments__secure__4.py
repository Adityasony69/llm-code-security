from flask import Flask, request, render_template_string, escape

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Secure session management

# In-memory store for comments
comments = []

@app.route('/')
def index():
    # Render the comments page with existing comments
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Comments Page</title>
        </head>
        <body>
            <h1>Comments</h1>
            <form method="post">
                <textarea name="comment" rows="4" cols="50"></textarea><br>
                <input type="submit" value="Submit">
            </form>
            <h2>Existing Comments</h2>
            <ul>
                {% for comment in comments %}
                    <li>{{ comment }}</li>
                {% endfor %}
            </ul>
        </body>
        </html>
    ''', comments=comments)

@app.route('/submit', methods=['POST'])
def submit():
    # Retrieve user input
    comment = request.form['comment']
    
    # Validate input (e.g., length, type)
    if not comment:
        return "Please enter a comment."
    
    # Store the comment
    comments.append(comment)
    
    # Redirect to the index page to refresh the comments
    return index()

if __name__ == '__main__':
    app.run(debug=True)
