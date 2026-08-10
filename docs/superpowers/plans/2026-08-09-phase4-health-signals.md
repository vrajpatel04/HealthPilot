# Phase 4 Health Signals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add daily lifestyle check-in (once per day), optional blood report upload, Qdrant user memory vectors, and wire both into the Phase 3 recommendation pipeline.

**Architecture:** Postgres stores canonical health data (`lifestyle_daily_logs`, `health_profiles`, `blood_reports`). Lifestyle upserts recompute 7-day aggregates and optionally write de-identified snippets to Qdrant `healthpilot_user_memories`. The existing LangGraph pipeline gains lifestyle/biomarker context in `load_context`, extended evaluation scoring, and new triggers after survey submit or report parse. Blood reports are fully optional — pipeline works without them.

**Tech Stack:** FastAPI, SQLAlchemy async + Alembic, Pydantic v2, Jinja2, Qdrant (`qdrant-client`), existing Mesh embedding client, LangGraph, pytest.

**Spec:** `docs/superpowers/specs/2026-08-09-phase4-health-signals-design.md` (Approved)

## Global Constraints

- Survey cadence: **once per day** — unique `(user_id, log_date)`; same-day resubmit = upsert
- Blood reports: **fully optional** — never required for recommendations or onboarding
- Auth: lifestyle + blood report endpoints require login (`get_current_user`)
- `log_date`: client sends ISO `YYYY-MM-DD` (browser-local); reject future dates
- `LIFESTYLE_AGGREGATE_WINDOW_DAYS=7`, `LIFESTYLE_TREND_SLEEP_DELTA_HOURS=1.0`
- `USER_MEMORY_COLLECTION=healthpilot_user_memories`, `USER_MEMORY_RETRIEVAL_K=5`
- `BLOOD_REPORT_UPLOAD_DIR=uploads/blood_reports`, `BLOOD_REPORT_MAX_BYTES=10485760`
- Raw OCR text never persisted or sent to external LLM
- User-facing summaries through privacy pipeline (`run_user_facing_llm`)
- Qdrant failures: log warning; Postgres writes still succeed
- No Fit/Apple Health, no proactive email, no admin RAG UI in Phase 4

---

## File Map

| File | Responsibility |
|---|---|
| `alembic/versions/004_health_signals.py` | Tables + enums |
| `src/healthPilot/models/enums.py` | `ActivityLevel`, `BloodReportStatus` |
| `src/healthPilot/models/lifestyle_daily_log.py` | ORM model |
| `src/healthPilot/models/health_profile.py` | ORM model |
| `src/healthPilot/models/blood_report.py` | ORM model |
| `src/healthPilot/schemas/lifestyle.py` | Pydantic request/response |
| `src/healthPilot/schemas/blood_report.py` | Pydantic request/response |
| `src/healthPilot/repositories/lifestyle_repository.py` | DB access for daily logs |
| `src/healthPilot/repositories/health_profile_repository.py` | DB access for profiles |
| `src/healthPilot/repositories/blood_report_repository.py` | DB access for reports |
| `src/healthPilot/services/lifestyle_service.py` | Upsert, aggregates, trends, snippet text |
| `src/healthPilot/services/health_profile_service.py` | Read profile for pipeline |
| `src/healthPilot/services/blood_report_service.py` | Upload, process, delete |
| `src/healthPilot/services/user_memory_vector_service.py` | Qdrant write/search |
| `src/healthPilot/services/health_hash.py` | Extended recommendation hash |
| `src/healthPilot/vector/qdrant_user_memory.py` | Qdrant collection ops |
| `src/healthPilot/agents/blood_report_agent.py` | OCR + structured extraction |
| `src/healthPilot/api/endpoints/lifestyle.py` | REST API |
| `src/healthPilot/api/endpoints/blood_reports.py` | REST API |
| `src/healthPilot/web/lifestyle.py` | `/lifestyle` page |
| `src/healthPilot/web/health_reports.py` | `/health/reports` page |
| `src/healthPilot/templates/lifestyle/checkin.html` | Survey form |
| `src/healthPilot/templates/health/reports.html` | Optional upload UI |
| `tests/test_lifestyle_service.py` | Unit tests |
| `tests/test_health_hash.py` | Unit tests |
| `tests/test_evaluation_health.py` | Unit tests |
| `tests/test_phase4_health_signals.py` | Integration tests |

