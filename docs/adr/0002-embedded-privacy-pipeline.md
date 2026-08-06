# Privacy pipeline: embedded Presidio and NeMo Guardrails

HealthPilot runs Presidio (PII detection/masking/de-anonymization) and NeMo Guardrails (input/output validation) **in-process** inside the FastAPI backend — no separate Docker services. The user-facing pipeline remains: **Presidio → NeMo input → LLM → NeMo output → Presidio de-anonymize**. NeMo config lives at `src/healthPilot/privacy/nemo_config/`. Requires the spaCy model: `python -m spacy download en_core_web_lg`.

**Considered options:** Separate Docker microservices (ADR-0001, superseded — added ops complexity for early-stage dev); Guardrails AI instead of NeMo (rejected — user chose NeMo Colang).

**Consequences:** Backend startup loads spaCy + NeMo (slower cold start, ~500MB+ memory); single-process deployment; no `docker compose` needed for privacy layer.
