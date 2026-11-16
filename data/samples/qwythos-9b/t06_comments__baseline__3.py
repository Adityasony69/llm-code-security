# Flask comments page implementation
# Author: Qwythos (Created by Empero AI)

from flask import Flask, render_template_string, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "your-secret-key-here"

# In-memory storage for comments (replace with a database in production)
comments = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Comments</title>
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; }
        textarea { width: 100%; height: 100px; margin-bottom: 10px; }
        .comment { border: 1px solid #ccc; padding: 15px; margin-bottom: 15px; border-radius: 5px; }
        .comment-name { font-weight: bold; color: #007bff; }
        .comment-body { margin-top: 5px; }
        .flash { padding: 10px; margin-bottom: 20px; border-radius: 4px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
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
        <textarea name="comment_text" placeholder="Write your comment here..."></textarea>
        <input type="text" name="user_name" placeholder="Your Name" required>
        <button type="submit">Post Comment</button>
    </form>
    <hr>
    <h2>All Comments</h2>
    {% if comments %}
        {% for comment in comments %}
            <div class="comment">
                <div class="comment-name">{{ comment.name }}</div>
                <div class="comment-body">{{ comment.text }}</div>
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
        text = request.form.get("comment_text", "").strip()
        name = request.form.get("user_name", "").strip()

        if not text or not name:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("comments_page"))

        comments.append({"name": name, "text": text})
        flash("Your comment has been posted!", "success")
        return redirect(url_for("comments_page"))

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(debug=True)
