# Privacy pipeline: Presidio → NeMo → LLM as Docker services

HealthPilot handles blood reports, chat, and behavioral data that mix PII and PHI. The full user-facing pipeline is **Presidio (mask)** → **NeMo Guardrails (input)** → **LLM** → **NeMo Guardrails (output)** → **Presidio (de-anonymize)** → user. Presidio and NeMo run as separate Docker services orchestrated by the FastAPI backend via HTTP; LangGraph agent nodes implement each step in order. Biomarkers enter LLM prompts only as structured fields, never as raw report text. Presidio failure blocks all external LLM calls; NeMo failure blocks user-facing responses only.

**Considered options:** Embedded Python libraries (simpler deploy, rejected for isolation and independent scaling); Guardrails AI instead of NeMo (rejected — user chose NeMo Colang); Guardrails before Presidio (rejected — policy engine should not process identifiable text).

**Consequences:** Three-network-hop latency on every LLM call; token vault in PostgreSQL for reversible de-identification; custom Presidio analyzer image for Indian lab-report recognizers; NeMo and agent LLMs configured separately via `.env`.
