from datetime import date

from healthPilot.services.lifestyle_service import (
    ACTIVITY_NUMERIC,
    LifestyleService,
    compute_aggregates_from_logs,
)


def test_activity_numeric_mapping():
    assert ACTIVITY_NUMERIC["sedentary"] == 1
    assert ACTIVITY_NUMERIC["active"] == 4


def test_compute_aggregates_single_day():
    logs = [
        {
            "responses": {
                "sleep_hours": 6.0,
                "water_glasses": 8,
                "activity_level": "light",
                "screen_hours": 4.0,
                "mood": 3,
                "stress": 4,
                "energy": 2,
            }
        }
    ]
    agg = compute_aggregates_from_logs(logs)
    assert agg["sleep_average"] == 6.0
    assert agg["stress_average"] == 4.0
    assert agg["days_in_window"] == 1


def test_material_change_detects_sleep_delta():
    old = {
        "sleep_hours": 7.0,
        "stress": 2,
        "mood": 4,
        "energy": 4,
        "water_glasses": 6,
        "screen_hours": 3.0,
        "activity_level": "moderate",
    }
    new = {
        "sleep_hours": 5.0,
        "stress": 2,
        "mood": 4,
        "energy": 4,
        "water_glasses": 6,
        "screen_hours": 3.0,
        "activity_level": "moderate",
    }
    assert LifestyleService.responses_materially_changed(old, new) is True


def test_material_change_ignores_small_delta():
    old = {
        "sleep_hours": 7.0,
        "stress": 2,
        "mood": 4,
        "energy": 4,
        "water_glasses": 6,
        "screen_hours": 3.0,
        "activity_level": "moderate",
    }
    new = {
        "sleep_hours": 7.5,
        "stress": 2,
        "mood": 4,
        "energy": 4,
        "water_glasses": 6,
        "screen_hours": 3.0,
        "activity_level": "moderate",
    }
    assert LifestyleService.responses_materially_changed(old, new) is False
