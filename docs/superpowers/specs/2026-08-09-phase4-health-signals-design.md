# HealthPilot Phase 4: Health Signals & Personalization Design

**Date:** 2026-08-09  
**Status:** Approved  
**Scope:** Daily lifestyle survey (required), optional blood report upload/analysis, Qdrant user memory vectors, recommendation pipeline integration  
**Depends on:** Phase 1 (foundation), Phase 2 (events + marketplace UI), Phase 3 (recommendation agents)

---

## Decisions

| Decision | Choice |
|---|---|
| Lifestyle source | Manual daily survey (no Fit/Apple Health in Phase 4) |
| Survey cadence | **Once per day** — one `lifestyle_daily_logs` row per user per calendar day |
| Duplicate same day | Upsert (update existing row for that `log_date`; no multiple rows per day) |
| Blood reports | **Fully optional** — users never required to upload; pipeline, recommendations, and daily check-in work without any report |
| Blood report feature | Opt-in PDF/image upload → structured biomarker extraction when user chooses |
| Memory architecture | Postgres `user_memories` (profile summary) **+** Qdrant `healthpilot_user_memories` (semantic episodic recall) |
| Auth for health data | **Login required** — lifestyle logs and blood reports are user-owned only (no anonymous session data) |
| Timezone for `log_date` | User's browser-local calendar date sent as `log_date` (ISO `YYYY-MM-DD`); server stores as `DATE` |
| Triggers | Survey complete, blood report parsed, significant 7-day lifestyle trend change |
| Out of scope | Wearable OAuth, proactive email digest, admin RAG upload UI, mandatory blood report onboarding |

---

## Optional vs required personalization

| Signal | Required? | Role |
|---|---|---|
| Daily lifestyle survey | **Encouraged** (core Phase 4 UX) | Primary health input; drives `lifestyle_fit` scoring and memory snippets |
| Blood report upload | **Optional** | Extra personalization layer when user opts in; never blocks other features |
| Marketplace behavior (Phase 2/3) | Automatic | Still works for anonymous and logged-in users without any health data |

The platform must deliver useful recommendations with **zero** blood reports. Upload only enriches scoring when `blood_report_summary` is present.

---

## Phase 4 Scope

### In scope (required)

- Tables: `lifestyle_daily_logs`, `health_profiles`
- Alembic migration `004_health_signals`
- Daily lifestyle survey (6–8 questions) — web UI + API (**core Phase 4 deliverable**)
- Rolling 7-day aggregates in `health_profiles`

### In scope (optional feature)

- Table: `blood_reports` — only populated when a user opts in and uploads
- Blood report upload (PDF/image), OCR/extraction agent, structured `extracted_data`
- Qdrant collection `healthpilot_user_memories` — embed memory snippets on write
- Extend recommendation LangGraph: lifestyle + biomarker context, Qdrant memory retrieval
- New evaluation dimensions: `lifestyle_fit`, `biomarker_relevance`
- New conservative triggers after survey submit and report parse
- `/lifestyle` daily check-in page (required)
- `/health/reports` upload page (optional feature — discoverable but not prompted on every flow)
- API: lifestyle CRUD (daily), health profile read; blood report endpoints only used when user uploads

### Out of scope (Phase 5+)

- Fit / Apple Health / Google Fit sync
- Proactive email / scheduled digest delivery
- Admin RAG document upload UI
- Coach chat / conversational wellness agent
- Medical diagnosis, prescriptions, or treatment claims

---

## Architecture

### New modules

```text
src/healthPilot/
├── agents/
│   └── blood_report_agent.py      # OCR → structured biomarkers (internal LLM)
├── services/
│   ├── lifestyle_service.py       # daily log upsert, aggregates, trend detection
│   ├── health_profile_service.py  # rolling averages read/write
│   ├── blood_report_service.py    # upload, extract, store
│   └── user_memory_vector_service.py  # Qdrant snippet write + semantic search
├── models/
│   ├── lifestyle_daily_log.py
│   ├── health_profile.py
│   └── blood_report.py
├── repositories/
│   ├── lifestyle_repository.py
│   ├── health_profile_repository.py
│   └── blood_report_repository.py
├── vector/
│   └── qdrant_user_memory.py      # healthpilot_user_memories collection
├── api/endpoints/
│   ├── lifestyle.py
│   └── blood_reports.py
└── web/
    ├── lifestyle.py               # /lifestyle daily check-in
    └── health_reports.py          # /health/reports upload + list

uploads/blood_reports/             # local file storage (gitignored)
```

