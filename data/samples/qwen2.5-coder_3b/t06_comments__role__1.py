from flask import Flask, request, render_template_string
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)  # Generate a secret key for CSRF protection

comments = []

def sanitize_comment(comment):
    # Basic sanitization to prevent XSS attacks
    return comment.replace('<', '&lt;').replace('>', '&gt;')

@app.route('/', methods=['GET', 'POST'])
def comments_page():
    if request.method == 'POST':
        comment = request.form.get('comment')
        if comment:
            sanitized_comment = sanitize_comment(comment)
            comments.append(sanitized_comment)
            return redirect('/')
        else:
            return "Comment cannot be empty", 400

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
                <textarea name="comment" rows="4" cols="50"></textarea><br>
                <input type="submit" value="Submit Comment">
            </form>
            <h2>Comments</h2>
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
