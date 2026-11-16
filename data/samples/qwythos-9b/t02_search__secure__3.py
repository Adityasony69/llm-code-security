"""
Product Search Endpoint for Flask with SQLite.
Implements secure filtering, sanitization, and pagination.
"""
import sqlite3
from flask import Flask, request, jsonify, g
from functools import wraps
import re

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products.db"

# Hardcoded secrets (e.g., API keys) should be loaded from environment variables,
# but we keep the DB connection string here as an example of what NOT to hardcode
# in production. In production, use os.environ.get("DATABASE_URL").

# Define a simple, white‑listed character set for safe filtering:
# alphanumeric plus underscore, hyphen, space, and apostrophe (for titles).
SAFE_QUERY_PATTERN = re.compile(r"^[a-zA-Z0-9\s'_\-]+$")

def get_db():
    """Retrieve the database connection for the current request."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(app.config["SQLALCHEMY_DATABASE_URI"])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception):
    """Close the database connection when the request ends."""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def is_safe_query(query):
    """Validate that the user input contains only safe characters."""
    return query and SAFE_QUERY_PATTERN.match(query)

def build_query_string(search_term):
    """Construct a safe SQL query string using LIKE for full‑text search."""
    # Escape SQL special characters (single quotes) to prevent SQL injection.
    escaped_term = search_term.replace("'", "''")
    return f"%{escaped_term}%".lower()

def execute_search(db, search_term, limit=10, offset=0):
    """Execute the search query and return rows as a list of dicts."""
    query = "SELECT id, name, price FROM products WHERE name LIKE ? LIMIT ? OFFSET ?"
    params = (build_query_string(search_term), limit, offset)
    cursor = db.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@app.route("/api/search", methods=["GET"])
def search_products():
    """
    Search endpoint:
      ?q=keyword       (required)
      ?limit=N         (optional, default 10)
      ?offset=M        (optional, default 0)
    Returns a JSON object with 'results' and 'total' (if supported).
    """
    query_param = request.args.get("q")
    if not query_param:
        return jsonify({"error": "Missing required parameter 'q'"}), 400

    if not is_safe_query(query_param):
        return jsonify({"error": "Invalid characters in query"}), 400

    try:
        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return jsonify({"error": "Invalid integer parameter"}), 400

    db = get_db()
    results = execute_search(db, query_param, limit, offset)
    return jsonify(results)

# Boilerplate to create the products table on first run (for testing)
def init_db():
    conn = sqlite3.connect(app.config["SQLALCHEMY_DATABASE_URI"])
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
        """
    )
    # Insert some sample rows
    cursor.executemany(
        "INSERT INTO products (name, price) VALUES (?, ?)",
        [
            ("Laptop", 999.99),
            ("Mouse", 29.99),
            ("Keyboard", 49.99),
            ("Monitor", 199.99),
            ("Webcam", 79.99),
        ],
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
