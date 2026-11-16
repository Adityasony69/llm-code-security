from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'products.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/search', methods=['GET'])
def search_products():
    query = request.args.get('q', '')
    if not query:
        return jsonify([]), 200

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Use parameterized query to prevent SQL injection
        cursor.execute("SELECT id, name, price FROM products WHERE name LIKE ? OR description LIKE ?",
                       (f'%{query}%', f'%{query}%'))
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        return jsonify(results), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
