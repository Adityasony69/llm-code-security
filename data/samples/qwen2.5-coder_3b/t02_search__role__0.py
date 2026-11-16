from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query', '')

    # Connect to the database
    conn = get_db_connection()

    # Prepare the SQL query
    sql = "SELECT * FROM products WHERE name LIKE ? OR description LIKE ?"
    params = ('%' + query + '%', '%' + query + '%')

    # Execute the query
    cursor = conn.cursor()
    cursor.execute(sql, params)

    # Fetch the results
    results = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Convert the results to a list of dictionaries
    products = [dict(row) for row in results]

    # Return the results as a JSON response
    return jsonify(products)

if __name__ == '__main__':
    app.run(debug=True)