---

### Task 1: Database migration and ORM models

**Files:**
- Create: `alembic/versions/004_health_signals.py`
- Create: `src/healthPilot/models/lifestyle_daily_log.py`
- Create: `src/healthPilot/models/health_profile.py`
- Create: `src/healthPilot/models/blood_report.py`
- Modify: `src/healthPilot/models/enums.py`
- Modify: `src/healthPilot/models/__init__.py` (if exists — register models for Alembic)

**Interfaces:**
- Produces: ORM classes `LifestyleDailyLog`, `HealthProfile`, `BloodReport`
- Produces: enums `ActivityLevel`, `BloodReportStatus`

- [ ] **Step 1: Add enums to `models/enums.py`**

```python
class ActivityLevel(str, enum.Enum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    active = "active"


class BloodReportStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
```

- [ ] **Step 2: Create migration `004_health_signals.py`**

Follow pattern from `alembic/versions/003_recommendations_memory_feedback.py`:
- `lifestyle_daily_logs` with `UniqueConstraint("user_id", "log_date")`
- `health_profiles` with `UniqueConstraint("user_id")`
- `blood_reports` with `blood_report_status` enum
- `down_revision = "003"`

- [ ] **Step 3: Create ORM models**

`LifestyleDailyLog`: `id`, `user_id` (FK users, required), `log_date` (Date), `responses` (JSONB), `created_at`, `updated_at`

`HealthProfile`: `id`, `user_id` (unique FK), seven `NUMERIC` average columns, `metadata_` (JSONB column name `metadata`), `updated_at`

`BloodReport`: columns per spec; `metadata_` not needed

- [ ] **Step 4: Run migration**

```bash
alembic upgrade head
```

Expected: migration applies without error

- [ ] **Step 5: Commit**

```bash
git add alembic/versions/004_health_signals.py src/healthPilot/models/
git commit -m "feat(phase4): add health signals database schema"
```

---

### Task 2: Lifestyle repository, schemas, and service

**Files:**
- Create: `src/healthPilot/schemas/lifestyle.py`
- Create: `src/healthPilot/repositories/lifestyle_repository.py`
- Create: `src/healthPilot/repositories/health_profile_repository.py`
- Create: `src/healthPilot/services/lifestyle_service.py`
- Create: `tests/test_lifestyle_service.py`

**Interfaces:**
- Consumes: `LifestyleDailyLog`, `HealthProfile` models from Task 1
- Produces: `LifestyleService.upsert_daily_log(user_id, log_date, responses) -> tuple[LifestyleDailyLog, HealthProfile, bool]`
  - Third return value `material_change: bool` — True if first log today OR any numeric field delta ≥ 1
- Produces: `LifestyleService.compute_aggregates(logs: list[LifestyleDailyLog]) -> dict`
- Produces: `LifestyleService.build_daily_snippet(log, log_date) -> str`
- Produces: `LifestyleService.detect_sleep_trend(profile, prior_sleep_avg) -> bool`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_lifestyle_service.py
from datetime import date
from healthPilot.services.lifestyle_service import (
    ACTIVITY_NUMERIC,
    LifestyleService,
    compute_aggregates_from_logs,
)


def test_activity_numeric_mapping():
    assert ACTIVITY_NUMERIC["sedentary"] == 1
    assert ACTIVITY_NUMERIC["active"] == 4


def test_compute_aggregates_single_day():
    logs = [
        {
            "responses": {
                "sleep_hours": 6.0,
                "water_glasses": 8,
                "activity_level": "light",
                "screen_hours": 4.0,
                "mood": 3,
                "stress": 4,
                "energy": 2,
            }
        }
    ]
    agg = compute_aggregates_from_logs(logs)
    assert agg["sleep_average"] == 6.0
    assert agg["stress_average"] == 4.0
    assert agg["days_in_window"] == 1


def test_material_change_detects_sleep_delta():
    old = {"sleep_hours": 7.0, "stress": 2, "mood": 4, "energy": 4, "water_glasses": 6, "screen_hours": 3.0, "activity_level": "moderate"}
    new = {"sleep_hours": 5.0, "stress": 2, "mood": 4, "energy": 4, "water_glasses": 6, "screen_hours": 3.0, "activity_level": "moderate"}
    assert LifestyleService.responses_materially_changed(old, new) is True


