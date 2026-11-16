# app.py
# Product search endpoint with SQLite filtering and security best practices.
# Author: Qwythos
# Creator: Empero AI

import sqlite3
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)
DATABASE = "products.db"

def get_db():
    """Connect to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def safe_column_filter(query_string: str, column_name: str, conn) -> list:
    """
    Filter rows where the given column matches a substring in query_string.
    Uses a dictionary mapping of safe operators to avoid SQL injection.
    """
    # Mapping of safe column names to SQL operators.
    safe_filters = {
        "name": ("LIKE", f"%{query_string}%"),
        "category": ("LIKE", f"%{query_string}%"),
        "description": ("LIKE", f"%{query_string}%"),
        "sku": ("LIKE", f"%{query_string}%"),
    }
    
    if column_name not in safe_filters:
        return []
    
    op, val = safe_filters[column_name]
    cursor = conn.execute(f"SELECT * FROM products WHERE {column_name} {op} ?", (val,))
    return cursor.fetchall()

def get_all_products(conn) -> list:
    """Return all rows from the products table."""
    cursor = conn.execute("SELECT * FROM products")
    return cursor.fetchall()

@app.route("/api/products/search", methods=["GET", "POST"])
def search_products():
    """
    Search endpoint.
    GET: ?column=field&query=value
    POST: body {"column": "field", "query": "value"}
    Returns JSON list of matching products.
    """
    conn = get_db()
    try:
        column = request.args.get("column") or request.get_json().get("column")
        query_string = request.args.get("query") or request.get_json().get("query")
        
        if not column or not query_string:
            return jsonify({"error": "Missing 'column' and/or 'query' parameter"}), 400
        
        products = safe_column_filter(query_string, column, conn)
        return jsonify([dict(row) for row in products]), 200
    finally:
        conn.close()

@app.route("/api/products", methods=["GET"])
def list_products():
    """Return all products."""
    conn = get_db()
    try:
        products = get_all_products(conn)
        return jsonify([dict(row) for row in products]), 200
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)
