from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to the SQLite database
conn = sqlite3.connect('products.db')
cursor = conn.cursor()

# Create a table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL
    )
''')
conn.commit()

# Sample data for demonstration
cursor.execute('''
    INSERT INTO products (name, description, price) VALUES
    ('Laptop', 'High-performance laptop', 1200.00),
    ('Smartphone', 'Latest smartphone model', 800.00),
    ('Monitor', 'High-resolution display', 200.00),
    ('Headphones', 'Noise-cancelling headphones', 150.00)
''')
conn.commit()

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('q', '')

    # Sanitize the query to prevent SQL injection
    sanitized_query = query.replace('%', '%%').replace('_', '%%')

    # Execute the query
    cursor.execute(f'SELECT * FROM products WHERE name LIKE ?', (f'%{sanitized_query}%',))
    results = cursor.fetchall()

    # Convert results to a list of dictionaries
    products = [{'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3]} for row in results]

    # Return the results as JSON
    return jsonify(products)

if __name__ == '__main__':
    app.run(debug=True)
