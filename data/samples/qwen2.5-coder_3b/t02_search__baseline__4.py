from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query', '')
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + query + '%',))
    results = cursor.fetchall()
    conn.close()
    return jsonify([{'id': row[0], 'name': row[1], 'price': row[2]} for row in results])

if __name__ == '__main__':
    app.run(debug=True)