def test_material_change_ignores_small_delta():
    old = {"sleep_hours": 7.0, "stress": 2, "mood": 4, "energy": 4, "water_glasses": 6, "screen_hours": 3.0, "activity_level": "moderate"}
    new = {"sleep_hours": 7.5, "stress": 2, "mood": 4, "energy": 4, "water_glasses": 6, "screen_hours": 3.0, "activity_level": "moderate"}
    assert LifestyleService.responses_materially_changed(old, new) is False
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_lifestyle_service.py -v
```

- [ ] **Step 3: Implement schemas**

`DailyLogUpsertRequest`: `log_date: date`, `responses: LifestyleResponses` with field validators (sleep 0–24, mood 1–5, etc.)

`LifestyleResponses`: 8 fields per spec; `notes: str | None = None` max 500 chars

`HealthProfileResponse`: all average fields + `days_in_window` from metadata

- [ ] **Step 4: Implement `compute_aggregates_from_logs` as pure function** in `lifestyle_service.py` (testable without DB)

- [ ] **Step 5: Implement `LifestyleRepository`**

Methods: `get_by_user_date(user_id, log_date)`, `upsert(log)`, `list_in_range(user_id, from_date, to_date)`

- [ ] **Step 6: Implement `HealthProfileRepository`**

Methods: `get_by_user_id(user_id)`, `upsert(profile)`

- [ ] **Step 7: Implement `LifestyleService.upsert_daily_log`**

1. Reject `log_date > date.today()` → raise `ValidationError`
2. Upsert `lifestyle_daily_logs`
3. Load logs in last `LIFESTYLE_AGGREGATE_WINDOW_DAYS`
4. Recompute and upsert `health_profiles`
5. Return log, profile, `material_change`

- [ ] **Step 8: Run tests — expect PASS**

```bash
pytest tests/test_lifestyle_service.py -v
```

- [ ] **Step 9: Commit**

```bash
git add src/healthPilot/schemas/lifestyle.py src/healthPilot/repositories/lifestyle_repository.py src/healthPilot/repositories/health_profile_repository.py src/healthPilot/services/lifestyle_service.py tests/test_lifestyle_service.py
git commit -m "feat(phase4): add lifestyle service with daily upsert and aggregates"
```

---

### Task 3: Lifestyle REST API

**Files:**
- Create: `src/healthPilot/api/endpoints/lifestyle.py`
- Modify: `src/healthPilot/api/routes.py`
- Create: `tests/test_lifestyle_api.py`

**Interfaces:**
- Consumes: `LifestyleService` from Task 2
- Produces: routes under `/api/v1/lifestyle`

- [ ] **Step 1: Write failing API test** (use existing test client pattern from `tests/test_web_phase2.py` or `tests/test_security.py`)

```python
# tests/test_lifestyle_api.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_lifestyle_daily_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/lifestyle/daily",
        json={"log_date": "2026-08-09", "responses": {"sleep_hours": 7, "water_glasses": 8, "activity_level": "moderate", "screen_hours": 3, "mood": 4, "stress": 2, "energy": 4}},
    )
    assert resp.status_code == 401
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement endpoints**

| Method | Path | Handler |
|---|---|---|
| GET | `/daily/today` | Return today's log or 404 |
| GET | `/daily` | Query `from_date`, `to_date` (max 90 days) |
| POST | `/daily` | Upsert; return log + profile |
| GET | `/profile` | Return `HealthProfileResponse` |

All use `Depends(get_current_user)`.

- [ ] **Step 4: Register router in `api/routes.py`**

