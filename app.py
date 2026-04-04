"""ACEest Fitness — v2.0: Pure business-logic functions added."""

from __future__ import annotations
from typing import Any

PROGRAMS = {
    "Fat Loss (FL) - 3 day": {"calorie_factor": 22, "description": "3-day full-body fat loss"},
    "Fat Loss (FL) - 5 day": {"calorie_factor": 24, "description": "5-day split fat loss"},
    "Muscle Gain (MG) - PPL": {"calorie_factor": 35, "description": "Push/Pull/Legs hypertrophy"},
    "Beginner (BG)": {"calorie_factor": 26, "description": "3-day beginner full-body"},
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
        category, risk_note = "Underweight", "Increase caloric intake."
    elif bmi < 25.0:
        category, risk_note = "Normal", "Maintain current lifestyle."
    elif bmi < 30.0:
        category, risk_note = "Overweight", "Prioritise adherence and cardio."
    else:
        category, risk_note = "Obese", "Focus on fat loss and supervision."
    return {"bmi": bmi, "category": category, "risk_note": risk_note}


def calculate_calories(weight_kg: float, program_name: str) -> int:
    """Estimate daily calories from bodyweight and programme type."""
    if program_name not in PROGRAMS:
        raise ValueError(f"Unknown program: '{program_name}'.")
    if weight_kg <= 0:
        raise ValueError("Weight must be a positive value (kg).")
    return int(weight_kg * PROGRAMS[program_name]["calorie_factor"])
