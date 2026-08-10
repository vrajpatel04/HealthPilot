<div align="center">

# 🩺 HealthPilot AI

**Agentic wellness recommendations that learn from behavior — without exposing personal identifiers to external LLMs.**

</div>

<p align="center">
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://python.org/"><img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL"></a>
  <a href="https://qdrant.tech/"><img src="https://img.shields.io/badge/Qdrant-FF4F8B?logo=qdrant&logoColor=white" alt="Qdrant"></a>
  <a href="https://python.langchain.com/"><img src="https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white" alt="LangChain"></a>
  <a href="https://langchain-ai.github.io/langgraph/"><img src="https://img.shields.io/badge/LangGraph-111827?logo=langgraph&logoColor=white" alt="LangGraph"></a>
  <a href="https://microsoft.github.io/presidio/"><img src="https://img.shields.io/badge/Presidio-0078D4?logo=microsoft&logoColor=white" alt="Presidio"></a>
  <a href="https://github.com/NVIDIA/NeMo-Guardrails"><img src="https://img.shields.io/badge/NeMo_Guardrails-76B900?logo=nvidia&logoColor=white" alt="NeMo Guardrails"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

> *"It doesn't just know what you click. It learns what you need next."*

HealthPilot AI is an **agentic wellness marketplace** that observes how users browse, search, check in on lifestyle habits, and optionally upload lab reports — then generates **personalized, persuasive product recommendations** grounded in trusted wellness knowledge.

Every user-facing AI response passes through a **mandatory privacy pipeline** before and after the external LLM boundary.

---

## 🧠 What makes HealthPilot different?

- **Behavioral intelligence** — batched event tracking, intent detection, and long-term memory — not just "users who bought this also bought…"
- **LangGraph agent orchestration** — multi-step recommendation workflow: behavior → memory → retrieval → evaluation → persuasion
- **Dual-store product catalog** — PostgreSQL (source of truth) + Qdrant (semantic search) with background vector sync
- **RAG grounding** — wellness knowledge base (sleep, nutrition, stress) retrieved at recommendation time
- **Optional health signals** — daily lifestyle check-ins and blood report biomarkers as structured personalization context
- **Privacy-first AI** — Presidio PII/PHI masking + NeMo Guardrails on every user-facing LLM call
- **AI efficiency** — smart triggers, behavior hashing, and Redis/Postgres caching to avoid unnecessary model calls

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI + Uvicorn, SQLAlchemy (async), Alembic |
| **Frontend** | Jinja2 templates + vanilla JavaScript (event tracker, async UI) |
| **Primary DB** | PostgreSQL (users, products, events, recommendations, health profiles) |
| **Vector DB** | Qdrant (product embeddings, RAG knowledge, user memory vectors) |
| **Cache** | Redis (optional — recommendations, product lists, trigger cooldowns) |
| **Agents** | LangGraph (recommendation graph + privacy coach graph) |
| **LLM / Embeddings** | Mesh API or any OpenAI-compatible provider |
| **PII protection** | Microsoft Presidio (embedded, in-process) + spaCy `en_core_web_lg` |
| **Safety guardrails** | NVIDIA NeMo Guardrails (embedded, in-process) |
| **Scheduler** | APScheduler (background vector sync) |
| **Observability** | LangSmith (optional tracing) |

---

## 📁 Project Structure

```text
.
├─ app.py                              # Entry point (runs FastAPI)
├─ pyproject.toml
├─ alembic/                            # Database migrations
├─ data/knowledge/                     # RAG source documents (sleep, nutrition, stress…)
├─ scripts/                            # seed_products.py, seed_rag.py
├─ docs/RUN.md                         # Detailed run guide
└─ src/healthPilot/
   ├─ main.py                          # FastAPI app, lifespan, middleware
   ├─ api/                             # REST API (auth, products, events, recommendations…)
   ├─ web/                             # Server-rendered pages (marketplace, lifestyle, admin)
   ├─ templates/ + static/             # Jinja2 HTML + CSS/JS
   ├─ agents/
   │  ├─ recommendation_graph.py      # LangGraph recommendation workflow
   │  ├─ recommendation_nodes.py       # Behavior, memory, retrieval, persuasion agents
   │  ├─ graph.py                      # Privacy coach graph (Presidio → NeMo → LLM)
   │  └─ blood_report_agent.py          # Lab report extraction (structured biomarkers)
   ├─ privacy/
   │  ├─ pipeline.py                   # Privacy pipeline orchestrator
   │  ├─ presidio_engine.py            # PII/PHI detection + custom Indian recognizers
   │  ├─ guardrails_engine.py          # NeMo policy enforcement
   │  ├─ token_vault.py                # Reversible token mappings for de-anonymization
   │  └─ nemo_config/config.yml         # Wellness-only safety policies
   ├─ services/                        # Business logic (orchestrator, lifestyle, blood reports…)
   ├─ repositories/                    # Data access layer
   ├─ vector/                          # Qdrant clients, embeddings
   ├─ rag/                             # Knowledge ingestion + retrieval
   ├─ cache/                           # Redis / NullCache fallback
   └─ jobs/                            # Background vector sync scheduler
```