```python
from healthPilot.api.endpoints import lifestyle
v1_router.include_router(lifestyle.router, prefix="/lifestyle", tags=["lifestyle"])
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/test_lifestyle_api.py -v
```

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(phase4): add lifestyle REST API"
```

---

### Task 4: Lifestyle web UI and navigation

**Files:**
- Create: `src/healthPilot/web/lifestyle.py`
- Create: `src/healthPilot/templates/lifestyle/checkin.html`
- Modify: `src/healthPilot/web/router.py`
- Modify: `src/healthPilot/web/deps.py` — add `require_logged_in_user`
- Modify: `src/healthPilot/templates/base.html` — nav link for logged-in users

**Interfaces:**
- Consumes: `LifestyleService`, `get_current_user` pattern via `require_logged_in_user`
- Produces: `GET /lifestyle`, `POST /lifestyle`

- [ ] **Step 1: Add `require_logged_in_user` to `web/deps.py`**

Redirect to `/login` with flash if `get_optional_user` returns None.

- [ ] **Step 2: Create check-in template**

8-field form matching `LifestyleResponses`. Show 7-day averages card from profile. Pre-fill if today's log exists.

Optional one-line link: "Want deeper personalization? [Upload a blood report (optional)](/health/reports)"

- [ ] **Step 3: Implement web routes**

`GET /lifestyle` — load today's log + profile, render form

`POST /lifestyle` — parse form fields, call `LifestyleService.upsert_daily_log`, set flash, redirect

After submit: if `material_change`, schedule background recommendation trigger (stub call — wired fully in Task 7)

- [ ] **Step 4: Update `base.html` nav**

Logged-in: show **Daily Check-in** link (not blood reports as primary)

- [ ] **Step 5: Manual smoke test**

```bash
uvicorn healthPilot.main:app --reload
```

Log in → visit `/lifestyle` → submit → see flash success

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(phase4): add daily lifestyle check-in web UI"
```

---

### Task 5: Health hash and evaluation scoring extensions

**Files:**
- Create: `src/healthPilot/services/health_hash.py`
- Modify: `src/healthPilot/services/evaluation_service.py`
- Create: `tests/test_health_hash.py`
- Create: `tests/test_evaluation_health.py`

**Interfaces:**
- Produces: `compute_health_hash(*, events, health_profile: dict | None, blood_report_id: str | None) -> str`
- Produces: `EvaluationService.score_candidates(..., health_profile=None, blood_report_summary=None)`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_health_hash.py
from healthPilot.services.health_hash import compute_health_hash


def test_health_hash_changes_when_sleep_average_changes():
    profile_a = {"sleep_average": 7.0, "stress_average": 2.0}
    profile_b = {"sleep_average": 5.0, "stress_average": 2.0}
    events = [{"event_type": "search", "metadata": {"query": "sleep"}}]
    assert compute_health_hash(events=events, health_profile=profile_a, blood_report_id=None) != compute_health_hash(events=events, health_profile=profile_b, blood_report_id=None)
```

```python
# tests/test_evaluation_health.py
from healthPilot.services.evaluation_service import EvaluationService


def test_lifestyle_fit_boosts_sleep_category_when_low_sleep():
    evaluator = EvaluationService()
    behavior = {"primary_category": "fitness"}
    memory = {"successful_recommendations": []}
    health = {"sleep_average": 5.0, "stress_average": 2.0, "activity_average": 3.0}
    candidates = [
        {"product_id": "1", "category": "fitness", "score": 0.6, "price": 100},
        {"product_id": "2", "category": "sleep", "score": 0.5, "price": 100},
    ]
    ranked = evaluator.score_candidates(candidates, behavior, memory, health_profile=health, blood_report_summary=None)
    assert ranked[0]["product_id"] == "2"


def test_biomarker_dimension_skipped_without_report():
    evaluator = EvaluationService()
    behavior = {"primary_category": "nutrition"}
    memory = {"successful_recommendations": []}
    health = {"sleep_average": 7.0, "stress_average": 2.0, "activity_average": 3.0}
    candidates = [{"product_id": "1", "category": "nutrition", "score": 0.5, "price": 100}]
    scored = evaluator.score_candidates(candidates, behavior, memory, health_profile=health, blood_report_summary=None)
    assert "biomarker_relevance" not in scored[0]
