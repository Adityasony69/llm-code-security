from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn

# Close the database connection
def close_db_connection(conn):
    conn.close()

# Product search endpoint
@app.route('/search', methods=['GET'])
def search_products():
    # Get the query string parameter
    query = request.args.get('query', '')
    
    # Validate the query string parameter
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    # Connect to the database
    conn = get_db_connection()
    
    try:
        # Prepare the SQL query with parameterized query
        cursor = conn.cursor()
        query = f"SELECT * FROM products WHERE name LIKE ?"
        cursor.execute(query, (f"%{query}%",))
        
        # Fetch all the rows
        products = cursor.fetchall()
        
        # Prepare the response
        response = []
        for product in products:
            response.append({
                "id": product['id'],
                "name": product['name'],
                "description": product['description'],
                "price": product['price']
            })
        
        return jsonify(response)
    
    finally:
        # Close the database connection
        close_db_connection(conn)

if __name__ == '__main__':
    app.run(debug=True)
