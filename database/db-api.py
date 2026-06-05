import sqlite3
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
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
def list_notes():
    conn = get_db()
    notes = conn.execute("SELECT * FROM Cities").fetchall()
    conn.close()
    return jsonify([dict(n) for n in notes])

@app.route("/cities/<int:city_id>", methods=["GET"])
def get_note(city_id):
    conn = get_db()
    note = conn.execute("SELECT * FROM Cities WHERE id = ?", (city_id,)).fetchone()
    conn.close()
    if note is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(note))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)