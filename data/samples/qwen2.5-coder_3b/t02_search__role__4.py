from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_connection():
    return sqlite3.connect('products.db')

@app.route('/search', methods=['GET'])
def search_products():
    query_string = request.args.get('q', '').strip()
    
    if not query_string:
        return jsonify({"error": "Query string is required"}), 400
    
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        # Assuming 'name' is the column you want to search by
        cursor.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + query_string + '%',))
        results = cursor.fetchall()
        
        # Convert results to a list of dictionaries for JSON response
        product_list = [{'id': row[0], 'name': row[1], 'description': row[2]} for row in results]
        
        return jsonify(product_list)
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)
