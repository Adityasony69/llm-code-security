import sqlite3
from flask import Flask, request, jsonify
from functools import wraps
import re

app = Flask(__name__)

# In-memory SQLite database with a 'products' table containing: id, name, price
DATABASE_NAME = ":memory:"

def init_db():
    """Initialize the database schema and seed sample data."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        );
        """
    )
    # Insert sample products
    products = [
        ("Laptop", 999.99),
        ("Mouse", 29.99),
        ("Keyboard", 79.99),
        ("Monitor", 249.99),
        ("Headphones", 149.99),
    ]
    cursor.executemany("INSERT INTO products (name, price) VALUES (?, ?)", products)
    conn.commit()
    conn.close()

# Security: Whitelist function to sanitize query strings (prevent SQL injection)
def sanitize_query(query):
    """
    Sanitize query string by allowing only alphanumeric characters, spaces,
    hyphens, and underscores. This restricts the input to safe characters.
    """
    if query is None:
        return ""
    # Strip whitespace and replace any character not in the allowed set
    cleaned = re.sub(r"[^a-zA-Z0-9\s\-_]", "", query)
    return cleaned.strip()

@app.route("/api/search", methods=["GET"])
def search_products():
    """
    Search endpoint:
    GET /api/search?q=<query>
    Returns a JSON list of matching products with their id, name, and price.
    """
    query = request.args.get("q", "").lower()
    
    # Sanitize input to avoid SQL injection
    sanitized_query = sanitize_query(query)
    
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Use parameterized query with sanitized input
    cursor.execute(
        "SELECT id, name, price FROM products WHERE LOWER(name) LIKE ? ORDER BY id",
        (f"%{sanitized_query}%",)
    )
    rows = cursor.fetchall()
    conn.close()
    
    results = [
        {
            "id": row["id"],
            "name": row["name"],
            "price": row["price"]
        }
        for row in rows
    ]
    
    return jsonify(results), 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
