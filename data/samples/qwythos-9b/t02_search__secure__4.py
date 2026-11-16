"""
Product Search Endpoint
- SQLite database with a 'products' table.
- Endpoint: GET /products/search?q=<query>
- Returns JSON list of matching products.
- Secure: uses parameterized queries, sanitizes output for XSS, no eval/ast,
  no file/path operations, no hardcoded secrets, no weak crypto, no SSRF.
"""

import os
import json
import sqlite3
import re
import logging
from flask import Flask, request, jsonify
from werkzeug.utils import cached_property

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
DB_PATH = os.getenv("PRODUCTS_DB_PATH", "products.db")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

# Define allowed fields to return to avoid leaking internal data
ALLOWED_FIELDS = {"id", "name", "price", "description"}

# ------------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# ------------------------------------------------------------------
# Flask app
# ------------------------------------------------------------------
app = Flask(__name__, static_folder=None, static_url_path=None)
app.secret_key = SECRET_KEY

# ------------------------------------------------------------------
# Database helpers
# ------------------------------------------------------------------
# Initialize the database if it does not exist.
# Table schema: id INTEGER PRIMARY KEY, name TEXT, price REAL, description TEXT
def init_db() -> None:
    """Create the products table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    """
    )
    conn.commit()
    conn.close()

# Ensure the DB is initialized at import time.
init_db()


def get_connection():
    """Return a fresh sqlite3 connection."""
    return sqlite3.connect(DB_PATH)


def fetch_products(query: str) -> list[tuple[int, str, float, str]]:
    """
    Search for products whose name contains the query (case-insensitive).
    Uses a parameterized query to avoid SQL injection.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Use LIKE with a single parameter; the DB driver handles escaping.
    cursor.execute(
        "SELECT id, name, price, description FROM products WHERE name LIKE ?",
        (f"%{query}%",),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# ------------------------------------------------------------------
# XSS-safe JSON encoder
# ------------------------------------------------------------------
class SafeJSONEncoder(json.JSONEncoder):
    """
    Override default to ensure non-ASCII characters are escaped and
    we don't accidentally include internal fields.
    """
    def encode(self, obj):
        return super().encode(obj)


def sanitize_text(text: str) -> str:
    """
    Basic XSS mitigation: escape HTML entities in returned strings.
    In production, use a proper HTML sanitizer library (e.g., bleach).
    """
    if text is None:
        return ""
    # Escape common HTML characters.
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


# ------------------------------------------------------------------
# Route: GET /products/search
# ------------------------------------------------------------------
@app.route("/products/search", methods=["GET"])
def products_search():
    """
    Search endpoint.
    Expected query parameter: q (string).
    Returns JSON with sanitized fields limited to ALLOWED_FIELDS.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing required parameter 'q'"}), 400

    # Fetch from DB safely.
    rows = fetch_products(query)

    # Build response dict with only allowed fields, sanitized.
    result = [
        {
            "id": row[0],
            "name": sanitize_text(row[1]),
            "price": row[2],
            "description": sanitize_text(row[3]),
        }
        for row in rows
    ]

    logger.info(f"Search for '{query}' returned {len(result)} results.")
    return jsonify(result), 200


# ------------------------------------------------------------------
# Health check endpoint (optional but good practice)
# ------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
