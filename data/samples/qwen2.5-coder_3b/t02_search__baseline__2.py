from flask import Flask, request, jsonify
from sqlite3 import connect

app = Flask(__name__)

# Sample SQLite database
# You can replace this with your actual SQLite database setup
DATABASE = 'products.db'

def get_db_connection():
    conn = connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + query + '%',))
    products = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in products])

if __name__ == '__main__':
    app.run(debug=True)
