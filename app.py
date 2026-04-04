"""
ACEest Fitness & Gym Management System
=======================================
REST API — Flask Application
Version : 3.2.4
Author  : ACEest DevOps Team

Evolution:
  v1.0   – Basic program display (tkinter prototype)
  v1.1   – Client profile + calorie factor
  v1.1.2 – Multi-client list, CSV export, embedded charts
  v2.0.1 – SQLite persistence, save / load clients
  v2.1.2 – Progress history (weekly adherence)
  v2.2.1 – Adherence chart (matplotlib)
  v2.2.4 – Body metrics, workout logging, BMI analytics
  v3.0.1 – Full client management with goals & analytics
  v3.1.2 – Login, PDF reports, AI-style program generator
  v3.2.4 – Production REST API (this file) — Flask + SQLite
"""

from __future__ import annotations

import os
import sqlite3
from typing import Any

from flask import Flask, abort, jsonify, request


PROGRAMS: dict[str, dict[str, Any]] = {
    "Fat Loss (FL) - 3 day": {
        "calorie_factor": 22,
        "description": "3-day full-body fat loss protocol",
        "days_per_week": 3,
        "workout_plan": {
            "Monday": "Back Squat 5x5 + Core AMRAP",
            "Wednesday": "Bench Press 4x8 + 21-15-9 Metabolic Circuit",
            "Friday": "Deadlift 4x5 + Zone 2 Cardio 30 min",
        },
        "nutrition": {
            "breakfast": "3 Egg Whites + Oats",
            "lunch": "Grilled Chicken (200 g) + Brown Rice",
            "dinner": "Fish Curry + Millet Roti",
            "target_kcal": 2000,
        },
    },
    "Fat Loss (FL) - 5 day": {
        "calorie_factor": 24,
        "description": "5-day split — higher-volume fat loss",
        "days_per_week": 5,
        "workout_plan": {
            "Monday": "Back Squat 5x5 + Core",
            "Tuesday": "EMOM 20 min Assault Bike",
            "Wednesday": "Bench Press + 21-15-9",
            "Thursday": "Deadlift + Box Jumps 10RFT",
            "Friday": "Zone 2 Cardio 30 min + Mobility",
        },
        "nutrition": {
            "breakfast": "3 Egg Whites + Oats",
            "lunch": "Grilled Chicken (200 g) + Brown Rice",
            "dinner": "Fish Curry + Millet Roti",
            "target_kcal": 2200,
        },
    },
    "Muscle Gain (MG) - PPL": {
        "calorie_factor": 35,
        "description": "Push / Pull / Legs hypertrophy 6-day split",
        "days_per_week": 6,
        "workout_plan": {
            "Monday": "Push: Bench Press 5x5 + Incline DB 4x10",
            "Tuesday": "Pull: Barbell Row 4x8 + Lat Pulldown 4x12",
            "Wednesday": "Legs: Back Squat 5x5 + Romanian DL 4x8",
            "Thursday": "Push: OHP 4x8 + Cable Fly 3x15",
            "Friday": "Pull: Deadlift 4x5 + Pull-Up 4x8",
            "Saturday": "Legs: Front Squat 4x6 + Leg Press 3x15",
        },
        "nutrition": {
            "breakfast": "4 Eggs + Peanut Butter Oats",
            "lunch": "Chicken Biryani (250 g Chicken)",
            "dinner": "Mutton Curry + Jeera Rice",
            "target_kcal": 3200,
        },
    },
    "Beginner (BG)": {
        "calorie_factor": 26,
        "description": "3-day simple beginner full-body program",
        "days_per_week": 3,
        "workout_plan": {
            "Monday": "Full Body: Air Squats 3x15, Ring Rows 3x10, Push-ups 3x12",
            "Wednesday": "Full Body: Goblet Squat 3x12, DB Row 3x10, Pike Push-up 3x8",
            "Friday": "Full Body: Lunges 3x12, Band Pull-Apart 3x15, Plank 3x30s",
        },
        "nutrition": {
            "breakfast": "Idli + Sambar",
            "lunch": "Rice + Dal + Vegetables",
            "dinner": "Chapati + Sabzi + Curd",
            "target_kcal": 1800,
        },
    },
}