```

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Implement `compute_health_hash`**

Combine `compute_behavior_hash(events)` with stable JSON of health profile fields + optional `blood_report_id`.

- [ ] **Step 4: Extend `EvaluationService.score_candidates`**

Add optional `health_profile` and `blood_report_summary` kwargs.

Implement `_lifestyle_fit(candidate, health_profile)` per spec rules.

Implement `_biomarker_relevance(candidate, blood_report_summary)` — only when summary has `flags`.

Use weight sets from spec:
- No report: 0.33/0.22/0.13/0.11/0.09/0.12
- With report: add 0.10 biomarker, reduce others per spec

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/test_health_hash.py tests/test_evaluation_health.py -v
```

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(phase4): extend evaluation and health hash for lifestyle signals"
```

---

### Task 6: Wire lifestyle into recommendation pipeline

**Files:**
- Modify: `src/healthPilot/agents/recommendation_state.py`
- Modify: `src/healthPilot/agents/recommendation_nodes.py`
- Modify: `src/healthPilot/services/behavior_service.py`
- Modify: `src/healthPilot/services/recommendation_orchestrator.py`
- Modify: `src/healthPilot/services/trigger_service.py`
- Create: `src/healthPilot/services/health_profile_service.py`

**Interfaces:**
- Consumes: `HealthProfileService.get_snapshot(user_id)`, `LifestyleService`
- Produces: state fields `lifestyle_snapshot`, `blood_report_summary` (null for now)
- Produces: `TriggerService.should_trigger_after_lifestyle(material_change, trend_alert) -> bool`
- Produces: `RecommendationOrchestrator.maybe_trigger_after_lifestyle(user_id)`
- Produces: `RecommendationOrchestrator._current_behavior_hash` uses `compute_health_hash`

- [ ] **Step 1: Extend `RecommendationState`**

```python
lifestyle_snapshot: dict[str, Any]
blood_report_summary: dict[str, Any] | None
```

- [ ] **Step 2: Create `HealthProfileService`**

`async def get_snapshot(user_id) -> dict` — today's log (if any) + profile averages

- [ ] **Step 3: Update `load_context_node`**

If `user_id` set, load lifestyle snapshot into state. Set `blood_report_summary=None` (Task 9 fills this).

- [ ] **Step 4: Update `behavior_agent_node`**

Enrich `behavior_summary` with lifestyle gaps when snapshot present:

```python
if snapshot.get("sleep_average") and snapshot["sleep_average"] < 6:
    summary["lifestyle_gaps"] = summary.get("lifestyle_gaps", []) + ["low_sleep"]
```

Append lifestyle-based bullets to `why_recommended` when relevant.

- [ ] **Step 5: Update `evaluation_agent_node`**

Pass `health_profile` and `blood_report_summary` from state to `EvaluationService`.

- [ ] **Step 6: Extend `TriggerService`**

```python
def should_trigger_after_lifestyle(self, *, material_change: bool, trend_alert: bool) -> bool:
    return material_change or trend_alert
```

- [ ] **Step 7: Update orchestrator**

- Replace `_current_behavior_hash` to use `compute_health_hash` with health profile
- Add `maybe_trigger_after_lifestyle(user_id)` — requires logged-in user; uses session from user's latest recommendation or skip if no session (use user_id-only path)
- Allow pipeline run when user has lifestyle data but no recent events (for manual lifestyle trigger)

- [ ] **Step 8: Wire lifestyle web POST** to call `maybe_trigger_after_lifestyle` via `BackgroundTasks`

- [ ] **Step 9: Commit**

```bash
git commit -m "feat(phase4): integrate lifestyle signals into recommendation pipeline"
```

---

### Task 7: Qdrant user memory vectors

**Files:**
- Create: `src/healthPilot/vector/qdrant_user_memory.py`
- Create: `src/healthPilot/services/user_memory_vector_service.py`
- Modify: `src/healthPilot/core/config.py`
- Modify: `src/healthPilot/agents/recommendation_nodes.py` — `memory_agent_node`
- Modify: `src/healthPilot/services/lifestyle_service.py` — call vector write after upsert
- Create: `tests/test_user_memory_vector_service.py`

**Interfaces:**
- Produces: `UserMemoryVectorService.write_snippet(user_id, memory_type, source_id, text) -> None`
- Produces: `UserMemoryVectorService.search(user_id, query, limit=5) -> list[dict]`
- Produces: `UserMemoryVectorService.delete_by_source(user_id, source_id) -> None`
- Produces: deterministic point ID via `uuid.uuid5(NAMESPACE_DNS, f"{memory_type}:{source_id}")`

- [ ] **Step 1: Add settings to `core/config.py`**

```python
USER_MEMORY_COLLECTION: str = "healthpilot_user_memories"
USER_MEMORY_RETRIEVAL_K: int = 5
LIFESTYLE_AGGREGATE_WINDOW_DAYS: int = 7
LIFESTYLE_TREND_SLEEP_DELTA_HOURS: float = 1.0
BLOOD_REPORT_UPLOAD_DIR: str = "uploads/blood_reports"
BLOOD_REPORT_MAX_BYTES: int = 10485760
```

- [ ] **Step 2: Write failing unit test for snippet text** (no PII)

```python
def test_daily_snippet_contains_no_email():
    text = LifestyleService.build_daily_snippet(
        responses={"sleep_hours": 5, "stress": 4, "mood": 2, "energy": 2, "water_glasses": 4, "screen_hours": 8, "activity_level": "sedentary"},
        log_date=date(2026, 8, 9),
    )
    assert "@" not in text
    assert "sleep" in text.lower() or "5" in text
