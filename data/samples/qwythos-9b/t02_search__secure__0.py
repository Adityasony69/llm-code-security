# Qwythos - Empero AI
# Secure Flask product search endpoint for SQLite

from flask import Flask, request, jsonify
import sqlite3
import re
from functools import lru_cache

app = Flask(__name__)

# Use a fixed path for the database to avoid path traversal vulnerabilities
DATABASE_PATH = '/var/lib/app/products.db'
# Use a simple dictionary for configuration instead of a config file to avoid SSRF
CONFIG = {
    'db_path': DATABASE_PATH,
    'allowed_fields': ['name', 'price', 'category', 'description'],
    'max_results': 50,
}

@lru_cache(maxsize=1)
def get_db_connection():
    """Cached database connection to minimize overhead."""
    conn = sqlite3.connect(CONFIG['db_path'])
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/products/search', methods=['GET'])
def search_products():
    # Securely parse query parameters with defaults
    q = request.args.get('q', '').strip()
    fields = request.args.get('fields', '').strip()
    limit = request.args.get('limit', '').strip()
    
    # Validate query string is not empty
    if not q:
        return jsonify({'error': 'Missing or empty search query'}), 400
    
    # Validate fields parameter to avoid SQL injection
    # Only allow fields listed in CONFIG
    if fields:
        valid_fields = [f for f in fields.split(',') if f in CONFIG['allowed_fields']]
        if not valid_fields:
            return jsonify({'error': 'No valid fields provided'}), 400
        field_clause = ','.join(f"{f} LIKE ?" for f in valid_fields)
        search_params = tuple(f'%{q}%') * len(valid_fields)
    else:
        # Default to searching all allowed fields
        field_clause = ','.join(f"{f} LIKE ?" for f in CONFIG['allowed_fields'])
        search_params = tuple(f'%{q}%') * len(CONFIG['allowed_fields'])
    
    # Validate limit parameter to prevent excessive data retrieval
    if limit:
        try:
            limit = int(limit)
            if limit < 1 or limit > CONFIG['max_results']:
                limit = CONFIG['max_results']
        except ValueError:
            limit = CONFIG['max_results']
    else:
        limit = CONFIG['max_results']
    
    cursor = get_db_connection().cursor()
    cursor.execute(
        f"SELECT * FROM products WHERE {field_clause} ORDER BY rowid LIMIT ?",
        search_params + (limit,)
    )
    rows = cursor.fetchall()
    cursor.close()
    
    # Return results in a simple JSON format
    products = [dict(row) for row in rows]
    return jsonify({'products': products}), 200

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