def calculate_bmi(weight_kg: float, height_cm: float) -> dict[str, Any]:
    """Calculate BMI and return category with risk note."""
    if height_cm <= 0:
        raise ValueError("Height must be a positive value (cm).")
    if weight_kg <= 0:
        raise ValueError("Weight must be a positive value (kg).")
    h_m = height_cm / 100.0
    bmi = round(weight_kg / (h_m ** 2), 1)
    if bmi < 18.5:
        category = "Underweight"
        risk_note = "Potential nutrient deficiency; consider increasing caloric intake."
    elif bmi < 25.0:
        category = "Normal"
        risk_note = "Low risk — maintain current lifestyle and training consistency."
    elif bmi < 30.0:
        category = "Overweight"
        risk_note = "Moderate risk — prioritise adherence and progressive cardio."
    else:
        category = "Obese"
        risk_note = "Higher risk — focus on fat loss, consistency, and professional supervision."
    return {"bmi": bmi, "category": category, "risk_note": risk_note}


def calculate_calories(weight_kg: float, program_name: str) -> int:
    """Estimate daily calories from bodyweight and program type."""
    if program_name not in PROGRAMS:
        valid = list(PROGRAMS.keys())
        raise ValueError(f"Unknown program: '{program_name}'. Valid options: {valid}")
    if weight_kg <= 0:
        raise ValueError("Weight must be a positive value (kg).")
    factor: int = PROGRAMS[program_name]["calorie_factor"]
    return int(weight_kg * factor)


