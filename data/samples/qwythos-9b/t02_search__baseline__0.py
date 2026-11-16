# Flask product search endpoint with SQLite filtering
# Requires: flask, sqlite3 (standard library)
# Usage: python app.py then visit http://localhost:5000/api/search?q=query_string

from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Initialize the database and create the products table if it doesn't exist
DATABASE = "products.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            category TEXT
        )
    """)
    # Insert some dummy data for demonstration
    cursor.executemany("""
        INSERT INTO products (name, price, description, category) VALUES (?, ?, ?, ?)
    """, [
        ("Laptop", 999.99, "High performance laptop", "Electronics"),
        ("Coffee", 12.50, "Freshly roasted coffee beans", "Food"),
        ("Desk", 150.00, "Wooden computer desk", "Furniture"),
        ("Mouse", 25.00, "Wireless mouse", "Electronics"),
        ("Keyboard", 60.00, "Mechanical keyboard", "Electronics"),
        ("Tea", 5.00, "Green tea bag", "Food"),
        ("Chair", 80.00, "Ergonomic office chair", "Furniture"),
        ("Monitor", 299.99, "27-inch monitor", "Electronics")
    ])
    conn.commit()
    conn.close()

# Ensure the database is initialized on startup
init_db()

@app.route("/api/search", methods=["GET"])
def search_products():
    """
    Search products by a query string parameter.
    The query is converted to lowercase and matched against name, description, and category.
    Returns a JSON list of matching products with their IDs.
    """
    query = request.args.get("q", "").lower()
    if not query:
        return jsonify([]), 200

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Use LIKE with wildcards for a flexible search
    cursor.execute("""
        SELECT id, name, price, description, category
        FROM products
        WHERE LOWER(name) LIKE ?
           OR LOWER(description) LIKE ?
           OR LOWER(category) LIKE ?
    """,
        (f"%{query}%", f"%{query}%", f"%{query}%")
    )
    rows = cursor.fetchall()
    conn.close()

    # Convert sqlite3.Row objects to dictionaries
    results = [dict(row) for row in rows]
    return jsonify(results), 200

if __name__ == "__main__":
    app.run(debug=True)
