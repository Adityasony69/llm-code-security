from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Create a SQLite database and a table
conn = sqlite3.connect('products.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price REAL
    )
''')
conn.commit()

# Sample data to insert into the table
c.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', ('Laptop', 'A high-performance laptop', 999.99))
c.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', ('Smartphone', 'Latest model with 5G', 799.99))
c.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', ('Tablet', 'Portable computing device', 499.99))
conn.commit()

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    # Connect to the SQLite database
    conn = sqlite3.connect('products.db')
    c = conn.cursor()

    # Execute the query
    c.execute('SELECT * FROM products WHERE name LIKE ?', ('%' + query + '%',))
    results = c.fetchall()

    # Close the database connection
    conn.close()

    # Prepare the response
    products = [{'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3]} for row in results]
    return jsonify(products)

if __name__ == '__main__':
    app.run(debug=True)
