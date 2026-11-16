from flask import Flask, request, render_template_string, session
import secrets
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

# Simple in-memory storage (in production, use a proper database)
comments = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Comments</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 40px auto; }
        form { display: flex; gap: 10px; margin-bottom: 20px; }
        input, textarea { padding: 8px; font-size: 14px; }
        button { padding: 8px 16px; cursor: pointer; }
        .comment { border: 1px solid #ddd; padding: 12px; margin-bottom: 10px; border-radius: 4px; }
        .comment-meta { font-size: 0.85em; color: #666; }
        .comment-body { margin-top: 4px; }
    </style>
</head>
<body>
    <h1>Comments</h1>
    <form method="post" action="/comments">
        <input type="text" name="name" placeholder="Your name" required>
        <textarea name="text" placeholder="Your comment" required></textarea>
        <button type="submit">Post</button>
    </form>
    <hr>
    <h2>Recent Comments</h2>
    {% for comment in comments %}
    <div class="comment">
        <div class="comment-meta">
            <strong>{{ comment['name'] }}</strong> wrote:
            <small>on {{ comment['timestamp'] }}</small>
        </div>
        <div class="comment-body">
            {{ comment['text'] }}
        </div>
    </div>
    {% endfor %}
</body>
</html>
"""

@app.route("/comments", methods=["GET", "POST"])
def comments_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        text = request.form.get("text", "").strip()
        if not name or not text:
            return render_template_string(HTML_TEMPLATE, comments=comments), 400
        comment = {
            "name": name,
            "text": text,
            "timestamp": request.args.get("timestamp", "now")
        }
        comments.append(comment)
    return render_template_string(HTML_TEMPLATE, comments=comments)

if __name__ == "__main__":
    app.run(debug=True)
