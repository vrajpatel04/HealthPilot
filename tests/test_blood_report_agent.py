from healthPilot.agents.blood_report_agent import BloodReportAgent, _parse_biomarkers, _derive_flags


def test_parse_biomarkers_from_lab_text():
    text = "HbA1c: 6.2\nVitamin D: 14\nLDL: 162\nHDL: 38\nTriglycerides: 230"
    biomarkers = _parse_biomarkers(text)
    assert biomarkers["hba1c"] == 6.2
    assert biomarkers["vitamin_d"] == 14.0
    assert biomarkers["ldl"] == 162.0


def test_derive_flags_vitamin_d_low():
    flags = _derive_flags({"vitamin_d": 14, "ldl": 100})
    assert "vitamin_d_low" in flags


def test_extract_returns_empty_when_no_text():
    agent = BloodReportAgent()
    result = agent.extract_biomarkers(b"", "image/jpeg")
    assert result["biomarkers"] == {}