---

## ✅ Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (dependency management)
- PostgreSQL (e.g. Neon)
- Docker (for local Qdrant)
- LLM API credentials (OpenAI-compatible — Mesh API supported via `OPENAI_BASE_URL`)
- (Optional) Redis for caching
- (Optional) LangSmith for agent tracing

---

## 🚀 Quick Start

### 1) Configure environment

```powershell
copy .env.example .env
```

Set at minimum:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname?sslmode=require
SESSION_SECRET=generate-a-long-random-string
ADMIN_EMAIL=admin@healthpilot.local
ADMIN_PASSWORD=change-me-on-first-run
QDRANT_URL=http://localhost:6333
OPENAI_BASE_URL=https://api.meshapi.ai/v1
OPENAI_API_KEY=rsk_your-key-here
EMBEDDING_MODEL=text-embedding-3-small
```

### 2) Start Qdrant

```powershell
docker run -p 6333:6333 qdrant/qdrant
```

### 3) Install dependencies

```powershell
uv sync
```

### 4) Run database migrations

```powershell
uv run alembic upgrade head
```

### 5) (Optional) Seed data

```powershell
uv run python scripts/seed_products.py
uv run python scripts/seed_rag.py
```

### 6) Run the app

```powershell
uv run python app.py
```

| Resource | URL |
|----------|-----|
| **Frontend** | http://localhost:8000/ |
| **Swagger** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |

On startup you should see readiness lines for **Presidio**, **NeMo Guardrails**, **PostgreSQL**, **Qdrant**, and **Redis**. The admin user is bootstrapped from `ADMIN_EMAIL` / `ADMIN_PASSWORD` if none exists.

For phase-by-phase setup (events, recommendations, lifestyle, blood reports), see [docs/RUN.md](docs/RUN.md).

---

## 🏗️ System Architecture

HealthPilot is built as a **behavior-driven recommendation engine** with a **privacy-enforced AI layer**. Data flows through four major subsystems:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER (Browser)                                 │
│   Browse · Search · Daily check-in · Upload lab report · Give feedback      │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │   Jinja2 + JavaScript UI    │
                    │   (event-tracker.js)        │
                    └──────────────┬──────────────┘
                                   │ batched events, API calls
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Application                               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────────────────┐  │
│  │ Web pages   │  │ REST API     │  │ Recommendation Orchestrator        │  │
│  │ marketplace │  │ auth, events │  │ triggers · caching · behavior hash │  │
│  │ lifestyle   │  │ products     │  └──────────────────┬─────────────────┘  │
│  │ admin       │  │ recommend.   │                     │                    │
│  └─────────────┘  └──────────────┘                     │                    │
└─────────────────────────────────────────────────────────┼────────────────────┘
                                                          │
         ┌────────────────────────────────────────────────┼────────────────────┐
         │                                                │                    │
         ▼                                                ▼                    ▼
   PostgreSQL                                         LangGraph              Qdrant
   (structured data)                              (agent workflows)      (vector search)
         │                                                │                    │
         │  users · products · events                     │                    │  product embeddings
         │  recommendations · feedback                    │                    │  RAG knowledge chunks
         │  health_profiles · blood_reports               │                    │  user memory vectors
         │  biomarkers (JSON fields)                      │                    │
         └────────────────────────────────────────────────┴────────────────────┘
                                                          │
                                                          ▼
                                              ┌───────────────────────┐
                                              │   Privacy Pipeline    │
                                              │ Presidio → NeMo → LLM │
                                              │ → NeMo → Presidio     │
                                              └───────────┬───────────┘
                                                          │
                                                          ▼
                                                   External LLM
                                                  (Mesh API / OpenAI)
```

---

## 🔄 How It Works — End to End

### Phase 1 — Marketplace & dual-write catalog

Admins create wellness products (courses, programs, guides). Each product is stored in **PostgreSQL** and embedded into **Qdrant** for semantic search. A background scheduler retries failed vector syncs so both stores stay aligned.

```text
Admin creates product
        ↓
PostgreSQL INSERT  +  Qdrant UPSERT (embedding)
        ↓
Public marketplace (search, filter, detail pages)
```

### Phase 2 — Behavioral event tracking

