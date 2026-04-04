"""
ACEest Fitness & Gym — Comprehensive Pytest Test Suite
=======================================================

Coverage map
------------
Section A  – Root & Health endpoints (smoke tests)
Section B  – Programs catalogue (listing + individual retrieval)
Section C  – BMI calculator endpoint
Section D  – Calorie estimation endpoint
Section E  – Client CRUD (create / read / delete / update)
Section F  – Weekly progress tracking
Section G  – Pure unit tests for business-logic functions
Section H  – Error-handling & edge cases
"""

import json
from urllib.parse import quote

import pytest

from app import PROGRAMS, calculate_bmi, calculate_calories


# ═══════════════════════════════════════════════════════════════════════════════
# A  –  Root & Health
# ═══════════════════════════════════════════════════════════════════════════════


class TestRootAndHealth:
    """Smoke tests: the service must be alive and self-describing."""

    def test_root_returns_200(self, client):
        rv = client.get("/")
        assert rv.status_code == 200

    def test_root_json_contains_service_name(self, client):
        data = client.get("/").get_json()
        assert data["service"] == "ACEest Fitness & Gym Management API"

    def test_root_json_contains_status_operational(self, client):
        data = client.get("/").get_json()
        assert data["status"] == "operational"

    def test_root_json_contains_version(self, client):
        data = client.get("/").get_json()
        assert "version" in data

    def test_root_json_contains_endpoints_map(self, client):
        data = client.get("/").get_json()
        assert "endpoints" in data
        assert "health" in data["endpoints"]
        assert "programs" in data["endpoints"]

    def test_health_returns_200(self, client):
        rv = client.get("/api/health")
        assert rv.status_code == 200

    def test_health_returns_healthy_status(self, client):
        data = client.get("/api/health").get_json()
        assert data["status"] == "healthy"

    def test_health_returns_service_name(self, client):
        data = client.get("/api/health").get_json()
        assert "aceest-fitness" in data["service"]


# ═══════════════════════════════════════════════════════════════════════════════
# B  –  Programs
# ═══════════════════════════════════════════════════════════════════════════════


class TestPrograms:
    """Validate the fitness-program catalogue endpoints."""

    def test_list_programs_returns_200(self, client):
        rv = client.get("/api/programs")
        assert rv.status_code == 200

    def test_list_programs_returns_all_four(self, client):
        data = client.get("/api/programs").get_json()
        assert data["count"] == 4

    def test_list_programs_contains_fat_loss_3day(self, client):
        data = client.get("/api/programs").get_json()
        assert "Fat Loss (FL) - 3 day" in data["programs"]

    def test_list_programs_contains_muscle_gain_ppl(self, client):
        data = client.get("/api/programs").get_json()
        assert "Muscle Gain (MG) - PPL" in data["programs"]

    def test_list_programs_contains_beginner(self, client):
        data = client.get("/api/programs").get_json()
        assert "Beginner (BG)" in data["programs"]

    def test_get_program_fat_loss_3day_returns_200(self, client):
        name = quote("Fat Loss (FL) - 3 day")
        rv = client.get(f"/api/programs/{name}")
        assert rv.status_code == 200

    def test_get_program_returns_calorie_factor(self, client):
        name = quote("Beginner (BG)")
        data = client.get(f"/api/programs/{name}").get_json()
        assert data["details"]["calorie_factor"] == 26

    def test_get_program_returns_workout_plan(self, client):
        name = quote("Beginner (BG)")
        data = client.get(f"/api/programs/{name}").get_json()
        assert "workout_plan" in data["details"]

    def test_get_program_returns_nutrition(self, client):
        name = quote("Beginner (BG)")
        data = client.get(f"/api/programs/{name}").get_json()
        assert "nutrition" in data["details"]

    def test_get_program_muscle_gain_calorie_factor(self, client):
        name = quote("Muscle Gain (MG) - PPL")
        data = client.get(f"/api/programs/{name}").get_json()
        assert data["details"]["calorie_factor"] == 35

    def test_get_nonexistent_program_returns_404(self, client):
        rv = client.get("/api/programs/Nonexistent Program")
        assert rv.status_code == 404

    def test_get_nonexistent_program_returns_error_key(self, client):
        data = client.get("/api/programs/Nonexistent Program").get_json()
        assert "error" in data


