# Task 2 Brief: Lifestyle repository, schemas, and service

**Plan:** Phase 4 Health Signals  
**Repo:** `d:\Projects\HealthPilot`

## Depends on Task 1

- Models: `LifestyleDailyLog`, `HealthProfile` in `src/healthPilot/models/`
- Enums: `ActivityLevel` in `src/healthPilot/models/enums.py`

## Global Constraints

- Once per day upsert: unique `(user_id, log_date)` — same day = update
- Reject `log_date > date.today()`
- `LIFESTYLE_AGGREGATE_WINDOW_DAYS=7` (use constant 7 for now; config added in Task 7)
- Activity mapping: sedentary=1, light=2, moderate=3, active=4

## Files to create

- `src/healthPilot/schemas/lifestyle.py`
- `src/healthPilot/repositories/lifestyle_repository.py`
- `src/healthPilot/repositories/health_profile_repository.py`
- `src/healthPilot/services/lifestyle_service.py`
- `tests/test_lifestyle_service.py`

## Interfaces to produce

```python
# lifestyle_service.py
ACTIVITY_NUMERIC: dict[str, int]

def compute_aggregates_from_logs(logs: list[dict]) -> dict  # pure function

class LifestyleService:
    @staticmethod
    def responses_materially_changed(old: dict, new: dict) -> bool

    async def upsert_daily_log(
        self, user_id: UUID, log_date: date, responses: dict
    ) -> tuple[LifestyleDailyLog, HealthProfile, bool]
    # material_change: True if first log today OR any numeric field delta >= 1

    @staticmethod
    def build_daily_snippet(responses: dict, log_date: date) -> str

    @staticmethod
    def detect_sleep_trend(current_sleep_avg: float | None, prior_sleep_avg: float | None) -> bool
    # True if prior - current >= 1.0 (LIFESTYLE_TREND_SLEEP_DELTA_HOURS)
```

## Schemas

`LifestyleResponses`: sleep_hours (0-24), water_glasses (0-20), activity_level (enum), screen_hours (0-24), mood/stress/energy (1-5), notes optional max 500

`DailyLogUpsertRequest`: log_date, responses

`HealthProfileResponse`: all averages + days_in_window

## Repository methods

`LifestyleRepository`: `get_by_user_date`, `upsert`, `list_in_range(user_id, from_date, to_date)`

`HealthProfileRepository`: `get_by_user_id`, `upsert`

## Tests (must pass)

```python
# tests/test_lifestyle_service.py — see plan for full test bodies
test_activity_numeric_mapping
test_compute_aggregates_single_day
test_material_change_detects_sleep_delta
test_material_change_ignores_small_delta
```

Run: `pytest tests/test_lifestyle_service.py -v`

## Patterns

- Follow `src/healthPilot/repositories/user_memory_repository.py` for repo style
- Follow `src/healthPilot/services/memory_service.py` for service style
- Use `healthPilot.core.exceptions` if ValidationError exists; else pydantic ValidationError

## Commit

```bash
git add src/healthPilot/schemas/lifestyle.py src/healthPilot/repositories/lifestyle_repository.py src/healthPilot/repositories/health_profile_repository.py src/healthPilot/services/lifestyle_service.py tests/test_lifestyle_service.py
git commit -m "feat(phase4): add lifestyle service with daily upsert and aggregates"
```

## Report

Write to: `.superpowers/sdd/2026-08-09-phase4-health-signals/task-2-report.md`

Return: STATUS, commits, tests, concerns