The frontend tracks meaningful interactions (views, searches, scroll depth, return visits). Events are **queued, throttled, and batched** — not sent on every scroll tick — then persisted to PostgreSQL.

```text
User action → client queue → throttle/batch → POST /events/batch → PostgreSQL
```

Anonymous users get a session cookie (`hp_anon_session`); logged-in users link events to their `user_id`.

### Phase 3 — Agentic recommendations

When behavior changes meaningfully (new search topic, category deep-dive, product return visit), the **Recommendation Orchestrator** invokes a **LangGraph workflow**:

```text
START
  → load_context          (recent events, health snapshot, settings)
  → behavior_agent        (summarize intent: primary interest, engagement level)
  → memory_agent          (retrieve/update long-term user memory from Qdrant)
  → retrieval_agent       (semantic product search + RAG knowledge retrieval)
  → evaluation_agent      (re-rank candidates by relevance, behavior fit, price)
  → recommendation_agent  (pick primary + secondary product, confidence, reason)
  → persuasion_agent      (generate personalized narrative — privacy pipeline)
  → store_recommendation  (PostgreSQL + Redis cache)
END
```

**AI efficiency controls** prevent runaway LLM costs:

| Mechanism | Purpose |
|-----------|---------|
| **Trigger detection** | Only run agents on meaningful behavior shifts |
| **Cooldown window** | Minimum gap between automatic recommendation runs |
| **Behavior hash** | Skip regeneration when events + health context unchanged |
| **Recommendation TTL** | Serve cached results until behavior materially changes |
| **Redis cache** | Fast lookup of latest recommendation per user/session |

Users can also manually refresh recommendations or record **Interested / Not for me** feedback, which feeds future memory updates.

### Phase 4 — Health signals (optional)

Logged-in users can submit a **daily lifestyle check-in** (sleep, steps, water, mood, screen time) and optionally upload a **blood report PDF**.

```text
Daily check-in → lifestyle_daily_logs + health_profiles (PostgreSQL)
              → de-identified memory snippet → Qdrant user memory

Blood report PDF → local file storage + extraction agent
                → biomarkers as structured JSON in PostgreSQL
                → wellness summary through privacy pipeline
                → de-identified memory snippet → Qdrant
```

**Critical design choice:** biomarkers (HbA1c, Vitamin D, LDL, etc.) are stored and passed to the LLM as **structured fields only**. Raw OCR text from lab reports **never** crosses the external LLM boundary.

---

## 🔒 Data Security — PII, PHI & the Privacy Pipeline

HealthPilot handles sensitive wellness data. Security is enforced in **code**, not only in prompts.

### The external LLM boundary

The **external LLM boundary** is the point where text leaves HealthPilot infrastructure and reaches a third-party model provider (Mesh API). **All free text must be de-identified before crossing this boundary.**

```text
                    HealthPilot infrastructure          │  Third party
                                                        │
User text ──► Presidio mask ──► NeMo input ──► LLM ──► NeMo output ──► Presidio restore ──► User
                                                        │
                              ▲                         │
                              └── biomarkers as         │
                                  structured JSON only ─┘
```

### Tiered data handling

| Data type | Storage | Sent to external LLM? |
|-----------|---------|----------------------|
| Names, phones, emails, Aadhaar, lab IDs | Masked via Presidio token vault | **No** — replaced with `{{PERSON_1}}`, `{{IN_PHONE_1}}`, etc. |
| Biomarkers (HbA1c, Vitamin D, LDL…) | PostgreSQL JSON fields | **Yes** — as structured data only, never raw report text |
| Chat, persuasion context, OCR narrative | Presidio-de-identified | Token placeholders only |
| Behavioral events | PostgreSQL (product IDs, event types) | Aggregated summaries — no raw PII in agent prompts |

### Presidio — PII/PHI detection & de-identification

