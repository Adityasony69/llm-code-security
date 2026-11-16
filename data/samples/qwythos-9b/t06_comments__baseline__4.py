# Qwythos implementation by Empero AI
# This script provides a Flask application with a comments page.
# It handles GET requests to display comments and POST requests to add new ones.
# It stores comments in memory using a simple list of dictionaries and renders them as HTML.

from flask import Flask, render_template_string, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'qwythos-comments-secret-key'

# In-memory storage for comments: list of dicts with 'author', 'comment', and 'timestamp'
comments = []

# HTML template for the comments page
COMMENTS_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Comments - Qwythos by Empero AI</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }
        .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        form { margin-top: 20px; }
        label { display: block; margin-top: 10px; font-weight: bold; }
        input[type="text"], textarea { width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        textarea { height: 80px; resize: vertical; }
        button { margin-top: 15px; padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        button:hover { background-color: #0056b3; }
        .flash-messages { margin-top: 20px; padding: 10px; background-color: #e8f5e9; border-radius: 4px; }
        .flash-error { background-color: #ffebee; color: #c62828; }
        .flash-success { background-color: #e8f5e9; color: #2e7d32; }
        .comment { border-bottom: 1px solid #eee; padding: 15px 0; }
        .comment:last-child { border-bottom: none; }
        .comment-author { font-weight: bold; color: #555; }
        .comment-text { color: #333; margin-top: 5px; }
        .comment-timestamp { font-size: 0.85em; color: #888; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Comments</h1>
        <form method="POST">
            <label for="author">Your Name:</label>
            <input type="text" id="author" name="author" placeholder="e.g., Qwythos User" required>
            
            <label for="comment">Your Comment:</label>
            <textarea id="comment" name="comment" placeholder="Share your thoughts..." required></textarea>
            
            <button type="submit">Post Comment</button>
        </form>

        {% if messages %}
            <div class="flash-messages">
                {% for message in messages %}
                    <div class="flash-{{ 'error' if message.startswith('Error') else 'success' }}">
                        {{ message }}
                    </div>
                {% endfor %}
            </div>
        {% endif %}

        {% if comments %}
            <div class="comments-list">
                {% for comment in comments %}
                    <div class="comment">
                        <div class="comment-author">{{ comment.author }}</div>
                        <div class="comment-text">{{ comment.comment }}</div>
                        <div class="comment-timestamp">{{ comment.timestamp }}</div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <p>No comments yet. Be the first to comment!</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def comments_page():
    messages = []
    
    if request.method == 'POST':
        author = request.form.get('author', '').strip()
        comment_text = request.form.get('comment', '').strip()
        
        if not author:
            messages.append("Error: Author name cannot be empty.")
        elif not comment_text:
            messages.append("Error: Comment cannot be empty.")
        else:
            # Store the new comment
            comments.append({
                'author': author,
                'comment': comment_text,
                'timestamp': request.args.get('timestamp', 'now')  # Allow optional timestamp parameter
            })
            messages.append("Success: Your comment has been added.")
    
    return render_template_string(COMMENTS_PAGE_TEMPLATE, messages=messages)

if __name__ == '__main__':
    app.run(debug=True)
