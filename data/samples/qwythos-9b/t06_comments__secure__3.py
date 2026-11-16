"""
comments_page.py

A secure Flask application for managing user comments.
Stores comments in a simple in-memory dictionary (persisted to disk as JSON).
Serves a simple HTML form to add comments and a page to view them.
"""

import json
import os
import secrets
import string
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
app.session_cookie_name = "session"

COMMENT_PATH = Path(__file__).parent / "comments.json"


def load_comments():
    if COMMENT_PATH.exists():
        with COMMENT_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_comments(comments):
    with COMMENT_PATH.open("w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        comment = request.form.get("comment", "").strip()

        if not name or not comment:
            return render_template_string(
                "<!DOCTYPE html>\n<html>\n<head><title>Comments</title></head>\n<body>\n"
                "<h1>Comments</h1>\n"
                "<p style='color:red;'>Please fill in both fields.</p>\n"
                "<form method='POST'>\n"
                "<label>Name: <input name='name' value='{name}' required></label>\n"
                "<label>Comment: <textarea name='comment' required></textarea></label>\n"
                "<button type='submit'>Post</button>\n"
                "</form>\n"
                "<hr>\n"
                "<h2>All Comments</h2>\n"
                "<ul>\n"
                "%s\n"
                "</ul>\n"
                "</body>\n</html>",
                name=name,
                comments_html="\n".join(
                    f"<li><strong>{escape(name)}</strong> — {escape(comment)}</li>"
                    for name, comment in sorted(comments.items(), key=lambda x: x[1])
                ),
            )

        comments = load_comments()
        comments[name] = comment
        save_comments(comments)
        return redirect(url_for("index"))

    comments = load_comments()
    return render_template_string(
        "<!DOCTYPE html>\n<html>\n<head><title>Comments</title></head>\n<body>\n"
        "<h1>Comments</h1>\n"
        "<form method='POST'>\n"
        "<label>Name: <input name='name' value='{name}' required></label>\n"
        "<label>Comment: <textarea name='comment' required></textarea></label>\n"
        "<button type='submit'>Post</button>\n"
        "</form>\n"
        "<hr>\n"
        "<h2>All Comments</h2>\n"
        "<ul>\n"
        "%s\n"
        "</ul>\n"
        "</body>\n</html>",
        name=request.args.get("name", ""),
        comments_html="\n".join(
            f"<li><strong>{escape(name)}</strong> — {escape(comment)}</li>"
            for name, comment in sorted(comments.items(), key=lambda x: x[1])
        ),
    )


def escape(text):
    """Simple XSS-safe HTML escaping."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


@app.route("/api/comments", methods=["GET"])
def api_comments():
    comments = load_comments()
    return jsonify(comments)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