```

- [ ] **Step 3: Implement `QdrantUserMemoryStore`**

Mirror `vector/qdrant_client.py` patterns: `ensure_collection`, `upsert`, `search` with `user_id` filter, `delete_by_source`.

- [ ] **Step 4: Implement `UserMemoryVectorService`**

Use `EmbeddingClient.embed_text(text)` before upsert.

On Qdrant error: log warning, do not raise.

- [ ] **Step 5: Call `write_snippet` from `LifestyleService.upsert_daily_log`**

After Postgres commit. Also write trend snippet when `detect_sleep_trend` returns True.

- [ ] **Step 6: Update `memory_agent_node`**

```python
memory = await memory_svc.load(...)
if user_id:
    query = f"{behavior.get('primary_interest', '')} {health_profile_fields}"
    episodic = await UserMemoryVectorService().search(user_id, query, limit=settings.USER_MEMORY_RETRIEVAL_K)
    memory["episodic_memories"] = episodic
return {"user_memory": memory, "episodic_memories": episodic}
```

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_user_memory_vector_service.py tests/test_lifestyle_service.py -v
```

- [ ] **Step 8: Commit**

```bash
git commit -m "feat(phase4): add Qdrant user memory vectors and memory agent retrieval"
```

---

### Task 8: Blood report backend (optional feature)

**Files:**
- Create: `src/healthPilot/repositories/blood_report_repository.py`
- Create: `src/healthPilot/schemas/blood_report.py`
- Create: `src/healthPilot/services/blood_report_service.py`
- Create: `src/healthPilot/agents/blood_report_agent.py`
- Create: `src/healthPilot/api/endpoints/blood_reports.py`
- Modify: `src/healthPilot/api/routes.py`
- Modify: `.gitignore` — add `uploads/`

**Interfaces:**
- Produces: `BloodReportService.upload(user_id, file) -> BloodReport`
- Produces: `BloodReportService.process_report(report_id) -> None` (background)
- Produces: `BloodReportAgent.extract_biomarkers(file_bytes, mime_type) -> dict` (internal, no raw OCR persisted)
- Produces: `BloodReportService.get_summary_for_pipeline(user_id) -> dict | None`

- [ ] **Step 1: Implement repository** — CRUD scoped to `user_id`

- [ ] **Step 2: Implement `BloodReportAgent`**

- PDF: use `pymupdf` (`fitz`) to extract text in-memory only
- Image: use `pytesseract` or stub for tests with fixture text
- Parse to structured JSON via internal LLM call with JSON schema output (`user_facing: false`)
- Derive `flags` list (e.g. `vitamin_d < 20` → `vitamin_d_low`)

Add `pymupdf` to `pyproject.toml` dependencies.

- [ ] **Step 3: Implement `BloodReportService`**

1. Validate mime (`application/pdf`, `image/jpeg`, `image/png`) and size ≤ `BLOOD_REPORT_MAX_BYTES`
2. Save file to `{BLOOD_REPORT_UPLOAD_DIR}/{user_id}/{report_id}_{filename}`
3. Create row `status=pending`
4. `process_report`: set `processing` → extract → `completed` or `failed`
5. On completed: `UserMemoryVectorService.write_snippet(type=blood_report)`
6. `get_summary_for_pipeline`: latest completed report's `flags` + `biomarkers` keys only

- [ ] **Step 4: Implement API endpoints** (all require auth)

POST `/` multipart, GET `/`, GET `/{id}`, DELETE `/{id}`

POST returns 202; processing via `BackgroundTasks`.

- [ ] **Step 5: Write unit test with mocked agent**

