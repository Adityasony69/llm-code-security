from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to SQLite database
conn = sqlite3.connect('products.db')
cursor = conn.cursor()

# Example SQLite table creation (adjust as needed)
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL
)
''')
conn.commit()

# Secure endpoint for filtering products
@app.route('/search', methods=['GET'])
def search_products():
    # Get the query string parameter
    query = request.args.get('query', '')

    # Sanitize the query string to prevent SQL injection
    # Use parameterized queries to avoid SQL injection
    sanitized_query = f"%{query}%"

    try:
        # Execute the query with parameterized input
        cursor.execute('''
            SELECT * FROM products
            WHERE name LIKE ?
        ''', (sanitized_query,))
        results = cursor.fetchall()

        # Convert results to a list of dictionaries
        products = [{'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3]} for row in results]

        return jsonify(products)

    except sqlite3.Error as e:
        # Log the error
        print(f"SQLite error: {e}")
        return jsonify({'error': 'An error occurred'}), 500

    finally:
        # Close the database connection
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