# ═══════════════════════════════════════════════════════════════════════════════
# C  –  BMI Calculator (endpoint)
# ═══════════════════════════════════════════════════════════════════════════════


class TestBMIEndpoint:
    """BMI endpoint input/output correctness and error handling."""

    def test_normal_bmi_returns_200(self, client):
        rv = client.get("/api/bmi?weight=70&height=175")
        assert rv.status_code == 200

    def test_normal_bmi_value(self, client):
        data = client.get("/api/bmi?weight=70&height=175").get_json()
        # BMI = 70 / (1.75)^2 = 22.9
        assert data["bmi"] == 22.9

    def test_normal_bmi_category(self, client):
        data = client.get("/api/bmi?weight=70&height=175").get_json()
        assert data["category"] == "Normal"

    def test_underweight_bmi_category(self, client):
        # BMI = 45 / (1.75)^2 ≈ 14.7
        data = client.get("/api/bmi?weight=45&height=175").get_json()
        assert data["category"] == "Underweight"

    def test_overweight_bmi_category(self, client):
        # BMI = 85 / (1.70)^2 ≈ 29.4
        data = client.get("/api/bmi?weight=85&height=170").get_json()
        assert data["category"] == "Overweight"

    def test_obese_bmi_category(self, client):
        # BMI = 110 / (1.70)^2 ≈ 38.1
        data = client.get("/api/bmi?weight=110&height=170").get_json()
        assert data["category"] == "Obese"

    def test_bmi_returns_risk_note(self, client):
        data = client.get("/api/bmi?weight=70&height=175").get_json()
        assert "risk_note" in data

    def test_zero_weight_returns_400(self, client):
        rv = client.get("/api/bmi?weight=0&height=175")
        assert rv.status_code == 400

    def test_zero_height_returns_400(self, client):
        rv = client.get("/api/bmi?weight=70&height=0")
        assert rv.status_code == 400

    def test_missing_params_returns_400(self, client):
        rv = client.get("/api/bmi")
        assert rv.status_code == 400

    def test_negative_weight_returns_400(self, client):
        rv = client.get("/api/bmi?weight=-10&height=175")
        assert rv.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# D  –  Calorie Calculator (endpoint)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCalorieEndpoint:
    """Calorie estimation endpoint correctness."""

    def test_beginner_program_returns_200(self, client):
        rv = client.get("/api/calories?weight=70&program=Beginner (BG)")
        assert rv.status_code == 200

    def test_beginner_program_calculation(self, client):
        # 70 kg × 26 factor = 1820 kcal
        data = client.get("/api/calories?weight=70&program=Beginner (BG)").get_json()
        assert data["estimated_kcal"] == 70 * 26

    def test_muscle_gain_ppl_calculation(self, client):
        # 80 kg × 35 factor = 2800 kcal
        name = quote("Muscle Gain (MG) - PPL")
        data = client.get(f"/api/calories?weight=80&program={name}").get_json()
        assert data["estimated_kcal"] == 80 * 35

    def test_fat_loss_3day_calculation(self, client):
        # 75 kg × 22 factor = 1650 kcal
        name = quote("Fat Loss (FL) - 3 day")
        data = client.get(f"/api/calories?weight=75&program={name}").get_json()
        assert data["estimated_kcal"] == 75 * 22

    def test_response_contains_program_name(self, client):
        data = client.get("/api/calories?weight=70&program=Beginner (BG)").get_json()
        assert data["program"] == "Beginner (BG)"

    def test_invalid_program_returns_400(self, client):
        rv = client.get("/api/calories?weight=70&program=Nonexistent")
        assert rv.status_code == 400

    def test_zero_weight_returns_400(self, client):
        rv = client.get("/api/calories?weight=0&program=Beginner (BG)")
        assert rv.status_code == 400

    def test_missing_program_returns_400(self, client):
        rv = client.get("/api/calories?weight=70")
        assert rv.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# E  –  Client CRUD
# ═══════════════════════════════════════════════════════════════════════════════


