from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "flask-comments-secret-key")
DB_PATH = "comments.db"

# Simple in-memory storage of user emails for demo (in production use proper auth)
registered_emails = set()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return redirect(url_for("comments_page"))

@app.route("/comments", methods=["GET", "POST"])
def comments_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        comment = request.form.get("comment", "").strip()

        if not name or not email or not comment:
            flash("All fields are required.", "error")
            return redirect(url_for("comments_page"))

        # Simple registration check (replace with proper auth in production)
        if email not in registered_emails:
            flash("You are not registered. Please register first.", "error")
            return redirect(url_for("comments_page"))

        # Store comment
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO comments (name, email, comment) VALUES (?, ?, ?)",
            (name, email, comment),
        )
        conn.commit()
        conn.close()

        flash("Thank you for your comment!", "success")
        return redirect(url_for("comments_page"))

    # Retrieve comments ordered newest first
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    comments = conn.execute("SELECT * FROM comments ORDER BY created_at DESC").fetchall()
    conn.close()

    return render_template(
        "comments.html",
        comments=comments,
        registered_emails=registered_emails,
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Email is required.", "error")
            return redirect(url_for("register"))
        registered_emails.add(email)
        flash("Registration successful!", "success")
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)
