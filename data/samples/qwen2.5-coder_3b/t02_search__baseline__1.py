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
    name TEXT NOT NULL
)
''')

# Insert some example data
cursor.execute("INSERT INTO products (name) VALUES ('Laptop'), ('Smartphone'), ('Tablet')")
conn.commit()

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query', '')

    # Execute the query to search for products
    cursor.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + query + '%',))
    products = cursor.fetchall()

    # Convert the products to a list of dictionaries
    product_list = [{'id': product[0], 'name': product[1]} for product in products]

    # Return the results as JSON
    return jsonify(product_list)

if __name__ == '__main__':
    app.run(debug=True)
