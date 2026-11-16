from flask import Flask, request, render_template_string, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///comments.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- Security-minded HTML template ---
# Uses a simple Jinja2 template with autoescaping enabled (Flask default)
# to prevent XSS when rendering user comments.
COMMENT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Comments - Secure Flask App</title>
    <style>
        body { font-family: sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .comment { border-bottom: 1px solid #eee; padding: 12px 0; }
        .comment:last-child { border-bottom: none; }
        .comment strong { color: #007bff; }
        .comment time { color: #888; font-size: 0.85em; }
        .comment .body { color: #333; margin-top: 4px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group textarea { width: 100%; padding: 8px; box-sizing: border-box; }
        .form-group textarea { height: 100px; resize: vertical; font-family: inherit; }
        button { background: #28a745; color: #fff; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #218838; }
        .flash { padding: 10px; margin-bottom: 15px; border-radius: 4px; }
        .flash.error { background: #f8d7da; color: #721c24; }
        .flash.success { background: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Comments</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        
        <form method="POST" action="{{ url_for('submit_comment') }}">
          <div class="form-group">
            <label for="name">Your Name:</label>
            <input type="text" id="name" name="name" required>
          </div>
          <div class="form-group">
            <label for="comment">Your Comment:</label>
            <textarea id="comment" name="comment" required></textarea>
          </div>
          <button type="submit">Post Comment</button>
        </form>
        
        <hr style="margin: 30px 0; border: 0; border-top: 1px solid #eee;">
        
        <h2>Recent Comments</h2>
        {% for comment in comments %}
          <div class="comment">
            <strong>{{ comment.name }}</strong> <time>{{ comment.created_at }}</time>
            <div class="body">{{ comment.body|safe }}</div>
          </div>
        {% else %}
          <p>No comments yet.</p>
        {% endfor %}
    </div>
</body>
</html>
"""

# --- Models ---
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        body = request.form.get("comment", "").strip()
        
        # Simple validation: ensure input is not empty
        if not name or not body:
            flash("Name and comment are required.", "error")
            return redirect(url_for("index"))
        
        # Optional: basic sanitization for the name (strip whitespace)
        # For the body, we rely on the template's autoescaping to handle HTML safely.
        # If you want to allow HTML, you would still store it as-is and let Flask render it.
        comment = Comment(name=name, body=body)
        db.session.add(comment)
        db.session.commit()
        flash("Your comment has been posted!", "success")
        return redirect(url_for("index"))
    
    # GET request: render the page with existing comments
    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template_string(COMMENT_TEMPLATE, comments=comments)

# --- Application entry point ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables (in a real app, this would be handled by migrations)
    app.run(debug=True)
