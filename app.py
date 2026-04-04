"""ACEest Fitness — v3.0: SQLite persistence and client CRUD endpoints."""

from __future__ import annotations
import os
import sqlite3
from typing import Any
from flask import Flask, abort, jsonify, request

PROGRAMS = {
    "Fat Loss (FL) - 3 day": {"calorie_factor": 22, "description": "3-day full-body fat loss"},
    "Fat Loss (FL) - 5 day": {"calorie_factor": 24, "description": "5-day split fat loss"},
    "Muscle Gain (MG) - PPL": {"calorie_factor": 35, "description": "Push/Pull/Legs hypertrophy"},
    "Beginner (BG)": {"calorie_factor": 26, "description": "3-day beginner full-body"},
}


def calculate_bmi(weight_kg, height_cm):
    if height_cm <= 0: raise ValueError("Height must be positive.")
    if weight_kg <= 0: raise ValueError("Weight must be positive.")
    bmi = round(weight_kg / (height_cm / 100.0) ** 2, 1)
    if bmi < 18.5: return {"bmi": bmi, "category": "Underweight", "risk_note": "Increase caloric intake."}
    if bmi < 25.0: return {"bmi": bmi, "category": "Normal", "risk_note": "Maintain current lifestyle."}
    if bmi < 30.0: return {"bmi": bmi, "category": "Overweight", "risk_note": "Prioritise cardio."}
    return {"bmi": bmi, "category": "Obese", "risk_note": "Focus on fat loss."}


def calculate_calories(weight_kg, program_name):
    if program_name not in PROGRAMS: raise ValueError(f"Unknown program: '{program_name}'.")
    if weight_kg <= 0: raise ValueError("Weight must be positive.")
    return int(weight_kg * PROGRAMS[program_name]["calorie_factor"])


def create_app(test_config=None):
    flask_app = Flask(__name__)
    flask_app.config.from_mapping(DATABASE=os.environ.get("DATABASE_URL", "aceest_fitness.db"))
    if test_config:
        flask_app.config.from_mapping(test_config)

    def get_db():
        conn = sqlite3.connect(flask_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        return conn

    def init_db():
        conn = get_db()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL,
                age INTEGER, height REAL, weight REAL, program TEXT, calories INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit(); conn.close()

    init_db()

    @flask_app.route("/")
    def index():
        return jsonify({"service": "ACEest Fitness & Gym Management API", "version": "3.0", "status": "operational"})

    @flask_app.route("/api/health")
    def health():
        return jsonify({"status": "healthy", "service": "aceest-fitness"})

    @flask_app.route("/api/programs")
    def list_programs():
        return jsonify({"programs": list(PROGRAMS.keys()), "count": len(PROGRAMS)})

    @flask_app.route("/api/programs/<string:name>")
    def get_program(name):
        if name not in PROGRAMS: abort(404, description=f"Program '{name}' not found.")
        return jsonify({"program": name, "details": PROGRAMS[name]})

    @flask_app.route("/api/clients", methods=["GET"])
    def list_clients():
        conn = get_db(); rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall(); conn.close()
        return jsonify({"clients": [dict(r) for r in rows], "count": len(rows)})

    @flask_app.route("/api/clients", methods=["POST"])
    def create_client():
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get("name") or "").strip()
        if not name: abort(400, description="'name' is required.")
        program = (data.get("program") or "").strip()
        if program and program not in PROGRAMS: abort(400, description=f"Unknown program: '{program}'.")
        weight = float(data.get("weight") or 0); height = float(data.get("height") or 0); age = int(data.get("age") or 0)
        calories = calculate_calories(weight, program) if weight > 0 and program else None
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO clients (name,age,height,weight,program,calories) VALUES (?,?,?,?,?,?)",
                     (name, age or None, height or None, weight or None, program or None, calories))
        conn.commit()
        row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone(); conn.close()
        return jsonify({"message": "Client saved.", "client": dict(row)}), 201

    @flask_app.route("/api/clients/<string:name>", methods=["GET"])
    def get_client(name):
        conn = get_db(); row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone(); conn.close()
        if row is None: abort(404, description=f"Client '{name}' not found.")
        return jsonify({"client": dict(row)})

    @flask_app.route("/api/clients/<string:name>", methods=["DELETE"])
    def delete_client(name):
        conn = get_db(); result = conn.execute("DELETE FROM clients WHERE name=?", (name,)); conn.commit(); conn.close()
        if result.rowcount == 0: abort(404, description=f"Client '{name}' not found.")
        return jsonify({"message": f"Client '{name}' deleted."})

    @flask_app.errorhandler(400)
    def bad_request(exc): return jsonify({"error": "Bad Request", "message": str(exc.description)}), 400

    @flask_app.errorhandler(404)
    def not_found(exc): return jsonify({"error": "Not Found", "message": str(exc.description)}), 404

    return flask_app


app = create_app()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