def create_app(test_config: dict | None = None) -> Flask:
    """Flask application factory."""
    flask_app = Flask(__name__)
    flask_app.config.from_mapping(
        DATABASE=os.environ.get("DATABASE_URL", "aceest_fitness.db"),
        TESTING=False,
    )
    if test_config is not None:
        flask_app.config.from_mapping(test_config)

    def get_db() -> sqlite3.Connection:
        conn = sqlite3.connect(flask_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db() -> None:
        conn = get_db()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    UNIQUE NOT NULL,
                age        INTEGER,
                height     REAL,
                weight     REAL,
                program    TEXT,
                calories   INTEGER,
                created_at TEXT    DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS progress (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name  TEXT    NOT NULL,
                week         TEXT    NOT NULL,
                adherence    INTEGER NOT NULL
                                     CHECK (adherence BETWEEN 0 AND 100),
                recorded_at  TEXT    DEFAULT (datetime('now'))
            );
            """
        )
        conn.commit()
        conn.close()

    init_db()

    @flask_app.route("/")
    def index():
        return jsonify({
            "service": "ACEest Fitness & Gym Management API",
            "version": "3.2.4",
            "status": "operational",
            "endpoints": {
                "health": "/api/health",
                "programs": "/api/programs",
                "bmi": "/api/bmi?weight=<kg>&height=<cm>",
                "calories": "/api/calories?weight=<kg>&program=<name>",
                "clients": "/api/clients",
                "client": "/api/clients/<name>",
                "progress": "/api/clients/<name>/progress",
            },
        })

    @flask_app.route("/api/health")
    def health():
        return jsonify({"status": "healthy", "service": "aceest-fitness"})

    @flask_app.route("/api/programs")
    def list_programs():
        return jsonify({"programs": list(PROGRAMS.keys()), "count": len(PROGRAMS)})

    @flask_app.route("/api/programs/<string:name>")
    def get_program(name: str):
        if name not in PROGRAMS:
            abort(404, description=f"Program '{name}' not found.")
        return jsonify({"program": name, "details": PROGRAMS[name]})

    @flask_app.route("/api/bmi")
    def bmi_endpoint():
        try:
            weight = float(request.args.get("weight") or 0)
            height = float(request.args.get("height") or 0)
            return jsonify(calculate_bmi(weight, height))
        except (ValueError, TypeError) as exc:
            abort(400, description=str(exc))

    @flask_app.route("/api/calories")
    def calories_endpoint():
        try:
            weight = float(request.args.get("weight") or 0)
            program = request.args.get("program") or ""
            kcal = calculate_calories(weight, program)
            return jsonify({"weight_kg": weight, "program": program, "estimated_kcal": kcal})
        except (ValueError, TypeError) as exc:
            abort(400, description=str(exc))

    @flask_app.route("/api/clients", methods=["GET"])
    def list_clients():
        conn = get_db()
        rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
        conn.close()
        return jsonify({"clients": [dict(r) for r in rows], "count": len(rows)})

    @flask_app.route("/api/clients", methods=["POST"])
    def create_client():
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get("name") or "").strip()
        if not name:
            abort(400, description="'name' is a required field.")
        program = (data.get("program") or "").strip()
        if program and program not in PROGRAMS:
            abort(400, description=f"Unknown program: '{program}'.")
        try:
            weight = float(data.get("weight") or 0)
            height = float(data.get("height") or 0)
            age = int(data.get("age") or 0)
        except (ValueError, TypeError):
            abort(400, description="'age', 'weight', and 'height' must be numeric.")
        calories = calculate_calories(weight, program) if weight > 0 and program else None
        conn = get_db()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO clients (name,age,height,weight,program,calories) VALUES (?,?,?,?,?,?)",
                (name, age or None, height or None, weight or None, program or None, calories),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
            conn.close()
            return jsonify({"message": "Client saved successfully.", "client": dict(row)}), 201
        except Exception as exc:
            conn.close()
            abort(500, description=str(exc))

    @flask_app.route("/api/clients/<string:name>", methods=["GET"])
    def get_client(name: str):
        conn = get_db()
        row = conn.execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
        conn.close()
        if row is None:
            abort(404, description=f"Client '{name}' not found.")
        return jsonify({"client": dict(row)})

    @flask_app.route("/api/clients/<string:name>", methods=["DELETE"])
    def delete_client(name: str):
        conn = get_db()
        result = conn.execute("DELETE FROM clients WHERE name = ?", (name,))
        conn.commit()
        conn.close()
        if result.rowcount == 0:
            abort(404, description=f"Client '{name}' not found.")
        return jsonify({"message": f"Client '{name}' deleted successfully."})

    @flask_app.route("/api/clients/<string:name>/progress", methods=["POST"])
    def add_progress(name: str):
        conn = get_db()
        if not conn.execute("SELECT 1 FROM clients WHERE name = ?", (name,)).fetchone():
            conn.close()
            abort(404, description=f"Client '{name}' not found.")
        data = request.get_json(force=True, silent=True) or {}
        week = (data.get("week") or "").strip()
        if not week:
            conn.close()
            abort(400, description="'week' is required (e.g. 'Week 01 - 2025').")
        try:
            adherence = int(data.get("adherence", -1))
        except (ValueError, TypeError):
            conn.close()
            abort(400, description="'adherence' must be an integer between 0 and 100.")
        if not (0 <= adherence <= 100):
            conn.close()
            abort(400, description=f"'adherence' must be between 0 and 100, got {adherence}.")
        conn.execute(
            "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
            (name, week, adherence),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Progress recorded.", "client": name, "week": week, "adherence": adherence}), 201

    @flask_app.route("/api/clients/<string:name>/progress", methods=["GET"])
    def get_progress(name: str):
        conn = get_db()
        if not conn.execute("SELECT 1 FROM clients WHERE name = ?", (name,)).fetchone():
            conn.close()
            abort(404, description=f"Client '{name}' not found.")
        rows = conn.execute(
            "SELECT week, adherence, recorded_at FROM progress WHERE client_name = ? ORDER BY id",
            (name,),
        ).fetchall()
        conn.close()
        history = [dict(r) for r in rows]
        avg = round(sum(r["adherence"] for r in history) / len(history), 1) if history else 0.0
        return jsonify({"client": name, "progress": history, "average_adherence": avg, "weeks_logged": len(history)})

    @flask_app.errorhandler(400)
    def bad_request(exc):
        return jsonify({"error": "Bad Request", "message": str(exc.description)}), 400

    @flask_app.errorhandler(404)
    def not_found(exc):
        return jsonify({"error": "Not Found", "message": str(exc.description)}), 404

    @flask_app.errorhandler(405)
    def method_not_allowed(exc):
        return jsonify({"error": "Method Not Allowed", "message": str(exc.description)}), 405

    @flask_app.errorhandler(500)
    def internal_error(exc):
        return jsonify({"error": "Internal Server Error", "message": str(exc.description)}), 500

    return flask_app


app = create_app()

if __name__ == "__main__":
    _port = int(os.environ.get("PORT", 5000))
    _debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=_port, debug=_debug)
