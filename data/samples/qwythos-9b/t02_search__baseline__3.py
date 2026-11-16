from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# Configuration
DATABASE = 'products.db'

def init_db():
    """Initialize the database with the products table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/search', methods=['GET'])
def search_products():
    """
    Search for products based on a query string parameter.
    
    Query Parameters:
    - q: The search term (matches name, price string, or category)
    - category: Optional exact category filter (e.g., 'electronics')
    
    Returns:
    - JSON list of matching products with id, name, price, category
    """
    query = request.args.get('q', '').lower().strip()
    category_filter = request.args.get('category', '').strip()

    if not query:
        return jsonify({'error': 'Missing required parameter "q"'}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    base_query = "SELECT id, name, price, category FROM products WHERE 1=1"

    if category_filter:
        base_query += f" AND category = '{category_filter}'"

    # Normalize the search query: remove punctuation and split into words
    clean_query = ''.join(char.lower() for char in query if char.isalnum())
    words = clean_query.split()

    if words:
        # Build dynamic WHERE clause to match any word in the query
        conditions = [
            f"(name LIKE '%{word}%' OR price LIKE '%{word}%' OR category LIKE '%{word}%')"
            for word in words
        ]
        base_query += " AND " + " AND ".join(conditions)

    cursor.execute(base_query)
    rows = cursor.fetchall()
    conn.close()

    products = [
        {
            'id': row[0],
            'name': row[1],
            'price': row[2],
            'category': row[3]
        }
        for row in rows
    ]

    return jsonify({'products': products}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
