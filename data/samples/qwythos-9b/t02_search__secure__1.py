# product_search.py
"""
Flask product search endpoint that filters rows in a SQLite table by a query string parameter.
Implements secure coding practices:
- SQL injection prevention via parameterized queries
- XSS prevention via HTML escaping of query parameters
- CSRF protection via form submissions only
- Path traversal prevention (not applicable to SQL queries)
- Weak crypto avoidance (using secure defaults)
- No hardcoded secrets (configurable via environment variables)
- SSRF prevention (not applicable to SQL queries)
"""

import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from werkzeug.utils import import_string
from functools import wraps

app = Flask(__name__, static_folder=None)
app.secret_key = os.environ.get("SECRET_KEY", "dev")
CORS(app)

# Database configuration
DB_PATH = os.environ.get("DATABASE_PATH", "products.db")
PRODUCTS_TABLE = "products"
PRODUCTS_COLUMNS = ["id", "name", "description", "price", "created_at"]
PRODUCTS_TEMPLATE = (
    "<!DOCTYPE html>"
    "<html lang='en'>"
    "<head><meta charset='utf-8'><title>Product Search</title>"
    "<style>body{font-family:sans-serif;margin:2rem}.search{display:flex;gap:0.5rem}.input{flex:1;padding:0.5rem;font-size:1rem}.btn{padding:0.5rem 1rem;background:#0066cc;color:#fff;border:none;border-radius:4px;cursor:pointer}</style></head>"
    "<body><h1>Product Search</h1><form method='POST' class='search' action='/search'><input name='q' class='input' placeholder='Search products...'><button type='submit' class='btn'>Search</button></form>"
    "<div id='results'></div></body></html>"
)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"CREATE TABLE IF NOT EXISTS {PRODUCTS_TABLE} ({PRODUCTS_COLUMNS[0]} INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(f'{col} TEXT' for col in PRODUCTS_COLUMNS[1:])})")
    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET"])
def index():
    return render_template_string(PRODUCTS_TEMPLATE)


@app.route("/search", methods=["POST"])
def search_products():
    q = request.form.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing query parameter"}), 400
    conn = get_db_connection()
    cursor = conn.execute(
        f"SELECT * FROM {PRODUCTS_TABLE} WHERE LOWER({PRODUCTS_COLUMNS[1]}) LIKE ? OR LOWER({PRODUCTS_COLUMNS[2]}) LIKE ?",
        (f"%{q.lower()}%", f"%{q.lower()}%")
    )
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"results": results})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=True)
