from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn

# Check if the request contains a valid query string parameter
def validate_query(query):
    if query is None or not isinstance(query, str):
        return False
    # Simplistic validation: ensure the query is not empty and does not contain potentially harmful characters
    if len(query) == 0 or any(char in [';', '&', '*', '(', ')', '"', "'"] for char in query):
        return False
    return True

# Product search endpoint
@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query')
    
    if not validate_query(query):
        return jsonify({'error': 'Invalid query string'}), 400
    
    # Connect to the database
    conn = get_db_connection()
    try:
        # Prepare the SQL query with parameterized query to prevent SQL injection
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + query + '%',))
        
        # Fetch all matching rows
        products = cur.fetchall()
        
        # Convert rows to a list of dictionaries for JSON response
        result = [dict(row) for row in products]
        
        return jsonify(result)
    finally:
        # Close the database connection
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
