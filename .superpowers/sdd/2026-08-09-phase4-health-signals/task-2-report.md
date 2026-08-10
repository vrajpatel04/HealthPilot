# Task 2 Report: Lifestyle repository, schemas, and service

**Status:** DONE  
**Date:** 2026-08-09

## Summary

Implemented lifestyle schemas, repositories, service layer, and unit tests per TDD. All four required tests pass.

## Files created

| File | Purpose |
|---|---|
| `src/healthPilot/schemas/lifestyle.py` | `LifestyleResponses`, `DailyLogUpsertRequest`, `HealthProfileResponse` |
| `src/healthPilot/repositories/lifestyle_repository.py` | `get_by_user_date`, `upsert`, `list_in_range` |
| `src/healthPilot/repositories/health_profile_repository.py` | `get_by_user_id`, `upsert` |
| `src/healthPilot/services/lifestyle_service.py` | Aggregates, material-change detection, daily upsert |
| `tests/test_lifestyle_service.py` | Four unit tests for pure service logic |

## Implementation notes

- `ACTIVITY_NUMERIC`: sedentary=1, light=2, moderate=3, active=4
- `LIFESTYLE_AGGREGATE_WINDOW_DAYS=7` constant (config deferred to Task 7)
- `compute_aggregates_from_logs` is a pure function over `list[dict]` with `responses` key
- `responses_materially_changed`: True when any numeric field delta ≥ 1 (including activity level mapping)
- `upsert_daily_log`: rejects future `log_date` via Pydantic `ValidationError`; returns `(log, profile, material_change)`
- `build_daily_snippet` and `detect_sleep_trend` implemented for Task 6 vector integration

## Tests

```text
uv run pytest tests/test_lifestyle_service.py -v
tests/test_lifestyle_service.py::test_activity_numeric_mapping PASSED
tests/test_lifestyle_service.py::test_compute_aggregates_single_day PASSED
tests/test_lifestyle_service.py::test_material_change_detects_sleep_delta PASSED
tests/test_lifestyle_service.py::test_material_change_ignores_small_delta PASSED
4 passed
```

## Commit

`feat(phase4): add lifestyle service with daily upsert and aggregates`

## Concerns

- Task 1 migration/models remain uncommitted from prior task; Task 2 commit is self-contained.
- `upsert_daily_log` DB integration not covered by unit tests (no DB fixtures in scope); covered in Task 3 API tests.
- `LIFESTYLE_AGGREGATE_WINDOW_DAYS` hardcoded; Task 7 will move to config.
