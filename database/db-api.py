import sqlite3
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DB_PATH = "/db/database.db"
MODEL_DIR = Path("/models")

STAEDTE_NACH_KLIMA = {
    "Gemäßigt": ["Copenhagen", "Regina", "Seattle", "Melbourne"],
    "Subtropisch": ["Guangzhou"],
    "Tropisch": ["Kuala Lumpur", "Quito", "Yaounde"],
}

KLIMAZONE_PRO_STADT = {
    stadt: klimazone
    for klimazone, staedte in STAEDTE_NACH_KLIMA.items()
    for stadt in staedte
}

MODEL_FILES = {
    "shannon_model": "shannon_mixed_modell.pkl",
    "shannon_baseline": "shannon_baseline_mediane.pkl",
    "tobamo_model": "tobamo_mixed_modell.pkl",
    "tobamo_baseline": "tobamo_baseline_mediane.pkl",
}

MODELS = None

def get_db():
    """Create a database connection with WAL mode enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # WAL mode allows concurrent reads while writing
    conn.execute("PRAGMA journal_mode=WAL")
    # Enable foreign key enforcement
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def load_models():
    global MODELS
    if MODELS is not None:
        return MODELS, []

    missing = [
        str(MODEL_DIR / filename)
        for filename in MODEL_FILES.values()
        if not (MODEL_DIR / filename).exists()
    ]
    if missing:
        return None, missing

    MODELS = {
        name: joblib.load(MODEL_DIR / filename)
        for name, filename in MODEL_FILES.items()
    }
    return MODELS, []

def value_or_none(value):
    if pd.isna(value):
        return None
    return float(value)

def first_prediction_value(prediction):
    if hasattr(prediction, "iloc"):
        return prediction.iloc[0]
    return prediction[0]

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

@app.route("/cities/<int:city_id>/sampleCount", methods=["GET"])
def get_sample_count(city_id):
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) as count FROM runs WHERE city_id = ?", (city_id,)).fetchone()
    conn.close()
    return jsonify(dict(count))

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
            (SELECT MAX(temperature) FROM Weather) AS max_temperature,
            (SELECT COUNT(*) FROM Virus WHERE human_host=1) AS host_count
    """).fetchone()
    conn.close()
    return jsonify(dict(stats))

@app.route("/cities/<int:city_id>/runs", methods=["GET"])
def get_runs_for_city(city_id):
    conn = get_db()
    runs = conn.execute("""
        SELECT 
            r.run_accession,
            r.run_alias,
            r.collection_date,
            r.city_id,
            r.SampleID,
            r.shannon_index
        FROM 
            runs r
        WHERE 
            r.city_id = ?
        ORDER BY 
            r.collection_date ASC
    """, (city_id,))

    runs_data = [dict(row) for row in runs.fetchall()]

    conn.close()
    return jsonify(runs_data)

@app.route("/runs/<run_accession>/model_values", methods=["GET"])
def get_model_values_for_run(run_accession):
    conn = get_db()
    row = conn.execute("""
        SELECT
            r.run_accession,
            r.collection_date,
            r.city_id,
            r.shannon_index,
            c.name AS city,
            c.country AS country,
            w.temperature,
            w.humidity,
            w.rainfall,
            w.wind_speed
        FROM runs r
        JOIN Cities c ON c.id = r.city_id
        LEFT JOIN Weather w ON w.run_accession = r.run_accession
        WHERE r.run_accession = ?
    """, (run_accession,)).fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "run not found"}), 404

    run_data = dict(row)
    klimazone = KLIMAZONE_PRO_STADT.get(run_data["city"])
    if klimazone is None:
        return jsonify({"error": "climate zone not configured for city", "run": run_data}), 500

    features = {
        "Temp": run_data["temperature"],
        "Regen": run_data["rainfall"],
        "Luftfeuchtigkeit": run_data["humidity"],
    }
    model_input = pd.DataFrame([{
        "Stadt": run_data["city"],
        "Klimazone": klimazone,
        **features,
    }])

    models, missing = load_models()
    response = {
        "run": run_data,
        "features": {
            "Stadt": run_data["city"],
            "Klimazone": klimazone,
            **{key: value_or_none(value) for key, value in features.items()},
        },
    }

    missing_inputs = [name for name, value in features.items() if value is None]
    if missing_inputs:
        response["model_status"] = "missing_input"
        response["missing_inputs"] = missing_inputs
        return jsonify(response), 422

    if models is None:
        response["model_status"] = "missing"
        response["missing_models"] = missing
        return jsonify(response), 503

    shannon_prediction = first_prediction_value(models["shannon_model"].predict(model_input))
    tobamo_prediction = first_prediction_value(models["tobamo_model"].predict(model_input))
    response["model_status"] = "ok"
    response["predictions"] = {
        "shannon_mixed_model": value_or_none(shannon_prediction),
        "shannon_baseline": value_or_none(models["shannon_baseline"].get(run_data["city"])),
        "tobamo_mixed_model": value_or_none(tobamo_prediction),
        "tobamo_baseline": value_or_none(models["tobamo_baseline"].get(run_data["city"])),
    }
    return jsonify(response)

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

