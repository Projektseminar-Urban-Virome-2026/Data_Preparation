import sqlite3
from flask import Flask, jsonify
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

@app.route("/stats", methods=["GET"])
def get_stats():
    conn = get_db()
    stats = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM Virus) AS virus_count,
            (SELECT COUNT(*) FROM runs) AS run_count,
            (SELECT COUNT(*) FROM Cities) AS city_count,
            (SELECT MIN(collection_date) FROM runs) as min_date,
            (SELECT MAX(collection_date) FROM runs) as max_date,
            (SELECT MIN(temperature) FROM Weather) AS min_temperature,
            (SELECT MAX(temperature) FROM Weather) AS max_temperature
    """).fetchone()
    conn.close()
    return jsonify(dict(stats))

@app.route("/cities/<int:city_id>/viruses", methods=["GET"])
def get_city_viruses(city_id):
    conn = get_db()
    city = conn.execute("SELECT * FROM Cities WHERE id = ?", (city_id,)).fetchone()
    rows = conn.execute("""
        SELECT
            v.tax_id AS virus_id,
            v.name AS name,
            v.realm AS realm,
            v.kingdom AS kingdom,
            v.phylum AS phylum,
            v.class AS class,
            v.taxonomic_order AS taxonomic_order,
            v.family AS family,
            v.genus AS genus,
            v.baltimore_class AS baltimore_class,
            COUNT(DISTINCT vir.run_accession) AS run_count,
            COUNT(*) AS hit_count
        FROM runs r
        JOIN Virus_in_Runs vir ON vir.run_accession = r.run_accession
        JOIN Virus v ON v.tax_id = vir.virus_tax_id
        WHERE r.city_id = ?
        GROUP BY v.tax_id, v.name
        ORDER BY run_count DESC, hit_count DESC, v.name ASC
    """, (city_id,)).fetchall()

    run_count = conn.execute(
        "SELECT COUNT(*) AS count FROM runs WHERE city_id = ?",
        (city_id,),
    ).fetchone()["count"]

    conn.close()
    return jsonify({
        "city": dict(city),
        "run_count": run_count,
        "viruses": [dict(row) for row in rows],
    })

@app.route("/viruses/<int:virus_id>/cities", methods=["GET"])
def get_virus_cities(virus_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT
            c.id AS city_id,
            c.name AS city_name,
            c.country AS country,
            c.latitude AS latitude,
            c.longitude AS longitude,
            COUNT(DISTINCT vir.run_accession) AS run_count,
            SUM(vir.amount_in_sample_as_percentage) / COUNT(DISTINCT vir.run_accession) AS average_amount,
            AVG(w.temperature) AS average_temperature
        FROM Virus_in_Runs vir
        JOIN runs r ON r.run_accession = vir.run_accession
        JOIN Cities c ON c.id = r.city_id
        LEFT JOIN Weather w ON w.run_accession = vir.run_accession
        WHERE vir.virus_tax_id = ?
        GROUP BY c.id, c.name, c.country, c.latitude, c.longitude
        ORDER BY average_amount DESC, run_count DESC
    """, (virus_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/cities/<int:city_id>/aggregate_realms", methods=["GET"])
def get_aggregated_realms_for_city(city_id):
    conn = get_db()
    city = conn.execute("SELECT * FROM Cities WHERE id = ?", (city_id,)).fetchone()

    if city is None:
        conn.close()
        return jsonify({"error": "City not found"}), 404

    rows = conn.execute("""
        SELECT 
            r.run_accession,
            r.collection_date,
            vi.realm,
            SUM(vir.amount_in_sample_as_percentage) AS total_percentage
        FROM 
            runs r
        JOIN 
            Virus_in_Runs vir ON r.run_accession = vir.run_accession
        JOIN 
            Virus vi ON vir.virus_tax_id = vi.tax_id
        WHERE 
            r.city_id = ?
        GROUP BY 
            r.run_accession, vi.realm
    """, (city_id,)).fetchall()

    conn.close()

    virus_data = [dict(row) for row in rows]

    return jsonify({
        "city": dict(city),
        "aggregated_virus_data": virus_data
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