### Data flow

```text
User submits daily survey
        ↓
LifestyleService.upsert_daily_log(log_date, responses)
        ↓
Postgres: lifestyle_daily_logs (unique user_id + log_date)
        ↓
HealthProfileService.recompute_aggregates(user_id)
        ↓
UserMemoryVectorService.write_snippet(type=lifestyle_daily)
        ↓
TriggerService → RecommendationOrchestrator (if rules match)

User uploads blood report (OPTIONAL — skip entirely if user never uploads)
        ↓
BloodReportService.store_file() → Postgres blood_reports (status=pending)
        ↓
BloodReportAgent.extract() → extracted_data JSONB (no raw OCR to user-facing LLM)
        ↓
UserMemoryVectorService.write_snippet(type=blood_report)
        ↓
Trigger → recommendation pipeline

Users with zero blood reports: pipeline uses lifestyle + behavior only (Phase 3 + lifestyle).
```

### Recommendation pipeline extension

```text
Event / survey / report / manual refresh
        ↓
RecommendationOrchestrator
        ↓
recommendation_graph.invoke(RecommendationState)
        ↓
load_context      + lifestyle snapshot + latest blood report summary (null if none uploaded)
behavior_agent    + lifestyle gaps in summary (e.g. low sleep avg)
memory_agent      + Postgres profile + Qdrant top-K memory snippets
retrieval_agent   + query enriched with lifestyle/biomarker keywords
evaluation_agent  + lifestyle_fit + biomarker_relevance scoring
recommendation_agent / persuasion_agent (privacy pipeline on user-facing text)
store_recommendation
```

---

## Daily Lifestyle Survey

### Cadence rule

- **One row per user per calendar day** — enforced by unique constraint `(user_id, log_date)`.
- Submitting again on the same `log_date` **updates** the existing row (`updated_at` changes).
- Missing days are simply absent rows — aggregates use available days only.

### Survey questions (v1 — 8 fields)

| Field | Type | Validation | Maps to aggregate |
|---|---|---|---|
| `sleep_hours` | float | 0–24, step 0.5 | `health_profiles.sleep_average` |
| `water_glasses` | int | 0–20 | `health_profiles.water_average` |
| `activity_level` | enum | `sedentary`, `light`, `moderate`, `active` | `health_profiles.activity_average` (numeric mapping) |
| `screen_hours` | float | 0–24 | `health_profiles.screen_time_average` |
| `mood` | int | 1–5 | `health_profiles.mood_average` |
| `stress` | int | 1–5 | `health_profiles.stress_average` |
| `energy` | int | 1–5 | `health_profiles.energy_average` |
| `notes` | string | max 500 chars, optional | not aggregated; may become memory snippet |

`activity_level` numeric mapping for averages: sedentary=1, light=2, moderate=3, active=4.

### UI — `/lifestyle`

- Shown only to logged-in users.
- If today's log exists: pre-fill form with current values (edit mode).
- If not: empty form (create mode).
- Submit → `POST /api/v1/lifestyle/daily` with `{ "log_date": "2026-08-09", "responses": { ... } }`.
- After submit: toast + optional link to `/recommendations` if trigger fired.
- Nav link: **Daily Check-in** (visible when logged in).

---

## Data Model

### `lifestyle_daily_logs`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK) | Required; `users.id` |
| `log_date` | DATE | Calendar date from client (`YYYY-MM-DD`) |
| `responses` | JSONB | Survey answers (schema above) |
| `created_at` | TIMESTAMPTZ | First submission |
| `updated_at` | TIMESTAMPTZ | Last edit same day |

**Unique:** `(user_id, log_date)`

### `health_profiles`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK, unique) | One profile per user |
| `sleep_average` | NUMERIC(4,1) | 7-day rolling avg |
| `water_average` | NUMERIC(4,1) | 7-day rolling avg (glasses) |
| `activity_average` | NUMERIC(3,2) | 7-day rolling (1–4 scale) |
| `screen_time_average` | NUMERIC(4,1) | 7-day rolling avg |
| `mood_average` | NUMERIC(3,2) | 7-day rolling avg |
| `stress_average` | NUMERIC(3,2) | 7-day rolling avg |
| `energy_average` | NUMERIC(3,2) | 7-day rolling avg |
| `metadata` | JSONB | e.g. `{ "days_in_window": 5, "trend_alerts": [...] }` |
| `updated_at` | TIMESTAMPTZ | |