@app.route("/cities/<int:city_id>/human_host_virus", methods=["GET"])
def get_human_host_viruses(city_id):
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
            v.human_host AS human_host,
            SUM(vir.amount_in_sample_as_percentage) AS percentage,
            COUNT(DISTINCT vir.run_accession) AS run_count,
            COUNT(*) AS hit_count
        FROM runs r
        JOIN Virus_in_Runs vir ON vir.run_accession = r.run_accession
        JOIN Virus v ON v.tax_id = vir.virus_tax_id
        WHERE r.city_id = ? AND human_host=1
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
        FROM runs r
        JOIN Virus_in_Runs vir ON r.run_accession = vir.run_accession
        JOIN Virus vi ON vir.virus_tax_id = vi.tax_id
        WHERE r.city_id = ? AND vi.realm IS NOT NULL
        GROUP BY r.run_accession, vi.realm
        ORDER BY vi.realm ASC, r.collection_date ASC
    """, (city_id,)).fetchall()

    conn.close()

    virus_data = [dict(row) for row in rows]

    return jsonify({
        "city": dict(city),
        "aggregated_virus_data": virus_data
    })

@app.route("/cities/<int:city_id>/virus/<int:virus_id>/abundance", methods=["GET"])
def get_virus_abundance(city_id, virus_id):
    conn = get_db()
    city = conn.execute("SELECT * FROM Cities WHERE id = ?", (city_id,)).fetchone()
    virus = conn.execute("SELECT name FROM Virus WHERE tax_id = ?", (virus_id,)).fetchone()
    if virus is None:
        return jsonify({"error": "Virus not found"}), 404

    virus_name = virus["name"]

    rows = conn.execute("""
         SELECT
                r.collection_date,
                COALESCE(vir.amount_in_sample_as_percentage, 0) AS amount_in_sample_as_percentage
            FROM runs r
            LEFT JOIN Virus_in_Runs vir 
            ON r.run_accession = vir.run_accession AND vir.virus_tax_id = ?
            WHERE r.city_id = ?
            ORDER BY r.collection_date
    """, (virus_id, city_id)).fetchall()

    conn.close()
    if not rows:
        return jsonify({"error": "No data found"}), 404

    abundance_data = [dict(row) for row in rows]

    return jsonify({
        "city": dict(city),
        "virus_id": virus_id,
        "virus_name": virus_name,
        "abundance_data": abundance_data,
    })



@app.route("/cities/<int:city_id>/collection_weather_data", methods=["GET"])
def get_collection_weather_data_for_city(city_id):
    conn = get_db()
    city = conn.execute("SELECT * FROM Cities WHERE id = ?", (city_id,)).fetchone()

    rows = conn.execute("""
        SELECT 
            r.run_accession,
            r.collection_date,
            w.temperature,
            w.humidity,
            w.rainfall,
            w.wind_speed
        FROM runs r
        JOIN Weather w ON r.run_accession = w.run_accession
        WHERE r.city_id = ?
        ORDER BY r.collection_date ASC
    """, (city_id,)).fetchall()

    weather_data = [dict(row) for row in rows]
    conn.close()

    return jsonify({
        "city": dict(city),
        "weather_data": weather_data
    })

@app.route("/cities/<int:city_id>/weather_data", methods=["GET"])
def get_weather_data_for_city(city_id):
    conn = get_db()
    city = conn.execute("SELECT name FROM Cities WHERE id = ?", (city_id,)).fetchone()
    conn.close()

    city = city['name'].replace(" ","")

    weather_data = pd.read_csv(f"/cities/{city}/smk_output/{city}_weather.csv")
    weather_data.rename(columns={'temperature_2m_mean (°C)': 'temperature', 'rain_sum (mm)': 'rainfall', 'relative_humidity_2m_mean (%)': 'humidity'}, inplace=True)
    return jsonify(weather_data.to_dict(orient='records'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
