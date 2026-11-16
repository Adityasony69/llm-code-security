"""
secure_search.py - A secure Flask product search endpoint for SQLite.
Specialises in application security (SQL Injection prevention, sanitization,
logging, and input validation).

Author: Qwythos (Empero AI)
"""

import logging
from typing import List, Dict, Any, Optional

from flask import Flask, request, jsonify, g
import sqlite3

# Configure logging for security events
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("secure_search")

app = Flask(__name__)

# In-memory SQLite database (use a real file in production)
DATABASE = ":memory:"

# Initialize the database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL,
                category TEXT
            )
        """)
        # Insert sample data
        sample_products = [
            ("Laptop", "High-performance laptop", 999.99, "Electronics"),
            ("Coffee Maker", "Automatic coffee maker", 49.99, "Appliances"),
            ("Running Shoes", "Durable running shoes", 79.99, "Sports"),
            ("Smartphone", "Latest model smartphone", 699.99, "Electronics"),
            ("Desk Chair", "Ergonomic desk chair", 149.99, "Furniture"),
        ]
        cursor.executemany(
            "INSERT INTO products (name, description, price, category) VALUES (?, ?, ?, ?)",
            sample_products
        )
        conn.commit()
    logger.info("Database initialized with sample products.")

# Global cache for the database connection
db_connection: Optional[sqlite3.Connection] = None

def get_db() -> sqlite3.Connection:
    """Get or create the database connection."""
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(DATABASE)
        db_connection.row_factory = sqlite3.Row
    return db_connection

@app.before_request
def before_request():
    """Ensure the DB connection exists before handling requests."""
    get_db()

@app.route("/api/search", methods=["GET"])
def product_search():
    """
    Search endpoint:
    GET /api/search?q=<query_string>

    Security considerations implemented:
    - Input validation: ensures 'q' is a non-empty string.
    - SQL Injection prevention: uses parameterized queries.
    - Logging: logs suspicious queries (e.g., containing SQL keywords).
    - Response: returns JSON with filtered products.
    """
    # Retrieve and clean the query parameter
    q = request.args.get("q", "").strip()
    if not q:
        logger.info("No query parameter provided.")
        return jsonify({"error": "Missing 'q' parameter."}), 400

    # Basic validation: ensure it's a string
    if not isinstance(q, str):
        logger.warning(f"Query parameter 'q' is not a string: {q!r}")
        return jsonify({"error": "Invalid query parameter type."}), 400

    # Optional: log queries that look like SQL injection attempts
    sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "--", "/*", "*/", "'", '"']
    for kw in sql_keywords:
        if kw.upper() in q.upper():
            logger.warning(f"Potential SQL injection attempt detected: {q!r}")

    # Secure query using parameterized statements
    cursor = get_db().cursor()
    query = """
        SELECT id, name, description, price, category
        FROM products
        WHERE name LIKE ? ESCAPE '\\'
    """
    # Use the '%' wildcards correctly; we pass the pattern as a single parameter
    cursor.execute(query, (f"%{q}%",))
    rows = cursor.fetchall()
    logger.info(f"Executed search query for '{q}' -> {len(rows)} results.")

    # Build a safe response
    results = [dict(row) for row in rows]
    return jsonify({"query": q, "results": results}), 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