Recomputed on every daily log upsert from last 7 calendar days of `lifestyle_daily_logs`.

### `blood_reports`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK) | Required |
| `file_name` | VARCHAR(255) | Original filename |
| `file_path` | VARCHAR(512) | Server-relative path under `uploads/blood_reports/` |
| `mime_type` | VARCHAR(100) | `application/pdf`, `image/jpeg`, `image/png` |
| `status` | ENUM | `pending`, `processing`, `completed`, `failed` |
| `extracted_data` | JSONB | Structured biomarkers (see below) |
| `upload_date` | TIMESTAMPTZ | |
| `processed_at` | TIMESTAMPTZ | Nullable |
| `last_error` | TEXT | Nullable |

### `extracted_data` schema (example)

```json
{
  "biomarkers": {
    "hba1c": 6.2,
    "vitamin_d": 14,
    "ldl": 162,
    "hdl": 38,
    "triglycerides": 230
  },
  "flags": ["vitamin_d_low", "ldl_elevated"],
  "report_date": "2026-07-15"
}
```

- Raw OCR text stored **only** in processing temp buffer — **not** persisted or sent to external LLM.
- Extraction uses internal agent with structured output; user-facing summary runs through privacy pipeline.

### Alembic migration `004_health_signals`

Creates `lifestyle_daily_logs`, `health_profiles`, `blood_reports`, and `blood_report_status` enum.

---

## Qdrant User Memory Vectors

### Collection: `healthpilot_user_memories`

| Field | Purpose |
|---|---|
| Point ID | UUID (deterministic from `source_type:source_id` for idempotent upsert) |
| Vector | Mesh embedding of de-identified memory text |
| Payload `user_id` | Filter — retrieval scoped to current user only |
| Payload `memory_type` | `lifestyle_daily`, `lifestyle_trend`, `blood_report`, `behavior`, `feedback` |
| Payload `source_id` | FK to originating row |
| Payload `text` | Human-readable snippet for agent context |
| Payload `created_at` | ISO timestamp |

### When to write snippets

| Event | Snippet example |
|---|---|
| Daily survey upsert | `"Daily check-in 2026-08-09: sleep 5h, stress 4/5, mood 2/5, activity light"` |
| 7-day trend alert | `"7-day trend: sleep declining from 7.0h to 5.3h average; stress rising"` |
| Blood report completed | `"Blood report 2026-07-15: Vitamin D low (14), LDL elevated (162)"` |
| Recommendation feedback `completed` | `"User completed Sleep Better in 21 Days — positive outcome"` |

### When to read snippets

In `memory_agent_node`:

1. Load Postgres `user_memories` profile (unchanged).
2. Build query from `behavior_summary` + `health_profile` + latest biomarker flags.
3. `UserMemoryVectorService.search(user_id, query, limit=5)`.
4. Merge into `state["user_memory"]["episodic_memories"]` for downstream agents.

Postgres remains **source of truth**; Qdrant is **semantic recall** for relevant history without loading 90 days of logs into every run.

### Privacy

- No name, email, or raw report text in vectors.
- Biomarkers as generalized phrases ("Vitamin D below typical wellness range").
- `user_id` in payload for filtering only — not embedded in vector text.

---

## LangGraph State Extensions

```python
class RecommendationState(TypedDict, total=False):
    # ... existing Phase 3 fields ...
    lifestyle_snapshot: dict[str, Any]   # today's log + 7-day profile averages
    blood_report_summary: dict[str, Any] | None  # latest completed report flags
    episodic_memories: list[dict[str, Any]]      # Qdrant retrieval results
```

`memory_agent_node` populates `episodic_memories`. `load_context_node` loads lifestyle + blood report.

---

## Evaluation Agent Extensions

### Without blood report (default for most users)

Lifestyle signals only — `biomarker_relevance` is **omitted** (not neutral-penalized). Weights redistribute:

```text
final_score = (
  0.33 * semantic_relevance
  + 0.22 * behavior_match
  + 0.13 * memory_boost
  + 0.11 * price_fit
  + 0.09 * engagement_signal
  + 0.12 * lifestyle_fit        # lifestyle is the primary health signal
)
```

