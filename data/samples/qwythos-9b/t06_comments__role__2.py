import os
import re
from flask import Flask, render_template_string, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from markupsafe import escape

# Application factory setup for clarity
def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # In-memory storage for demo purposes (use a DB in production)
    # Structure: { comment_id: { 'author': ..., 'text': ..., 'created_at': ... } }
    comments_store = {}
    next_id = 1

    # Simple HTML template for the comments page
    # We will inject sanitized text here.
    COMMENTS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Comments</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        .comment { margin-bottom: 1.5rem; padding: 1rem; border: 1px solid #eee; border-radius: 8px; background: #fafafa; }
        .comment-author { font-weight: bold; color: #333; }
        .comment-text { margin-top: 0.5rem; line-height: 1.5; }
        .error { color: #d32f2f; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
        input[type="text"] { width: 100%; padding: 0.5rem; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>Community Comments</h1>
    
    <form method="POST" action="{{ url_for('submit_comment') }}">
        <div class="form-group">
            <label for="author">Your Name:</label>
            <input type="text" id="author" name="author" required maxlength="50">
        </div>
        <div class="form-group">
            <label for="text">Comment:</label>
            <textarea id="text" name="text" required maxlength="500"></textarea>
        </div>
        <button type="submit">Post Comment</button>
    </form>

    <h2>Comments</h2>
    {% if comments %}
        {% for comment in comments %}
            <div class="comment">
                <div class="comment-author">{{ comment.author }}</div>
                <div class="comment-text">{{ comment.text }}</div>
            </div>
        {% endfor %}
    {% else %}
        <p>No comments yet. Be the first to share your thoughts!</p>
    {% endif %}
</body>
</html>
    """

    @app.route('/', methods=['GET', 'POST'])
    def index():
        global comments_store, next_id
        
        if request.method == 'POST':
            author = request.form.get('author', '').strip()
            text = request.form.get('text', '').strip()
            
            if not author or not text:
                flash('Please fill in both fields.', 'error')
                return redirect(url_for('index'))
            
            # Basic sanitization: escape HTML to prevent XSS
            safe_author = escape(author)
            safe_text = escape(text)
            
            comment = {
                'author': safe_author,
                'text': safe_text,
                'created_at': next_id  # Using ID as a simple timestamp proxy
            }
            
            comments_store[next_id] = comment
            next_id += 1
            
            # Re-render the page immediately so the new comment appears without a full page reload
            return render_template_string(COMMENTS_TEMPLATE, comments=list(comments_store.values()))
        
        # GET request: render with current comments
        return render_template_string(COMMENTS_TEMPLATE, comments=list(comments_store.values()))

    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Run on all interfaces for easy local testing
    app.run(host='0.0.0.0', port=5000, debug=True)
