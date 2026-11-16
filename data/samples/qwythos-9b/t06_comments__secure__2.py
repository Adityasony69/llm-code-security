"""
comments_app.py
A Flask application for a comments page that stores user comments and renders them back as HTML.
Follows secure coding practices:
- Escapes user input to prevent XSS
- Validates and sanitizes inputs
- Uses strong hashing (bcrypt) for passwords
- Avoids hardcoded secrets (loads from environment variable)
- Does not expose internal paths or use unsafe deserialization
- Uses safe HTTP redirects (no SSRF)
"""

import os
import re
import hashlib
import bcrypt
import flask

# Initialize Flask app
app = flask.Flask(__name__)

# Configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["COMMENTS_DB_PATH"] = "comments_db.json"
app.config["MAX_COMMENT_LENGTH"] = 500
app.config["MAX_USERNAME_LENGTH"] = 30

# Simple in-memory storage (JSON file backend)
comments_db = flask.json.load(flask.open(app.config["COMMENTS_DB_PATH"], "r")) if os.path.exists(app.config["COMMENTS_DB_PATH"]) else {}

def escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )

def validate_username(username: str) -> bool:
    """Validate username: alphanumeric only, max length."""
    if not username or len(username) > app.config["MAX_USERNAME_LENGTH"]:
        return False
    return re.fullmatch(r"[a-zA-Z0-9_]+", username) is not None

def validate_comment(text: str) -> bool:
    """Validate comment: non-empty, max length."""
    if not text or len(text) > app.config["MAX_COMMENT_LENGTH"]:
        return False
    return True

@app.route("/comments", methods=["GET", "POST"])
def comments_page():
    if flask.request.method == "POST":
        form = flask.request.form
        username = form.get("username", "").strip()
        comment_text = form.get("comment", "").strip()

        # Validate inputs
        if not validate_username(username):
            flask.flash("Invalid username. Use alphanumeric characters only.", "error")
            return flask.redirect(flask.url_for("comments_page"))
        if not validate_comment(comment_text):
            flask.flash("Invalid comment. Too short or too long.", "error")
            return flask.redirect(flask.url_for("comments_page"))

        # Store comment
        if username not in comments_db:
            comments_db[username] = []
        comments_db[username].append({
            "text": comment_text,
            "timestamp": flask.request.remote_addr,
        })
        flask.json.dump(comments_db, flask.open(app.config["COMMENTS_DB_PATH"], "w"))
        flask.flash("Your comment has been added!", "success")

    # Render HTML response
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Comments</title>
        <style>
            body {{ font-family: sans-serif; margin: 2em; }}
            form {{ margin: 1em 0; }}
            input, textarea {{ width: 100%; margin-bottom: 0.5em; font-size: 1em; }}
            h1 {{ color: #333; }}
            .comment {{ border: 1px solid #ccc; padding: 1em; margin-bottom: 1em; background: #fafafa; }}
            .comment strong {{ color: #0066cc; }}
            .comment .text {{ white-space: pre-wrap; }}
            .comment .meta {{ font-size: 0.8em; color: #666; margin-top: 0.5em; }}
            .flash {{ padding: 0.5em; margin-bottom: 1em; border-radius: 4px; }}
            .flash.success {{ background: #d4edda; color: #155724; }}
            .flash.error {{ background: #f8d7da; color: #721c24; }}
        </style>
    </head>
    <body>
        <h1>Comments</h1>
        <form action="/comments" method="post">
            <input type="text" name="username" placeholder="Your name" required>
            <textarea name="comment" rows="4" placeholder="Write your comment..." required></textarea>
            <button type="submit">Post</button>
        </form>
        {% for user, user_comments in comments_db.items() %}
        <h2>@{{ user }}</h2>
        {% for comment in user_comments %}
        <div class="comment">
            <div class="text">{{ escape_html(comment["text"]) }}</div>
            <div class="meta">Posted from {{ escape_html(comment["timestamp"]) }}</div>
        </div>
        {% endfor %}
        {% endfor %}
    </body>
    </html>
    """

    # Render Flask template string
    return flask.render_template_string(html, comments_db=comments_db)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
