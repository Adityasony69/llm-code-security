from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'products.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    ''')
    if conn.execute("SELECT 1 FROM products LIMIT 1").fetchone() is None:
        conn.executemany(
            "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
            [
                ("Laptop", 999.99, "High performance laptop"),
                ("Mouse", 29.99, "Wireless ergonomic mouse"),
                ("Keyboard", 79.99, "Mechanical RGB keyboard"),
                ("Monitor", 349.99, "27-inch 4K display"),
                ("Headphones", 149.99, "Noise-cancelling over-ear headphones")
            ]
        )
    conn.commit()
    conn.close()

@app.route('/api/search', methods=['GET'])
def search_products():
    query = request.args.get('q', '').lower().strip()
    conn = get_db()
    cursor = conn.execute(
        "SELECT id, name, price, description FROM products WHERE name LIKE ? OR description LIKE ? ORDER BY name",
        (f'%{query}%', f'%{query}%')
    )
    results = cursor.fetchall()
    conn.close()
    return jsonify([{
        "id": row["id"],
        "name": row["name"],
        "price": row["price"],
        "description": row["description"]
    } for row in results])

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
