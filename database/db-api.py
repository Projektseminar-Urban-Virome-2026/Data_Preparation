import sqlite3
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DB_PATH = "/db/database.db"

def get_db():
    """Create a database connection with WAL mode enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # WAL mode allows concurrent reads while writing
    conn.execute("PRAGMA journal_mode=WAL")
    # Enable foreign key enforcement
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

@app.route("/cities", methods=["GET"])
def list_cities():
    conn = get_db()
    cities = conn.execute("SELECT * FROM Cities").fetchall()
    conn.close()
    return jsonify([dict(n) for n in cities])

@app.route("/cities/<int:city_id>", methods=["GET"])
def get_cities(city_id):
    conn = get_db()
    cities = conn.execute("SELECT * FROM Cities WHERE id = ?", (city_id,)).fetchone()
    conn.close()
    if cities is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(cities))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