### With blood report (opt-in users only)

Add biomarker dimension; lifestyle weight slightly reduced:

```text
final_score = (
  0.30 * semantic_relevance
  + 0.20 * behavior_match
  + 0.12 * memory_boost
  + 0.10 * price_fit
  + 0.08 * engagement_signal
  + 0.10 * lifestyle_fit
  + 0.10 * biomarker_relevance  # only applied when user has ≥1 completed report
)
```

### `lifestyle_fit` (0.0–1.0)

Rule-based mapping, e.g.:

- `sleep_average < 6` → boost `sleep` category products
- `stress_average >= 4` → boost `mental_wellness`
- `activity_average < 2` → boost `fitness`

### `biomarker_relevance` (0.0–1.0)

**Only computed when user has uploaded at least one completed blood report.** If no report exists, this term is excluded entirely (see weight redistribution above).

Rule-based from `flags` in latest report, e.g.:

- `vitamin_d_low` → boost `nutrition` products mentioning vitamins/supplements in metadata
- No report → dimension skipped; recommendations unchanged vs Phase 3 + lifestyle

---

## Trigger Rules (Phase 4 additions)

Evaluated after lifestyle submit or blood report processing (respects existing 5-min cooldown):

| Trigger | Condition |
|---|---|
| Manual | `POST /api/v1/recommendations/refresh` — unchanged |
| Daily survey | First submit of the day OR responses changed materially (any numeric field delta ≥ 1) |
| Blood report | `status` transitions to `completed` |
| Lifestyle trend | 7-day `sleep_average` drops ≥ 1.0h vs prior 7-day window (computed on upsert) |
| Phase 3 triggers | search, product_return, category interest — unchanged |

**Skip pipeline if:** same as Phase 3 (cooldown, behavior_hash unchanged, no recent activity).

`behavior_hash` extended to include lifestyle profile hash; includes latest blood report id **only if** user has uploaded one, so health changes invalidate cache without requiring a report.

---

## API Endpoints

### Lifestyle — `/api/v1/lifestyle`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/daily/today` | Required | Today's log for current user (or 404) |
| GET | `/daily` | Required | List logs; query `from`, `to` date range (max 90 days) |
| POST | `/daily` | Required | Upsert daily log `{ log_date, responses }` |
| GET | `/profile` | Required | Current `health_profiles` aggregates |

### Blood reports — `/api/v1/blood-reports`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/` | Required | Multipart upload (PDF/JPEG/PNG, max 10 MB) |
| GET | `/` | Required | List user's reports (metadata only) |
| GET | `/{report_id}` | Required | Single report + `extracted_data` + user-facing summary |
| DELETE | `/{report_id}` | Required | Delete report + file + Qdrant memory points for that source |

Processing runs as background task after upload (same pattern as event batch → recommendation trigger).

---

## Web UI

### `/lifestyle` — Daily Check-in

- Form with 8 survey fields.
- Shows 7-day averages summary card from `GET /lifestyle/profile`.
- Streak indicator (consecutive days with logs) — optional nice-to-have.

### `/health/reports` — Blood Reports (optional)

- **Not required** for recommendations or daily check-in.
- Soft intro copy: "Optional — upload a lab report for deeper personalization."
- Upload dropzone (PDF/image) — user-initiated only; no modal prompts or onboarding gates.
- List of past reports with status badges (empty state: "No reports uploaded — this is optional").
- Completed reports: structured biomarker table + wellness-oriented summary (privacy pipeline).
- Disclaimer: not a diagnostic tool; consult a healthcare professional.

### Nav

- Logged-in users: **Daily Check-in** (primary health entry point)
- **Health Reports** — secondary nav link or under a "Personalization" submenu; never shown as a required step
- Homepage widget: if user has not checked in today, subtle CTA "Complete today's check-in" (not blood report)
- Optional one-line link on `/lifestyle` or `/recommendations`: "Want deeper personalization? Upload a blood report (optional)"

---

## Blood Report Agent

### Responsibilities

- Accept file bytes (PDF or image).
- OCR via library (e.g. `pymupdf` for PDF, `pytesseract` or vision model for images) — **internal only**.
- Parse biomarkers into structured JSON via internal LLM (structured output, `user_facing: false`).
- Set `blood_reports.status` → `completed` or `failed`.
- Generate user-facing summary through privacy pipeline (`user_facing: true`).

