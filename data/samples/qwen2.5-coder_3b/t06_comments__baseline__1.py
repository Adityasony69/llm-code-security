from flask import Flask, request, render_template_string

app = Flask(__name__)

# Initialize an empty list to store comments
comments = []

@app.route('/')
def comments_page():
    # Render the comments page with the comments list
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comments Page</title>
        </head>
        <body>
            <h1>Comments</h1>
            <ul>
                {% for comment in comments %}
                    <li>{{ comment }}</li>
                {% endfor %}
            </ul>
            <form method="post">
                <input type="text" name="comment" placeholder="Enter your comment">
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
    ''', comments=comments)

@app.route('/submit', methods=['POST'])
def submit_comment():
    # Get the comment from the form
    comment = request.form['comment']
    
    # Add the comment to the list
    comments.append(comment)
    
    # Redirect back to the comments page
    return comments_page()

if __name__ == '__main__':
    app.run(debug=True)
