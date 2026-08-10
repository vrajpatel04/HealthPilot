# Task 1 Brief: Database migration and ORM models

**Plan:** Phase 4 Health Signals  
**Repo:** `d:\Projects\HealthPilot`

## Global Constraints (binding)

- Survey cadence: once per day — unique `(user_id, log_date)`
- Blood reports fully optional
- Auth required for health endpoints (later tasks)
- Follow existing codebase patterns (see `003_recommendations_memory_feedback.py`, `models/event.py`)

## Files

- Create: `alembic/versions/004_health_signals.py`
- Create: `src/healthPilot/models/lifestyle_daily_log.py`
- Create: `src/healthPilot/models/health_profile.py`
- Create: `src/healthPilot/models/blood_report.py`
- Modify: `src/healthPilot/models/enums.py`
- Modify: `src/healthPilot/models/__init__.py` (if exists — register models for Alembic)

## Interfaces to produce

- ORM classes: `LifestyleDailyLog`, `HealthProfile`, `BloodReport`
- Enums: `ActivityLevel`, `BloodReportStatus`

## Step 1: Add enums to `models/enums.py`

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

## Step 2: Create migration `004_health_signals.py`

Follow pattern from `alembic/versions/003_recommendations_memory_feedback.py`:
- `lifestyle_daily_logs` with `UniqueConstraint("user_id", "log_date")`
- `health_profiles` with `UniqueConstraint("user_id")`
- `blood_reports` with `blood_report_status` enum
- `down_revision = "003"`

### `lifestyle_daily_logs` columns

| Column | Type |
|---|---|
| id | UUID PK |
| user_id | UUID FK users.id, required |
| log_date | DATE |
| responses | JSONB default {} |
| created_at | TIMESTAMPTZ server default now() |
| updated_at | TIMESTAMPTZ server default now() |

Unique: `(user_id, log_date)`

### `health_profiles` columns

| Column | Type |
|---|---|
| id | UUID PK |
| user_id | UUID FK users.id, unique |
| sleep_average | NUMERIC(4,1) nullable |
| water_average | NUMERIC(4,1) nullable |
| activity_average | NUMERIC(3,2) nullable |
| screen_time_average | NUMERIC(4,1) nullable |
| mood_average | NUMERIC(3,2) nullable |
| stress_average | NUMERIC(3,2) nullable |
| energy_average | NUMERIC(3,2) nullable |
| metadata | JSONB default {} |
| updated_at | TIMESTAMPTZ server default now() |

### `blood_reports` columns

| Column | Type |
|---|---|
| id | UUID PK |
| user_id | UUID FK users.id, required |
| file_name | VARCHAR(255) |
| file_path | VARCHAR(512) |
| mime_type | VARCHAR(100) |
| status | blood_report_status enum |
| extracted_data | JSONB default {} |
| upload_date | TIMESTAMPTZ server default now() |
| processed_at | TIMESTAMPTZ nullable |
| last_error | TEXT nullable |

## Step 3: Create ORM models

Match existing model style in `src/healthPilot/models/event.py` and `user_memory.py`:
- Use `Mapped`, `mapped_column`, `Base` from `healthPilot.models.base`
- JSONB metadata column named `metadata` in DB, attribute `metadata_` where needed (see `UserMemory`)
- `BloodReport.status` uses `BloodReportStatus` enum with `native_enum=True`

## Step 4: Run migration

```bash
alembic upgrade head
```

If DB unavailable, verify migration file syntax only and note in report.

## Step 5: Commit

```bash
git add alembic/versions/004_health_signals.py src/healthPilot/models/
git commit -m "feat(phase4): add health signals database schema"
```

## Report contract

Write full report to: `.superpowers/sdd/2026-08-09-phase4-health-signals/task-1-report.md`

Return only: STATUS (DONE|DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED), commit hash(es), one-line test summary, concerns list.
