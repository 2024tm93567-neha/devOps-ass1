"""ACEest Fitness — v2.2: Flask REST API skeleton with health + programmes."""

from __future__ import annotations
import os
from typing import Any
from flask import Flask, abort, jsonify, request

PROGRAMS = {
    "Fat Loss (FL) - 3 day": {"calorie_factor": 22, "description": "3-day full-body fat loss"},
    "Fat Loss (FL) - 5 day": {"calorie_factor": 24, "description": "5-day split fat loss"},
    "Muscle Gain (MG) - PPL": {"calorie_factor": 35, "description": "Push/Pull/Legs hypertrophy"},
    "Beginner (BG)": {"calorie_factor": 26, "description": "3-day beginner full-body"},
}


def calculate_bmi(weight_kg, height_cm):
    if height_cm <= 0:
        raise ValueError("Height must be a positive value (cm).")
    if weight_kg <= 0:
        raise ValueError("Weight must be a positive value (kg).")
    h_m = height_cm / 100.0
    bmi = round(weight_kg / (h_m ** 2), 1)
    if bmi < 18.5:
        category, risk_note = "Underweight", "Increase caloric intake."
    elif bmi < 25.0:
        category, risk_note = "Normal", "Maintain current lifestyle."
    elif bmi < 30.0:
        category, risk_note = "Overweight", "Prioritise adherence and cardio."
    else:
        category, risk_note = "Obese", "Focus on fat loss and supervision."
    return {"bmi": bmi, "category": category, "risk_note": risk_note}


def calculate_calories(weight_kg, program_name):
    if program_name not in PROGRAMS:
        raise ValueError(f"Unknown program: '{program_name}'.")
    if weight_kg <= 0:
        raise ValueError("Weight must be a positive value (kg).")
    return int(weight_kg * PROGRAMS[program_name]["calorie_factor"])


def create_app(test_config=None):
    flask_app = Flask(__name__)
    flask_app.config.from_mapping(DATABASE=os.environ.get("DATABASE_URL", "aceest_fitness.db"))
    if test_config:
        flask_app.config.from_mapping(test_config)

    @flask_app.route("/")
    def index():
        return jsonify({"service": "ACEest Fitness & Gym Management API", "version": "2.2", "status": "operational"})

    @flask_app.route("/api/health")
    def health():
        return jsonify({"status": "healthy", "service": "aceest-fitness"})

    @flask_app.route("/api/programs")
    def list_programs():
        return jsonify({"programs": list(PROGRAMS.keys()), "count": len(PROGRAMS)})

    @flask_app.route("/api/programs/<string:name>")
    def get_program(name):
        if name not in PROGRAMS:
            abort(404, description=f"Program '{name}' not found.")
        return jsonify({"program": name, "details": PROGRAMS[name]})

    @flask_app.errorhandler(404)
    def not_found(exc):
        return jsonify({"error": "Not Found", "message": str(exc.description)}), 404

    return flask_app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
