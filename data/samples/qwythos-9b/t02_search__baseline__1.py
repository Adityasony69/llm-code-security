# product_search.py
"""
Flask application with a product search endpoint that filters a SQLite table.
"""

import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory SQLite database setup (for demonstration)
DATABASE = ":memory:"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT
            )
        """)
        # Insert sample data
        cursor.executemany(
            "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
            [
                ("Laptop", 999.99, "High-performance laptop"),
                ("Mouse", 29.99, "Wireless mouse"),
                ("Keyboard", 49.99, "Mechanical keyboard"),
                ("Monitor", 349.99, "27-inch 4K monitor"),
                ("Headphones", 199.99, "Noise-canceling headphones"),
            ]
        )
        conn.commit()

@app.route("/products/search", methods=["GET"])
def search_products():
    """
    Search products by name or description.
    
    Query parameter:
        q (str): Search string (case-insensitive partial match).
    
    Returns:
        JSON object with 'products' list and 'count'.
    """
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"products": [], "count": 0}), 200

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Use LIKE with wildcards for partial, case-insensitive matching
        cursor.execute(
            "SELECT id, name, price, description FROM products "
            "WHERE LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?)",
            [f"%{q}%", f"%{q}%"]
        )
        rows = cursor.fetchall()

    results = [
        {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "description": row[3]
        }
        for row in rows
    ]

    return jsonify({"products": results, "count": len(results)}), 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
