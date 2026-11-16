from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to the SQLite database
conn = sqlite3.connect('products.db')
cursor = conn.cursor()

# Create the products table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL
    )
''')

# Insert some sample data into the products table
cursor.execute('''
    INSERT INTO products (name, description, price) VALUES
    ('Product A', 'Description for Product A', 19.99),
    ('Product B', 'Description for Product B', 29.99),
    ('Product C', 'Description for Product C', 39.99)
''')

conn.commit()

@app.route('/search', methods=['GET'])
def search_products():
    query_string = request.args.get('query', '')
    
    if not query_string:
        return jsonify({'error': 'No query string provided'}), 400
    
    # Filter products based on the query string
    cursor.execute('SELECT * FROM products WHERE name LIKE ?', (f'%{query_string}%',))
    products = cursor.fetchall()
    
    # Convert the results to a list of dictionaries
    product_list = [{'id': product[0], 'name': product[1], 'description': product[2], 'price': product[3]} for product in products]
    
    return jsonify(product_list)

if __name__ == '__main__':
    app.run(debug=True)