class TestClientCRUD:
    """Full create / read / update / delete lifecycle for client records."""

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _post_client(client, payload: dict):
        return client.post(
            "/api/clients",
            data=json.dumps(payload),
            content_type="application/json",
        )

    # ── list (empty state) ───────────────────────────────────────────────────

    def test_list_clients_returns_200(self, client):
        rv = client.get("/api/clients")
        assert rv.status_code == 200

    def test_list_clients_returns_count_key(self, client):
        data = client.get("/api/clients").get_json()
        assert "count" in data

    # ── create ───────────────────────────────────────────────────────────────

    def test_create_minimal_client_returns_201(self, client):
        rv = self._post_client(client, {"name": "Arjun Sharma"})
        assert rv.status_code == 201

    def test_create_client_returns_message(self, client):
        rv = self._post_client(client, {"name": "Priya Nair"})
        data = rv.get_json()
        assert "message" in data

    def test_create_client_persists_name(self, client):
        self._post_client(client, {"name": "Ravi Kumar"})
        data = client.get("/api/clients/Ravi Kumar").get_json()
        assert data["client"]["name"] == "Ravi Kumar"

    def test_create_client_calculates_calories_when_weight_and_program_given(self, client):
        payload = {
            "name": "Deepa Pillai",
            "weight": 60.0,
            "program": "Beginner (BG)",
        }
        data = self._post_client(client, payload).get_json()
        expected = 60 * 26  # 1560 kcal
        assert data["client"]["calories"] == expected

    def test_create_client_with_full_profile(self, client):
        payload = {
            "name": "Vikram Singh",
            "age": 28,
            "height": 178.0,
            "weight": 82.0,
            "program": "Muscle Gain (MG) - PPL",
        }
        rv = self._post_client(client, payload)
        assert rv.status_code == 201
        data = rv.get_json()
        assert data["client"]["age"] == 28
        assert data["client"]["height"] == 178.0

    def test_create_client_missing_name_returns_400(self, client):
        rv = self._post_client(client, {"age": 25})
        assert rv.status_code == 400

    def test_create_client_invalid_program_returns_400(self, client):
        rv = self._post_client(
            client, {"name": "Test User", "program": "Invalid Program"}
        )
        assert rv.status_code == 400

    # ── read ─────────────────────────────────────────────────────────────────

    def test_get_existing_client_returns_200(self, client):
        self._post_client(client, {"name": "Meena Krishnan"})
        rv = client.get("/api/clients/Meena Krishnan")
        assert rv.status_code == 200

    def test_get_existing_client_returns_client_data(self, client):
        self._post_client(client, {"name": "Suresh Babu"})
        data = client.get("/api/clients/Suresh Babu").get_json()
        assert "client" in data
        assert data["client"]["name"] == "Suresh Babu"

    def test_get_nonexistent_client_returns_404(self, client):
        rv = client.get("/api/clients/Nobody Here")
        assert rv.status_code == 404

    def test_get_nonexistent_client_returns_error_key(self, client):
        data = client.get("/api/clients/Nobody Here").get_json()
        assert "error" in data

    # ── update (upsert) ───────────────────────────────────────────────────────

    def test_update_existing_client_via_upsert(self, client):
        self._post_client(client, {"name": "Anand Raj", "age": 30})
        self._post_client(client, {"name": "Anand Raj", "age": 31})
        data = client.get("/api/clients/Anand Raj").get_json()
        assert data["client"]["age"] == 31

    # ── delete ────────────────────────────────────────────────────────────────

    def test_delete_existing_client_returns_200(self, client):
        self._post_client(client, {"name": "ToDelete User"})
        rv = client.delete("/api/clients/ToDelete User")
        assert rv.status_code == 200

    def test_delete_existing_client_removes_record(self, client):
        self._post_client(client, {"name": "ToDelete2 User"})
        client.delete("/api/clients/ToDelete2 User")
        rv = client.get("/api/clients/ToDelete2 User")
        assert rv.status_code == 404

    def test_delete_nonexistent_client_returns_404(self, client):
        rv = client.delete("/api/clients/Nobody")
        assert rv.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# F  –  Progress Tracking
# ═══════════════════════════════════════════════════════════════════════════════


