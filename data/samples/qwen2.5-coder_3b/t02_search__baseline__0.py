from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to SQLite database
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

# Sample data to populate the table
data = [
    ('Laptop', 'High-performance notebook', 999.99),
    ('Smartphone', 'Latest Android smartphone', 499.99),
    ('Tablet', 'Touchscreen tablet', 299.99),
    ('Monitor', '32-inch full HD monitor', 249.99)
]

# Insert sample data into the table
cursor.executemany('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', data)
conn.commit()

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query', '', type=str)
    
    if not query:
        return jsonify({'error': 'No query parameter provided'}), 400
    
    # Prepare the SQL query with a wildcard for partial matches
    cursor.execute('SELECT * FROM products WHERE name LIKE ?', ('%' + query + '%',))
    results = cursor.fetchall()
    
    # Convert results to a list of dictionaries for JSON response
    products = [{'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3]} for row in results]
    
    return jsonify(products)

if __name__ == '__main__':
    app.run(debug=True)
