"""Embedded Presidio analyzer and anonymizer engines."""

from __future__ import annotations

import logging
from functools import lru_cache

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from healthPilot.core.config import get_settings

logger = logging.getLogger(__name__)


def _custom_recognizers() -> list[PatternRecognizer]:
    indian_phone = PatternRecognizer(
        supported_entity="IN_PHONE",
        patterns=[
            Pattern(
                name="india_mobile",
                regex=r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",
                score=0.85,
            ),
        ],
        context=["phone", "mobile", "contact", "tel"],
    )
    aadhaar = PatternRecognizer(
        supported_entity="IN_AADHAAR",
        patterns=[
            Pattern(
                name="aadhaar",
                regex=r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b",
                score=0.75,
            ),
        ],
        context=["aadhaar", "uid", "uidai"],
    )
    lab_patient_id = PatternRecognizer(
        supported_entity="LAB_PATIENT_ID",
        patterns=[
            Pattern(
                name="lab_id",
                regex=r"(?i)(?:patient|lab|mrn|uhid|ipd|sample)\s*(?:id|no|#)?[\s:.-]*[A-Z0-9-]{5,20}",
                score=0.7,
            ),
        ],
    )
    medical_record = PatternRecognizer(
        supported_entity="MEDICAL_RECORD_NUMBER",
        patterns=[
            Pattern(
                name="mrn",
                regex=r"(?i)\b(?:MRN|UHID|IPD|OPD)\s*(?:No\.?|#|:)?\s*[A-Z0-9-]{4,20}\b",
                score=0.75,
            ),
        ],
    )
    return [indian_phone, aadhaar, lab_patient_id, medical_record]


@lru_cache
def get_analyzer_engine() -> AnalyzerEngine:
    settings = get_settings()
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": settings.PRESIDIO_SPACY_MODEL}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
    for recognizer in _custom_recognizers():
        analyzer.registry.add_recognizer(recognizer)
    logger.info("Presidio analyzer ready (%d recognizers)", len(analyzer.registry.recognizers))
    return analyzer


@lru_cache
def get_anonymizer_engine() -> AnonymizerEngine:
    return AnonymizerEngine()


def warmup_presidio() -> None:
    get_analyzer_engine()
    get_anonymizer_engine()


def analyze(text: str, *, language: str = "en", score_threshold: float) -> list:
    if not text.strip():
        return []
    return get_analyzer_engine().analyze(
        text=text,
        language=language,
        score_threshold=score_threshold,
    )


def anonymize(text: str, analyzer_results: list, operators: dict[str, OperatorConfig]) -> str:
    result = get_anonymizer_engine().anonymize(
        text=text,
        analyzer_results=analyzer_results,
        operators=operators,
    )
    return result.text