[Presidio](https://microsoft.github.io/presidio/) runs **embedded in-process** inside the FastAPI backend. It is responsible for **entity detection and token vault de-anonymization** — not conversational policy.

**What it does:**

1. Detects PII/PHI entities using spaCy NER + custom pattern recognizers
2. Replaces identifiers with reversible tokens (e.g. `{{PERSON_1}}`)
3. Stores mappings in a **session-scoped token vault**
4. Restores original identifiers in the final response **only after** output guardrails pass

**Custom recognizers for Indian context:**

| Entity | Examples detected |
|--------|-------------------|
| `IN_PHONE` | Indian mobile numbers (+91 / 10-digit) |
| `IN_AADHAAR` | Aadhaar numbers |
| `LAB_PATIENT_ID` | Lab / sample / patient IDs on pathology reports |
| `MEDICAL_RECORD_NUMBER` | MRN, UHID, IPD, OPD numbers |

**Example flow:**

```text
User input:
  "Hi, I'm Alex. What sleep programs would help me improve my rest?"

After Presidio (sent to LLM):
  "Hi, I'm {{PERSON_1}}. What sleep programs would help me improve my rest?"

After de-anonymization (returned to user):
  "Hi Alex, a consistent bedtime routine and sleep-focused programs can help. Based on your interest in sleep programs…"
```

**Failure behavior:** If Presidio is unavailable, **all external LLM calls are blocked**. There is no fallback that sends raw PII to the model provider.

### NeMo Guardrails — wellness-only safety policies

[NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) runs **embedded in-process** and enforces **programmable safety policies**. It handles conversational policy and blocking — entity detection is Presidio's job.

Config: `src/healthPilot/privacy/nemo_config/config.yml`

**Allowed:**

- Lifestyle and wellness coaching
- General wellness relevance of biomarkers ("your Vitamin D is on the lower side")
- Educational context from the RAG knowledge base

**Blocked:**

- Diagnosis requests ("Do I have diabetes?")
- Prescription or dosage advice
- Emergency medical triage (redirect to emergency services)
- Harmful, illegal, or abusive content
- Claims that replace a healthcare professional

**Rail placement:**

```text
Input rail  → at graph entry, validates de-identified user text before LLM call
Output rail → on user-facing agents only (recommendation, persuasion, coach, report summaries)
Skipped     → internal agents (retrieval, scoring, memory) when user_facing: false
```

Blocked content returns a **safe refusal** — never unvalidated LLM output.

**Failure behavior:** If NeMo is unavailable on a **user-facing** path, the response is blocked. Internal non-user-facing agent steps may proceed without output rails.

### Privacy pipeline — fixed, mandatory sequence

Every user-facing LLM call follows this **non-optional** order:

```text
Presidio (mask PII)
      ↓
NeMo Guardrails (input validation)
      ↓
External LLM (Mesh API) + structured biomarkers
      ↓
NeMo Guardrails (output validation)
      ↓
Presidio (de-anonymize from token vault)
      ↓
User-facing response
```

Implemented as:

- `PrivacyPipeline` class in `privacy/pipeline.py` — used by recommendation and coach services
- LangGraph coach graph in `agents/graph.py` — dedicated node topology with error routing

```text
START → presidio_deidentify → guardrail_input → llm_call
      → guardrail_output → presidio_deanonymize → END
```

**Key guarantees:**

- Guardrails and the LLM **never** see raw PII
- De-anonymization runs **only after** output guardrails pass
- Biomarkers enter prompts as structured fields, not as raw report OCR text

### Application security

| Control | Implementation |
|---------|----------------|
| Authentication | Session cookies (`SESSION_SECRET`), bcrypt password hashing |
| Authorization | Role-based access (user vs admin), user-owned health data |
| Secrets | `.env` only — never committed (see `.gitignore`) |
| File uploads | Size limits, local storage with access control for blood reports |
| CORS | Configurable `ALLOWED_ORIGINS` |
| Data minimization | Store only what recommendations need; session-scoped token vaults |

---

## 🔁 Continuous Learning Loop

HealthPilot does not start from zero on every visit. Recommendations improve over time:

```text
OBSERVE (events, check-ins, reports)
      ↓
UNDERSTAND (behavior agent → intent summary)
      ↓
RETRIEVE (products + RAG + user memory from Qdrant)
      ↓
RECOMMEND + PERSUADE (privacy pipeline → user)
      ↓
OBSERVE RESPONSE (feedback: interested / not for me / click)
      ↓
UPDATE MEMORY (Qdrant user memory vectors)
      ↓
RECOMMEND BETTER  ↺
```

---

## 🛡️ Responsible AI

HealthPilot is a **wellness recommendation platform**, not a medical diagnosis system.

> HealthPilot AI provides educational and wellness-oriented recommendations based on information you provide. It does not diagnose medical conditions, prescribe medication, or replace professional medical advice.

Safety is enforced at three layers:

1. **Presidio** — strips direct identifiers before text reaches any external model
2. **NeMo Guardrails** — blocks diagnosis, prescription, and emergency-triage requests on input and output
3. **Structured biomarkers** — allow wellness context without sending raw lab report text to the LLM

---

## 📚 Further Reading

| Document | Description |
|----------|-------------|
| [docs/RUN.md](docs/RUN.md) | Step-by-step run guide for all phases |
| [docs/Project Idea.md](docs/Project%20Idea.md) | Full product vision and design rationale |
| [CONTEXT.md](CONTEXT.md) | Glossary (PII, PHI, privacy pipeline, de-anonymization) |

