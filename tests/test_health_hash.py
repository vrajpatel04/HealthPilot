from healthPilot.services.health_hash import compute_health_hash


def test_health_hash_changes_when_sleep_average_changes():
    profile_a = {"sleep_average": 7.0, "stress_average": 2.0}
    profile_b = {"sleep_average": 5.0, "stress_average": 2.0}
    events = [{"event_type": "search", "metadata": {"query": "sleep"}}]
    assert compute_health_hash(events=events, health_profile=profile_a, blood_report_id=None) != compute_health_hash(
        events=events, health_profile=profile_b, blood_report_id=None
    )


def test_health_hash_includes_blood_report_id():
    events = [{"event_type": "search", "metadata": {"query": "sleep"}}]
    health = {"sleep_average": 7.0}
    without = compute_health_hash(events=events, health_profile=health, blood_report_id=None)
    with_report = compute_health_hash(events=events, health_profile=health, blood_report_id="abc-123")
    assert without != with_report
