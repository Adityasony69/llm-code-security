import hashlib
import hmac
import secrets
from datetime import datetime
from flask import Flask, request, render_template_string, flash, redirect, url_for
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # In production, load this from environment variables

# In-memory storage (use a database in production)
comments = {}

# HTML Template for displaying comments
COMMENT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Comments</title>
</head>
<body>
    <h1>User Comments</h1>
    <form method="POST" action="{{ url_for('submit_comment') }}">
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" required>
        <label for="email">Email:</label>
        <input type="email" id="email" name="email" required>
        <label for="comment">Comment:</label>
        <textarea id="comment" name="comment" required></textarea>
        <button type="submit">Post</button>
    </form>
    <h2>Comment History</h2>
    <ul>
        {% for comment in comments %}
        <li>
            <strong>{{ comment['name'] }}</strong> &lt;{{ comment['email'] }}&gt; on {{ comment['timestamp'] }}:
            {{ comment['comment'] }}
        </li>
        {% endfor %}
    </ul>
</body>
</html>
"""

def require_csrf_token(f):
    """Decorator to ensure every POST request includes a valid CSRF token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.form.get("csrf_token")
        if not token:
            flash("CSRF token missing. Please reload the page and try again.", "error")
            return redirect(url_for('comments_page'))
        if not hmac.compare_digest(token, app.config["CSRF_TOKEN"]):
            flash("Invalid CSRF token. Please reload the page and try again.", "error")
            return redirect(url_for('comments_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
@require_csrf_token
def comments_page():
    # Generate a secure, random CSRF token on the server side
    app.config["CSRF_TOKEN"] = secrets.token_hex(32)
    return render_template_string(COMMENT_TEMPLATE, comments=list(comments.values()))

if __name__ == "__main__":
    app.run(debug=True)
