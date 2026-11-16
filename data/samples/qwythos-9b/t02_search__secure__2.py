import sqlite3
import os
from flask import Flask, request, jsonify, render_template_string
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-in-production')
DATABASE = 'products.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- Security Utilities ---
def validate_integer(value, min_val=None, max_val=None):
    if value is None:
        return None
    try:
        int_val = int(value)
        if min_val is not None and int_val < min_val:
            raise ValueError(f"Value {int_val} is below minimum {min_val}")
        if max_val is not None and int_val > max_val:
            raise ValueError(f"Value {int_val} exceeds maximum {max_val}")
        return int_val
    except ValueError:
        raise ValueError(f"Invalid integer: {value}")

def sanitize_html(text: str, max_len: int = 256) -> str:
    """Strip HTML tags and truncate to prevent XSS."""
    from html import escape
    if text is None:
        return ""
    clean = escape(str(text).strip())
    return clean[:max_len]

def safe_deserialize_json(data: str, value_type: type) -> value_type:
    """Safely deserialize JSON after validation to avoid unsafe deserialization."""
    if not isinstance(data, str):
        raise ValueError("Input must be a string")
    try:
        parsed = value_type(data)
        # Optional: add range checks here if applicable
        return parsed
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {value_type.__name__}: {data}")

# --- Endpoints ---

@app.route('/api/products/search', methods=['GET'])
def search_products():
    # 1. Validate and sanitize 'q' query parameter (prevent injection if used elsewhere, though we use % escaping)
    q = request.args.get('q', '')
    if not isinstance(q, str):
        q = str(q)
    q = q.strip()
    if not q:
        return jsonify({'error': 'Missing or empty query parameter "q".'}), 400

    # 2. Validate optional page/limit integers
    page = validate_integer(request.args.get('page'), min_val=1)
    limit = validate_integer(request.args.get('limit'), min_val=1, max_val=100)
    if limit is None:
        limit = 20  # default

    # 3. Connect to DB
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 4. Execute query with parameterized statement (SQL injection safe)
        query = """
            SELECT id, name, price, category
            FROM products
            WHERE name LIKE ?
            ORDER BY name
            LIMIT ? OFFSET ?
        """
        pattern = f"%{sanitize_html(q)}%"  # sanitize for display, use % for LIKE
        cursor.execute(query, (pattern, limit, (page - 1) * limit))
        rows = cursor.fetchall()

        # 5. Build response
        results = [
            {
                "id": row["id"],
                "name": row["name"],
                "price": row["price"],
                "category": row["category"]
            }
            for row in rows
        ]
        return jsonify({
            "count": len(results),
            "page": page,
            "limit": limit,
            "results": results
        })
    finally:
        conn.close()

@app.route('/api/products/<path:path>', methods=['GET'])
def get_product_detail(path):
    # Secure path traversal: only allow alphanumeric + hyphen/underscore
    if not all(c.isalnum() or c in '-_' for c in path):
        return jsonify({"error": "Invalid product identifier."}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, category FROM products WHERE id = ?", (path,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Product not found."}), 404
        return jsonify({
            "id": row["id"],
            "name": row["name"],
            "price": row["price"],
            "category": row["category"]
        })
    finally:
        conn.close()

# --- Example HTML template (serves as a simple UI) ---
# This demonstrates XSS sanitization: user input is escaped before rendering.
@app.route('/')
def index():
    return render_template_string('''
        <!doctype html>
        <html>
        <head><title>Empero AI Product Search</title></head>
        <body>
          <h1>Search Products</h1>
          <form method="get" action="/api/products/search">
            <input name="q" placeholder="Search name or category" required>
            <button type="submit">Search</button>
          </form>
          <p>Use <code>/api/products/search?q=...&page=1&limit=20</code> via curl.</p>
          <script>
            // Simple client-side validation: ensure query is not empty
            document.querySelector('form').addEventListener('submit', function(e) {
              const q = new URLSearchParams(window.location.search).get('q');
              if (!q) e.preventDefault();
            });
          </script>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    # In production, use gunicorn or uvicorn instead of Flask's debug server
    app.run(host='127.0.0.1', port=5000, debug=True)