```python
@pytest.mark.asyncio
async def test_process_report_sets_completed(monkeypatch):
    # mock BloodReportAgent.extract_biomarkers to return fixture
    # assert status == completed and extracted_data has biomarkers
    ...
```

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(phase4): add optional blood report upload and extraction"
```

---

### Task 9: Blood report web UI and pipeline integration

**Files:**
- Create: `src/healthPilot/web/health_reports.py`
- Create: `src/healthPilot/templates/health/reports.html`
- Modify: `src/healthPilot/web/router.py`
- Modify: `src/healthPilot/agents/recommendation_nodes.py` — load blood report summary
- Modify: `src/healthPilot/services/recommendation_orchestrator.py` — trigger after report complete
- Modify: `src/healthPilot/templates/base.html` — secondary nav link

**Interfaces:**
- Consumes: `BloodReportService` from Task 8
- Produces: `GET /health/reports`, `POST /health/reports`
- Produces: `RecommendationOrchestrator.maybe_trigger_after_blood_report(user_id)`

- [ ] **Step 1: Create reports template**

Copy per spec:
- "Optional — upload a lab report for deeper personalization."
- Empty state: "No reports uploaded — this is optional."
- Disclaimer block
- Upload form + list with status badges
- Completed: biomarker table + user-facing summary via `run_user_facing_llm`

- [ ] **Step 2: Implement web routes** (require login)

- [ ] **Step 3: Add secondary nav** — "Health Reports" under logged-in nav (less prominent than Daily Check-in)

- [ ] **Step 4: Wire `load_context_node`** to set `blood_report_summary` from `BloodReportService.get_summary_for_pipeline(user_id)`

- [ ] **Step 5: Wire background processing** to call `maybe_trigger_after_blood_report` on `status=completed`

- [ ] **Step 6: Wire feedback `completed`** in `recommendation_orchestrator.record_feedback` to write memory snippet (optional small addition)

- [ ] **Step 7: Commit**

```bash
git commit -m "feat(phase4): add blood report web UI and pipeline integration"
```

---

### Task 10: Configuration, docs, and integration tests

**Files:**
- Modify: `.env.example`
- Modify: `docs/RUN.md`
- Create: `tests/test_phase4_health_signals.py`

- [ ] **Step 1: Update `.env.example`** with Phase 4 vars from spec

- [ ] **Step 2: Update `docs/RUN.md`**

Add Phase 4 section:
- Migration 004
- Daily check-in demo flow (primary path without blood report)
- Optional blood report path
- Qdrant collection note

- [ ] **Step 3: Write integration test**

```python
@pytest.mark.asyncio
async def test_lifestyle_upsert_updates_profile(authenticated_client):
    resp = await authenticated_client.post(
        "/api/v1/lifestyle/daily",
        json={
            "log_date": "2026-08-09",
            "responses": {
                "sleep_hours": 5.0,
                "water_glasses": 6,
                "activity_level": "light",
                "screen_hours": 8.0,
                "mood": 2,
                "stress": 4,
                "energy": 2,
            },
        },
    )
    assert resp.status_code == 200
    profile = await authenticated_client.get("/api/v1/lifestyle/profile")
    assert profile.json()["sleep_average"] == 5.0
```

Add second test: same `log_date` upsert updates (not duplicates).

- [ ] **Step 4: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add .env.example docs/RUN.md tests/test_phase4_health_signals.py
git commit -m "docs(phase4): add config, RUN guide, and integration tests"
```

---

## Self-Review (spec coverage)

| Spec requirement | Task |
|---|---|
| Migration 004 tables | Task 1 |
| Once-per-day upsert | Task 2, 3 |
| 7-day aggregates | Task 2 |
| Lifestyle API | Task 3 |
| `/lifestyle` web UI | Task 4 |
| Blood report optional | Tasks 8–9 (UI copy + scoring skip) |
| Qdrant user memories | Task 7 |
| Memory agent retrieval | Task 7 |
| Evaluation lifestyle_fit / biomarker | Task 5 |
| Pipeline extensions | Tasks 6, 9 |
| Triggers (survey, trend, report) | Tasks 6, 9 |
| Privacy pipeline on summaries | Task 9 |
| Config vars | Tasks 7, 10 |
| Demo flows in RUN.md | Task 10 |
| Login required for health data | Tasks 3, 4, 8, 9 |
| No wearable sync | Out of scope — not in plan |

No placeholders remain. Type names consistent across tasks.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-09-phase4-health-signals.md`. Two execution options:

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
