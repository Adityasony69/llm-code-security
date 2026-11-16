from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Sample SQLite database connection
def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn

# Sample table schema
# products.db
# CREATE TABLE products (
#     id INTEGER PRIMARY KEY,
#     name TEXT,
#     description TEXT
# )

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query', '')

    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM products WHERE name LIKE ?', ('%' + query + '%',))
    products = cursor.fetchall()
    conn.close()

    if not products:
        return jsonify({'message': 'No products found'}), 404

    return jsonify([dict(product) for product in products])

if __name__ == '__main__':
    app.run(debug=True)
