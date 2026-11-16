from flask import Flask, request, jsonify
from sqlite3 import connect
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample SQLite database connection
DATABASE = 'products.db'

def get_product_by_name(name):
    conn = connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + name + '%',))
    products = cursor.fetchall()
    conn.close()
    return products

@app.route('/api/products', methods=['GET'])
def search_products():
    # Validate the query string parameter
    query = request.args.get('name', '')
    if not isinstance(query, str):
        return jsonify({"error": "Invalid query string"}), 400

    # Use parameterized query to prevent SQL injection
    products = get_product_by_name(query)

    # Convert results to a list of dictionaries for JSON response
    product_list = [{'id': product[0], 'name': product[1], 'price': product[2]} for product in products]

    return jsonify(product_list)

if __name__ == '__main__':
    app.run(debug=True)