class TestProgressTracking:
    """Weekly adherence recording and retrieval."""

    @staticmethod
    def _create_test_client(client, name: str = "Progress Client"):
        client.post(
            "/api/clients",
            data=json.dumps({"name": name}),
            content_type="application/json",
        )

    @staticmethod
    def _post_progress(client, name: str, week: str, adherence: int):
        return client.post(
            f"/api/clients/{name}/progress",
            data=json.dumps({"week": week, "adherence": adherence}),
            content_type="application/json",
        )

    def test_add_progress_returns_201(self, client):
        self._create_test_client(client, "Prog Client 1")
        rv = self._post_progress(client, "Prog Client 1", "Week 01 - 2025", 85)
        assert rv.status_code == 201

    def test_add_progress_response_contains_adherence(self, client):
        self._create_test_client(client, "Prog Client 2")
        data = self._post_progress(
            client, "Prog Client 2", "Week 01 - 2025", 70
        ).get_json()
        assert data["adherence"] == 70

    def test_get_progress_returns_200(self, client):
        self._create_test_client(client, "Prog Client 3")
        rv = client.get("/api/clients/Prog Client 3/progress")
        assert rv.status_code == 200

    def test_get_progress_empty_client_returns_empty_list(self, client):
        self._create_test_client(client, "Prog Client Empty")
        data = client.get("/api/clients/Prog Client Empty/progress").get_json()
        assert data["progress"] == []
        assert data["weeks_logged"] == 0

    def test_get_progress_returns_recorded_entries(self, client):
        self._create_test_client(client, "Prog Client 4")
        self._post_progress(client, "Prog Client 4", "Week 01 - 2025", 80)
        self._post_progress(client, "Prog Client 4", "Week 02 - 2025", 90)
        data = client.get("/api/clients/Prog Client 4/progress").get_json()
        assert data["weeks_logged"] == 2

    def test_get_progress_calculates_correct_average(self, client):
        self._create_test_client(client, "Avg Client")
        self._post_progress(client, "Avg Client", "Week 01 - 2025", 80)
        self._post_progress(client, "Avg Client", "Week 02 - 2025", 100)
        data = client.get("/api/clients/Avg Client/progress").get_json()
        assert data["average_adherence"] == 90.0

    def test_add_progress_nonexistent_client_returns_404(self, client):
        rv = self._post_progress(client, "Nobody At All", "Week 01 - 2025", 50)
        assert rv.status_code == 404

    def test_add_progress_adherence_above_100_returns_400(self, client):
        self._create_test_client(client, "Prog Client 5")
        rv = self._post_progress(client, "Prog Client 5", "Week 01 - 2025", 101)
        assert rv.status_code == 400

    def test_add_progress_adherence_below_0_returns_400(self, client):
        self._create_test_client(client, "Prog Client 6")
        rv = self._post_progress(client, "Prog Client 6", "Week 01 - 2025", -1)
        assert rv.status_code == 400

    def test_add_progress_missing_week_returns_400(self, client):
        self._create_test_client(client, "Prog Client 7")
        rv = client.post(
            "/api/clients/Prog Client 7/progress",
            data=json.dumps({"adherence": 75}),
            content_type="application/json",
        )
        assert rv.status_code == 400

    def test_add_progress_boundary_zero_adherence(self, client):
        self._create_test_client(client, "Prog Client 8")
        rv = self._post_progress(client, "Prog Client 8", "Week 01 - 2025", 0)
        assert rv.status_code == 201

    def test_add_progress_boundary_100_adherence(self, client):
        self._create_test_client(client, "Prog Client 9")
        rv = self._post_progress(client, "Prog Client 9", "Week 01 - 2025", 100)
        assert rv.status_code == 201


