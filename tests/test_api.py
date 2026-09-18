"""
API integration tests.

Uses TestClient with MOCK_LLM=true to avoid real LLM calls during CI.
"""
import json
import os

import pytest

# Set MOCK_LLM before importing the app
os.environ["MOCK_LLM"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key-not-used"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_valid_request() -> dict:
    hours = []
    for h in range(24):
        solar = max(0, 40 - abs(h - 12) * 5)
        demand = 60 + (20 if 8 <= h <= 20 else 0)
        tariff = 14.0 if 17 <= h <= 20 else 8.0
        hours.append({
            "hour": h,
            "demand_kwh": demand,
            "solar_kwh": solar,
            "tariff_bdt_per_kwh": tariff,
        })
    return {
        "scenario_id": "test-scenario-001",
        "operator_notes": [
            "Reduce solar output by 30% from 11 AM to 2 PM.",
            "Maintain at least 40 kWh in battery from 6 PM to 9 PM.",
            "Do not charge the battery from 5 PM to 9 PM.",
        ],
        "hours": hours,
        "battery": {
            "capacity_kwh": 200.0,
            "initial_energy_kwh": 100.0,
            "minimum_energy_kwh": 20.0,
            "max_charge_kwh_per_hour": 50.0,
            "max_discharge_kwh_per_hour": 50.0,
        },
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealth:
    def test_get_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Valid POST /optimize-energy
# ---------------------------------------------------------------------------

class TestValidOptimization:
    def test_valid_request_returns_200(self):
        payload = make_valid_request()
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 200, f"Got {response.status_code}: {response.text[:500]}"

    def test_response_has_correct_structure(self):
        payload = make_valid_request()
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "scenario_id" in data
        assert "directive_interpretation" in data
        assert "hourly_plan" in data
        assert "total_grid_kwh" in data
        assert "total_cost_bdt" in data
        assert "peak_grid_kwh" in data
        assert "plan_summary" in data

    def test_scenario_id_matches(self):
        payload = make_valid_request()
        payload["scenario_id"] = "unique-test-123"
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 200
        assert response.json()["scenario_id"] == "unique-test-123"

    def test_exactly_24_hourly_plans(self):
        payload = make_valid_request()
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["hourly_plan"]) == 24

    def test_hourly_plan_hours_are_0_to_23(self):
        payload = make_valid_request()
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 200
        hours = [h["hour"] for h in response.json()["hourly_plan"]]
        assert sorted(hours) == list(range(24))

    def test_directive_interpretation_count_matches_notes(self):
        payload = make_valid_request()
        payload["operator_notes"] = ["Reduce solar by 20% from 10 AM to 1 PM."]
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["directive_interpretation"]) == 1

    def test_battery_actions_valid(self):
        payload = make_valid_request()
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 200
        for h in response.json()["hourly_plan"]:
            assert h["battery_action"] in ("charge", "discharge", "idle")

    def test_idle_hours_have_zero_battery_kwh(self):
        payload = make_valid_request()
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 200
        for h in response.json()["hourly_plan"]:
            if h["battery_action"] == "idle":
                assert h["battery_kwh"] == 0.0

    def test_final_battery_equals_initial(self):
        payload = make_valid_request()
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 200
        hourly = response.json()["hourly_plan"]
        final_battery = hourly[23]["battery_energy_after_kwh"]
        initial = payload["battery"]["initial_energy_kwh"]
        assert abs(final_battery - initial) < 0.01, (
            f"Final battery {final_battery} != initial {initial}"
        )

    def test_total_grid_kwh_is_consistent(self):
        payload = make_valid_request()
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 200
        data = response.json()
        computed = sum(h["grid_kwh"] for h in data["hourly_plan"])
        assert abs(data["total_grid_kwh"] - round(computed, 4)) < 0.01

    def test_peak_grid_kwh_is_consistent(self):
        payload = make_valid_request()
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 200
        data = response.json()
        peak = max(h["grid_kwh"] for h in data["hourly_plan"])
        assert abs(data["peak_grid_kwh"] - round(peak, 4)) < 0.01


# ---------------------------------------------------------------------------
# Malformed requests
# ---------------------------------------------------------------------------

class TestMalformedRequests:
    def test_missing_scenario_id(self):
        payload = make_valid_request()
        del payload["scenario_id"]
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_missing_battery(self):
        payload = make_valid_request()
        del payload["battery"]
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_missing_hours(self):
        payload = make_valid_request()
        del payload["hours"]
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_missing_operator_notes(self):
        payload = make_valid_request()
        del payload["operator_notes"]
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_empty_operator_notes(self):
        payload = make_valid_request()
        payload["operator_notes"] = []
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_too_many_operator_notes(self):
        payload = make_valid_request()
        payload["operator_notes"] = ["note1", "note2", "note3", "note4"]  # 4 > max 3
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_invalid_json_body(self):
        response = client.post(
            "/optimize-energy",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Invalid hours structure
# ---------------------------------------------------------------------------

class TestInvalidHoursStructure:
    def test_wrong_number_of_hours(self):
        payload = make_valid_request()
        payload["hours"] = payload["hours"][:20]  # only 20 hours
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_duplicate_hours(self):
        payload = make_valid_request()
        payload["hours"][5]["hour"] = 3  # duplicate hour 3
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_negative_demand(self):
        payload = make_valid_request()
        payload["hours"][0]["demand_kwh"] = -5.0
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_negative_solar(self):
        payload = make_valid_request()
        payload["hours"][0]["solar_kwh"] = -1.0
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_negative_tariff(self):
        payload = make_valid_request()
        payload["hours"][0]["tariff_bdt_per_kwh"] = -0.5
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_battery_initial_exceeds_capacity(self):
        payload = make_valid_request()
        payload["battery"]["initial_energy_kwh"] = 300.0  # > capacity 200
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_battery_minimum_exceeds_capacity(self):
        payload = make_valid_request()
        payload["battery"]["minimum_energy_kwh"] = 250.0  # > capacity 200
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400

    def test_battery_initial_below_minimum(self):
        payload = make_valid_request()
        payload["battery"]["initial_energy_kwh"] = 10.0
        payload["battery"]["minimum_energy_kwh"] = 50.0
        response = client.post("/optimize-energy", json=payload)
        assert response.status_code == 400
