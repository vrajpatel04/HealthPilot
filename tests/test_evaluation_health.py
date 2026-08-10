from healthPilot.services.evaluation_service import EvaluationService


def test_lifestyle_fit_boosts_sleep_category_when_low_sleep():
    evaluator = EvaluationService()
    behavior = {"primary_category": None, "high_intent_product_id": None}
    memory = {"successful_recommendations": []}
    health = {"sleep_average": 5.0, "stress_average": 2.0, "activity_average": 3.0}
    candidates = [
        {"product_id": "1", "category": "fitness", "score": 0.5, "price": 100},
        {"product_id": "2", "category": "sleep", "score": 0.5, "price": 100},
    ]
    ranked = evaluator.score_candidates(
        candidates, behavior, memory, health_profile=health, blood_report_summary=None
    )
    assert ranked[0]["product_id"] == "2"


def test_biomarker_dimension_skipped_without_report():
    evaluator = EvaluationService()
    behavior = {"primary_category": "nutrition"}
    memory = {"successful_recommendations": []}
    health = {"sleep_average": 7.0, "stress_average": 2.0, "activity_average": 3.0}
    candidates = [{"product_id": "1", "category": "nutrition", "score": 0.5, "price": 100}]
    scored = evaluator.score_candidates(
        candidates, behavior, memory, health_profile=health, blood_report_summary=None
    )
    assert "biomarker_relevance" not in scored[0]