# ═══════════════════════════════════════════════════════════════════════════════
# G  –  Pure Unit Tests (business logic functions, no HTTP layer)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCalculateBMI:
    """Direct unit tests for :func:`app.calculate_bmi`."""

    def test_normal_bmi_value(self):
        result = calculate_bmi(70, 175)
        assert result["bmi"] == 22.9

    def test_normal_bmi_category(self):
        assert calculate_bmi(70, 175)["category"] == "Normal"

    def test_underweight_bmi_category(self):
        assert calculate_bmi(45, 175)["category"] == "Underweight"

    def test_overweight_bmi_category(self):
        # 85 / 1.70^2 ≈ 29.4
        assert calculate_bmi(85, 170)["category"] == "Overweight"

    def test_obese_bmi_category(self):
        # 110 / 1.70^2 ≈ 38.1
        assert calculate_bmi(110, 170)["category"] == "Obese"

    def test_result_contains_risk_note(self):
        assert "risk_note" in calculate_bmi(70, 175)

    def test_zero_height_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_bmi(70, 0)

    def test_zero_weight_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_bmi(0, 175)

    def test_negative_height_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_bmi(70, -10)

    def test_negative_weight_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_bmi(-5, 175)

    def test_bmi_boundary_normal_lower(self):
        # BMI = 18.5 → Normal (not Underweight)
        h = 175
        w = 18.5 * (h / 100) ** 2
        assert calculate_bmi(round(w, 1), h)["category"] == "Normal"

    def test_bmi_boundary_overweight_lower(self):
        # BMI = 25.0 → Overweight
        h = 175
        w = 25.0 * (h / 100) ** 2
        assert calculate_bmi(round(w, 1), h)["category"] == "Overweight"


class TestCalculateCalories:
    """Direct unit tests for :func:`app.calculate_calories`."""

    def test_beginner_factor(self):
        assert calculate_calories(70, "Beginner (BG)") == 70 * 26

    def test_fat_loss_3day_factor(self):
        assert calculate_calories(75, "Fat Loss (FL) - 3 day") == 75 * 22

    def test_fat_loss_5day_factor(self):
        assert calculate_calories(75, "Fat Loss (FL) - 5 day") == 75 * 24

    def test_muscle_gain_factor(self):
        assert calculate_calories(80, "Muscle Gain (MG) - PPL") == 80 * 35

    def test_returns_integer(self):
        assert isinstance(calculate_calories(72, "Beginner (BG)"), int)

    def test_unknown_program_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_calories(70, "Unknown Program")

    def test_zero_weight_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_calories(0, "Beginner (BG)")

    def test_negative_weight_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_calories(-10, "Beginner (BG)")


class TestProgramsData:
    """Validate the integrity of the PROGRAMS data constant."""

    def test_programs_has_four_entries(self):
        assert len(PROGRAMS) == 4

    def test_every_program_has_calorie_factor(self):
        for name, data in PROGRAMS.items():
            assert "calorie_factor" in data, f"Missing calorie_factor in '{name}'"

    def test_every_program_has_workout_plan(self):
        for name, data in PROGRAMS.items():
            assert "workout_plan" in data, f"Missing workout_plan in '{name}'"

    def test_every_program_has_nutrition(self):
        for name, data in PROGRAMS.items():
            assert "nutrition" in data, f"Missing nutrition in '{name}'"

    def test_every_program_has_description(self):
        for name, data in PROGRAMS.items():
            assert "description" in data, f"Missing description in '{name}'"

    def test_calorie_factors_are_positive_integers(self):
        for name, data in PROGRAMS.items():
            factor = data["calorie_factor"]
            assert isinstance(factor, int) and factor > 0, (
                f"Invalid calorie_factor {factor} in '{name}'"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# H  –  Edge Cases & Error Handling
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Non-happy-path scenarios that must return appropriate HTTP errors."""

    def test_unknown_route_returns_404(self, client):
        rv = client.get("/api/nonexistent-endpoint")
        assert rv.status_code == 404

    def test_error_response_has_error_key(self, client):
        data = client.get("/api/clients/DoesNotExist").get_json()
        assert "error" in data

    def test_error_response_has_message_key(self, client):
        data = client.get("/api/clients/DoesNotExist").get_json()
        assert "message" in data

    def test_create_client_with_empty_body_returns_400(self, client):
        rv = client.post(
            "/api/clients",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert rv.status_code == 400

    def test_get_progress_nonexistent_client_returns_404(self, client):
        rv = client.get("/api/clients/NoSuchPerson/progress")
        assert rv.status_code == 404

    def test_list_clients_returns_list_key(self, client):
        data = client.get("/api/clients").get_json()
        assert "clients" in data
        assert isinstance(data["clients"], list)