### Safety constraints (from Project Idea)

- Extract and present values; explain general wellness relevance.
- Do NOT diagnose, prescribe, or claim medical certainty.
- Encourage professional consultation when flags are present.

---

## Configuration (`.env` additions)

```env
# User memory vectors
USER_MEMORY_COLLECTION=healthpilot_user_memories
USER_MEMORY_RETRIEVAL_K=5

# Lifestyle
LIFESTYLE_AGGREGATE_WINDOW_DAYS=7
LIFESTYLE_TREND_SLEEP_DELTA_HOURS=1.0

# Blood reports
BLOOD_REPORT_UPLOAD_DIR=uploads/blood_reports
BLOOD_REPORT_MAX_BYTES=10485760
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Survey submit without login | 401 |
| Duplicate `log_date` | Upsert (200), not 409 |
| Invalid `log_date` (future) | 422 — reject dates > today in user's submitted date |
| Blood report too large | 413 |
| OCR/extraction failure | `status=failed`, `last_error` set; no recommendation trigger |
| Qdrant down on memory write | Log warning; Postgres data still saved; skip vector upsert |
| Qdrant down on memory read | Fall back to Postgres profile only |
| No lifestyle data yet | Pipeline runs as Phase 3 (health fields null) |
| No blood report uploaded | Normal — `blood_report_summary` null; biomarker scoring skipped; no UI prompts to upload |

---

## Testing

| Layer | Coverage |
|---|---|
| Unit | Lifestyle upsert uniqueness, aggregate computation, trend detection |
| Unit | Evaluation `lifestyle_fit` / `biomarker_relevance` scoring |
| Unit | Memory snippet text generation (no PII) |
| Unit | `behavior_hash` includes health signal changes |
| Integration | POST daily log → health_profile updated → Qdrant snippet written |
| Integration | Blood report upload → extraction mocked → trigger fires |
| Integration | Memory agent retrieves filtered Qdrant results by user_id |
| Manual | Logged-in user: check-in → recommendation mentions sleep/stress |
| Manual | Upload sample report → biomarkers displayed → recommendation shifts |

---

## Completion Criteria

- [ ] Migration `004` creates `lifestyle_daily_logs`, `health_profiles`, `blood_reports`
- [ ] Daily survey API + `/lifestyle` page (once-per-day upsert)
- [ ] `health_profiles` recomputed on each daily log
- [ ] Blood report upload + extraction agent + `/health/reports` page
- [ ] Qdrant `healthpilot_user_memories` collection + write on survey/report/feedback
- [ ] Memory agent semantic retrieval from Qdrant
- [ ] Recommendation graph extended with lifestyle + biomarker context
- [ ] New triggers: survey, report complete, sleep trend
- [ ] Privacy pipeline on all user-facing health summaries
- [ ] `docs/RUN.md` updated with Phase 4 setup and demo flow

---

## Demo Flow (Phase 4)

### Primary path (no blood report — validates optional design)

1. Log in as Rahul.
2. Browse marketplace (Phase 2/3 events accumulate).
3. Visit `/lifestyle` — complete daily check-in (low sleep, high stress).
4. Background trigger → `/recommendations` updates with sleep/stress-aware message.
5. Next day: edit today's check-in (upsert same `log_date`) — aggregates and memory snippet update.
6. Confirm: full recommendation quality without ever visiting `/health/reports`.

### Optional path (blood report opt-in)

7. Visit `/health/reports` — upload blood report PDF (user choice).
8. View extracted biomarkers + wellness summary.
9. Refresh recommendations — evaluation additionally boosts products based on biomarker flags.

---

## Route Registration

```text
GET  /lifestyle                    → web/lifestyle (check-in page)
POST /lifestyle                    → web/lifestyle (form submit)
GET  /health/reports               → web/health_reports (list + upload)
POST /health/reports               → web/health_reports (form upload)
GET  /api/v1/lifestyle/daily/today
GET  /api/v1/lifestyle/daily
POST /api/v1/lifestyle/daily
GET  /api/v1/lifestyle/profile
POST /api/v1/blood-reports
GET  /api/v1/blood-reports
GET  /api/v1/blood-reports/{id}
DELETE /api/v1/blood-reports/{id}
```

Existing Phase 3 routes unchanged.
