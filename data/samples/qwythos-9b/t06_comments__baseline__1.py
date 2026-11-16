import os
from flask import Flask, render_template_string, request, flash, redirect, url_for
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

# In-memory storage (replace with a real DB in production)
comments = []

# HTML template for the comments page
COMMENTS_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Comments</title>
    <style>
        body { font-family: sans-serif; margin: 2rem; }
        .comment { border: 1px solid #ccc; padding: 1rem; margin-bottom: 1rem; border-radius: 4px; }
        .comment .meta { color: #666; font-size: 0.9rem; margin-bottom: 0.5rem; }
        .comment .text { white-space: pre-wrap; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.25rem; font-weight: bold; }
        input[type="text"], textarea { width: 100%; padding: 0.5rem; box-sizing: border-box; }
        button { background: #007bff; color: #fff; border: none; padding: 0.5rem 1rem; cursor: pointer; border-radius: 4px; }
        button:hover { background: #0056b3; }
        .flash { padding: 0.5rem; border-radius: 4px; margin-bottom: 1rem; }
        .flash.error { background: #f8d7da; color: #721c24; }
        .flash.success { background: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <h1>Comments</h1>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="flash {{ category }}">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    <form method="POST">
      <div class="form-group">
        <label for="name">Name</label>
        <input type="text" id="name" name="name" required>
      </div>
      <div class="form-group">
        <label for="text">Comment</label>
        <textarea id="text" name="text" rows="4" required></textarea>
      </div>
      <button type="submit">Submit</button>
    </form>
    <hr>
    <h2>Submitted Comments</h2>
    {% if comments %}
      {% for comment in comments %}
        <div class="comment">
          <div class="meta"><strong>{{ comment.name }}</strong> – {{ comment.timestamp.strftime("%Y-%m-%d %H:%M") }}</div>
          <div class="text">{{ comment.text }}</div>
        </div>
      {% endfor %}
    {% else %}
      <p>No comments yet.</p>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def comments_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        text = request.form.get("text", "").strip()
        if not name or not text:
            flash("Please provide both a name and a comment.", "error")
            return render_template_string(COMMENTS_PAGE_TEMPLATE)

        comments.append({
            "name": name,
            "text": text,
            "timestamp": datetime.datetime.now(datetime.timezone.utc)
        })
        flash("Your comment has been submitted!", "success")

    return render_template_string(COMMENTS_PAGE_TEMPLATE)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
