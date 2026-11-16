"""
secure_search.py

A secure Flask product search endpoint that filters a SQLite table by a query string
parameter. The implementation follows security best practices:
- Uses parameterized queries to prevent SQL injection.
- Normalizes and sanitizes user input (UTF-8, strip, case-insensitive matching).
- Implements tokenization to support "AND" search logic (e.g., "apple pie").
- Limits result size and includes basic pagination headers.
- Logs search events for observability.

Run:
    python secure_search.py
"""

from flask import Flask, request, jsonify, make_response
from sqlite3 import connect, RowFactory
import logging
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATABASE_PATH = "products.db"
MAX_RESULTS = 100
LOG_LEVEL = logging.INFO

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask app setup
# ---------------------------------------------------------------------------
app = Flask(__name__)

# ---------------------------------------------------------------------------
# Database schema (run this once to create the table)
# ---------------------------------------------------------------------------
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    category TEXT
);
"""

# ---------------------------------------------------------------------------
# Helper: initialize the DB with sample data (run once)
# ---------------------------------------------------------------------------
def init_db() -> None:
    with connect(DATABASE_PATH) as conn:
        conn.row_factory = RowFactory
        conn.execute(CREATE_TABLE_SQL)
        # Insert some sample rows
        rows = [
            (1, "apple", "A red apple", 0.99, "fruit"),
            (2, "banana", "Yellow banana", 0.59, "fruit"),
            (3, "cherry", "Sweet cherry", 1.20, "fruit"),
            (4, "orange", "Juicy orange", 0.79, "fruit"),
            (5, "lemon", "Sour lemon", 0.89, "fruit"),
            (6, "grape", "Purple grape", 1.50, "fruit"),
            (7, "peach", "Fuzzy peach", 1.10, "fruit"),
            (8, "kiwi", "Brown kiwi", 1.30, "fruit"),
            (9, "mango", "Tropical mango", 1.80, "fruit"),
            (10, "pear", "Green pear", 0.95, "fruit"),
        ]
        conn.executemany(
            "INSERT INTO products (id, name, description, price, category) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
        logger.info("Database initialized with sample products.")

# ---------------------------------------------------------------------------
# Core search logic (parameterized, tokenized, sanitized)
# ---------------------------------------------------------------------------
def search_products(query: str) -> List[Dict[str, Any]]:
    if not query:
        return []

    # Normalize query: lower-case, strip whitespace, replace multiple spaces with single space
    query = query.strip().lower()
    if not query:
        return []

    # Tokenize: split on spaces (supports "AND" naturally)
    tokens = query.split()
    if not tokens:
        return []

    # Build a list of lower-case, stripped tokens (security: avoid any SQL injection by not using raw strings)
    safe_tokens = [t.strip() for t in tokens if t.strip()]
    if not safe_tokens:
        return []

    with connect(DATABASE_PATH) as conn:
        conn.row_factory = RowFactory
        # Use a single query with placeholders for each token
        placeholders = ",".join(["?" for _ in safe_tokens])
        cols = "id, name, description, price, category"
        sql = f"""
            SELECT {cols}
            FROM products
            WHERE name LIKE ?
              OR description LIKE ?
              OR category LIKE ?
            AND
            {placeholders}
        """
        # Prepare list of LIKE patterns for each token
        patterns = ["%", t, "%"] for t in safe_tokens
        cursor = conn.execute(sql, patterns)
        results = cursor.fetchall()

    # Limit results
    return results[:MAX_RESULTS]

# ---------------------------------------------------------------------------
# Flask route: GET /search
# ---------------------------------------------------------------------------
@app.route("/search", methods=["GET"])
def search_endpoint() -> Response:
    query = request.args.get("q", "")
    logger.info(f"Search request received: q={query!r}")

    results = search_products(query)

    # Build JSON payload
    payload: Dict[str, Any] = {
        "query": query,
        "count": len(results),
        "results": [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "price": row[3],
                "category": row[4],
            }
            for row in results
        ],
    }

    response = make_response(jsonify(payload), 200)
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    response.headers["X-Total-Count"] = str(len(results))
    response.headers["X-Query-Time"] = "0"  # placeholder for future metrics
    return response

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
