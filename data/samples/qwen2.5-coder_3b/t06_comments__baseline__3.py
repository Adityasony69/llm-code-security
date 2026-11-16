from flask import Flask, request, render_template_string

app = Flask(__name__)

# List to store comments
comments = []

@app.route('/', methods=['GET', 'POST'])
def comments_page():
    if request.method == 'POST':
        comment = request.form.get('comment')
        if comment:
            comments.append(comment)
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
                <input type="text" name="comment" placeholder="Enter your comment">
                <button type="submit">Submit</button>
            </form>
            <ul>
                {% for comment in comments %}
                    <li>{{ comment }}</li>
                {% endfor %}
            </ul>
        </body>
        </html>
    ''', comments=comments)

if __name__ == '__main__':
    app.run(debug=True)
