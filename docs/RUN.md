# HealthPilot — Run Guide & API Examples

Steps to run the backend with the embedded privacy pipeline (Presidio + NeMo Guardrails).

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [uv](https://docs.astral.sh/uv/) | Latest | Python dependency management |
| Python | 3.12+ | Backend runtime |

No Docker required for Presidio or NeMo — both run in-process.

---

## 1. Clone and configure environment

```powershell
cd D:\Projects\HealthPilot
copy .env.example .env
```

Edit `.env` and set at minimum:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-agent-llm-key
LLM_MODEL=openai/gpt-4o

NEMO_LLM_BASE_URL=https://api.openai.com/v1
NEMO_LLM_API_KEY=your-nemo-judge-key
NEMO_LLM_MODEL=gpt-4o-mini
```

For **Mesh API**:

```env
OPENAI_BASE_URL=https://api.meshapi.ai/v1
OPENAI_API_KEY=rsk_your-key-here
```

---

## 2. Install dependencies

```powershell
uv sync
```

The spaCy model (`en_core_web_lg`) is installed automatically as a project dependency.

---

## 3. Start the backend

```powershell
uv run python app.py
```

Backend runs at **http://localhost:8000**.

On startup you should see:

```text
Privacy pipeline — Presidio: ready, NeMo Guardrails: ready
```

Interactive API docs: **http://localhost:8000/docs**

---

## Privacy pipeline flow

Every user-facing coach request follows this order:

```text
User input
    → Presidio (PII detection + masking)
    → NeMo Guardrails (input validation)
    → LLM (Mesh / OpenAI-compatible)
    → NeMo Guardrails (output validation)
    → Presidio (de-anonymization)
    → User response
```

NeMo config: `src/healthPilot/privacy/nemo_config/config.yml`

---

## 4. Health checks

### Backend

```bash
curl http://localhost:8000/health
```

```powershell
Invoke-RestMethod http://localhost:8000/health
```

### Privacy pipeline

```bash
curl http://localhost:8000/api/privacy/health
```

Example response:

```json
{
  "presidio": true,
  "nemo_guardrails": true,
  "ready": true
}
```

---

## 5. API examples

Base URL: `http://localhost:8000`

### Root

```bash
curl http://localhost:8000/
```

### AI Coach (full privacy pipeline)

**Basic wellness question:**

```bash
curl -X POST http://localhost:8000/api/privacy/coach \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What are three simple habits to improve sleep?\"}"
```

**With PII + structured biomarkers** (name masked before LLM, restored in response):

```bash
curl -X POST http://localhost:8000/api/privacy/coach \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Hi, I am Rahul. My phone is 9876543210. What wellness goals should I focus on?\", \"biomarkers\": {\"HbA1c\": 6.2, \"Vitamin D\": 14}}"
```

Example response:

```json
{
  "response": "Hi Rahul, based on your HbA1c of 6.2 and Vitamin D of 14, ...",
  "deidentified_input": "Hi, I am {{PERSON_1}}. My phone is {{IN_PHONE_1}}. What wellness goals should I focus on?",
  "blocked": false,
  "error": null
}
```

**Internal agent path** (skips NeMo output rail and de-anonymization):

```bash
curl -X POST http://localhost:8000/api/privacy/coach \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Extract biomarkers from this report text.\", \"user_facing\": false}"
```

---

## 6. PowerShell equivalents

```powershell
$body = @{
  message = "Hi, I am Rahul. What wellness goals should I focus on?"
  biomarkers = @{ HbA1c = 6.2; "Vitamin D" = 14 }
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://localhost:8000/api/privacy/coach `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

```powershell
Invoke-RestMethod http://localhost:8000/api/privacy/health
```

---

## 7. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Presidio: failed` on startup | Run `uv sync` — spaCy model is bundled as a dependency |
| `NeMo Guardrails: failed` | Check `NEMO_LLM_API_KEY` and `NEMO_LLM_BASE_URL` in `.env` |
| `503` on `/api/privacy/coach` | Privacy engines failed to load — check startup logs |
| `422` blocked response | Content failed guardrails (diagnosis/prescription/emergency policy) |
| Slow first request | Normal — spaCy + NeMo load on first use (~10–30s cold start) |

---

## Quick start (copy-paste)

```powershell
copy .env.example .env
# Edit .env with your API keys

uv sync
uv run python app.py
```

In another terminal:

```powershell
Invoke-RestMethod http://localhost:8000/api/privacy/health
```
