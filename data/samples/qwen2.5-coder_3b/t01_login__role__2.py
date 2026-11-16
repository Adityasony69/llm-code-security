from flask import Flask, request, jsonify
import sqlite3
import bcrypt

app = Flask(__name__)

# Connect to SQLite database
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
conn.commit()

def hash_password(password):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def verify_password(stored_password, provided_password):
    # Verify the provided password against the stored hash
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    # Check if the username already exists
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    user = c.fetchone()
    if user:
        return jsonify({'error': 'Username already exists'}), 400

    # Hash the password
    hashed_password = hash_password(password)

    # Insert the user into the database
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    # Fetch the user from the database
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    user = c.fetchone()
    if not user or not verify_password(user[2], password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Login successful, you can return a token or session here
    return jsonify({'message': 'Login successful'}), 200

if __name__ == '__main__':
    app.run(debug=True)
