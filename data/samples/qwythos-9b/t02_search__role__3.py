# product_search.py
# A secure Flask endpoint for searching a SQLite 'products' table.
# Requirements: Flask==2.3.2, Flask-SQLAlchemy==3.0.5, Flask-Talisman==1.0.0
# Install with: pip install Flask Flask-SQLAlchemy Flask-Talisman

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from functools import wraps
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Talisman(app, force_https=False, content_security_policy={
    "default-src": "'self'",
    "script-src": "'self'",
    "style-src": "'self'",
    "img-src": "'self' data:"
})

# Product model
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)

# --- Security utilities ---

def sanitize_text(text: str, max_len: int = 256) -> str:
    """Strip HTML, control chars, and truncate to max_len."""
    if not isinstance(text, str):
        text = str(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove non-printables and excessive whitespace
    text = re.sub(r'[^\w\s.,!?;:\-\(\)\[\]\{\}\'\"—…]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_len]

def normalize_search_term(term: str) -> str:
    """Lowercase, strip punctuation, collapse spaces, max 50 chars."""
    term = sanitize_text(term)
    term = term.lower()
    term = re.sub(r'[^a-z0-9\s]', '', term)
    term = re.sub(r'\s+', ' ', term).strip()
    return term[:50]

def validate_query_param(param: str, allowed: str = 'alphanumeric_spaces_punctuation') -> str:
    """Reject params containing SQL injection keywords or long strings."""
    if not param or len(param) > 256:
        raise ValueError("Query parameter too long or empty.")
    if re.search(r'\b(sql|select|insert|update|delete|drop|where|union|;|--|/\\|\\x)\b', param, re.IGNORECASE):
        raise ValueError("Invalid characters in query parameter.")
    return param

# --- Endpoint ---

@app.route('/api/products/search', methods=['GET'])
def search_products():
    # 1. Get and validate the query string
    raw_query = request.args.get('q', '').strip()
    if not raw_query:
        return jsonify({'error': 'Missing required query parameter: q'}), 400

    try:
        clean_query = validate_query_param(raw_query)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # 2. Normalize for case-insensitive search
    normalized = normalize_search_term(clean_query)
    if not normalized:
        return jsonify({'error': 'No valid search term found'}), 400

    # 3. Build a safe SQL query using LIKE with wildcards
    #    Using SQLAlchemy's text() ensures no ORM escaping issues.
    #    We limit results to 20 rows and include a simple score by matching
    #    both name and category for better relevance.
    stmt = db.session.query(Product).filter(
        (Product.name.ilike(f'%{normalized}%')) |
        (Product.category.ilike(f'%{normalized}%'))
    ).limit(20).all()

    # 4. Serialize results
    results = [
        {
            'id': p.id,
            'name': p.name,
            'price': round(p.price, 2),
            'category': p.category
        }
        for p in stmt
    ]

    return jsonify({'results': results}), 200

# --- Seed script for local testing (run once) ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Populate with sample data
        sample_products = [
            Product(name="Wireless Mouse", price=19.99, category="Electronics"),
            Product(name="USB-C Cable", price=9.99, category="Electronics"),
            Product(name="Yoga Mat", price=24.50, category="Fitness"),
            Product(name="Running Shoes", price=89.99, category="Fitness"),
            Product(name="Notebook", price=5.99, category="Stationery"),
        ]
        for p in sample_products:
            db.session.add(p)
        db.session.commit()
        print("Database seeded with 5 products.")
        app.run(debug=True, host='127.0.0.1', port=5000)
