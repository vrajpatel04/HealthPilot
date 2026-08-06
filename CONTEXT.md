# HealthPilot

An agentic AI wellness coach that learns from daily behavior, blood reports, and trusted health knowledge to produce personalized lifestyle recommendations.

## Language

**Presidio**:
Embedded PII detection and de-identification library (presidio-analyzer + presidio-anonymizer) running in-process in the backend. Responsible for entity detection and token vault de-anonymization only, not conversational policy.
_Avoid_: Privacy layer, PII scanner, Presidio Docker service

**Guardrails**:
Embedded NeMo Guardrails library enforcing programmable safety policies (wellness scope, no diagnosis, emergency redirect) in-process in the backend.
_Avoid_: Safety filters, content moderation (as product terms), NeMo Docker service

**PII**:
Direct personal identifiers in free text — names, phone numbers, email addresses, government IDs, patient IDs on lab reports.
_Avoid_: Sensitive data (too broad), personal info

**PHI**:
Health information linked to an identifiable person — biomarkers, diagnoses, provider names, dates of service, plus any PII appearing on medical documents.
_Avoid_: Health data (when you mean structured biomarkers only), medical PII

**De-identification**:
Removing or replacing direct identifiers from free text before that text crosses the external LLM boundary. Biomarkers are excluded when already stored in structured fields.
_Avoid_: Anonymization (implies irreversible), redaction (one technique among several)

**External LLM boundary**:
The point where text leaves HealthPilot infrastructure and reaches a third-party model provider (Mesh API). All free text must be de-identified before crossing this boundary.
_Avoid_: API gateway, model endpoint

**Privacy pipeline**:
The mandatory sequence for user-facing LLM calls: Presidio (mask PII) → Guardrails (input check) → LLM → Guardrails (output check) → Presidio (de-anonymize). Guardrails and the LLM never see raw PII; the user receives de-anonymized text only at the end.
_Avoid_: Middleware chain, safety stack

**De-anonymization**:
Restoring original identifiers from token placeholders in the validated LLM response before it is returned to the user. Uses the token vault created during masking; runs only after output guardrails pass.
_Avoid_: Decryption, unmasking
