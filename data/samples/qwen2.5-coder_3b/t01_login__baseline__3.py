from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlite3 import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# Connect to SQLite database
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password TEXT NOT NULL)''')
conn.commit()

# Register a new user
@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Insert the user into the database
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()

    return jsonify({"message": "User registered successfully"}), 201

# Login a user
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Retrieve the user from the database
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()

    if not user or not check_password_hash(user[2], password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Generate a session token (simplified for demonstration)
    session_token = "generated_session_token"  # Replace with actual session management
    return jsonify({"message": "Logged in successfully", "session_token": session_token}), 200

if __name__ == '__main__':
    app.run(debug=True)
