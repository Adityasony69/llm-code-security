from flask import Flask, request, jsonify
from sqlite3 import connect

app = Flask(__name__)

# Connect to the SQLite database
conn = connect('products.db')
cursor = conn.cursor()

# Create the products table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL
)
''')
conn.commit()

# Insert some sample data into the products table
cursor.execute('''
INSERT INTO products (name, description, price) VALUES
('Product A', 'Description of product A', 10.99),
('Product B', 'Description of product B', 19.99),
('Product C', 'Description of product C', 9.99)
''')
conn.commit()

# Define the product search endpoint
@app.route('/search', methods=['GET'])
def search_products():
    # Get the query string parameter
    query = request.args.get('query', '')

    # If the query is empty, return all products
    if not query:
        cursor.execute('SELECT * FROM products')
    else:
        # Search for products that match the query string
        cursor.execute('SELECT * FROM products WHERE name LIKE ?', ('%' + query + '%',))

    # Fetch the results
    results = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Return the results as JSON
    return jsonify([{'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3]} for row in results])

if __name__ == '__main__':
    app.run(debug=True)
