# Task 3 Report: Lifestyle REST API

**Status:** DONE  
**Date:** 2026-08-09

## Summary

Implemented authenticated lifestyle REST endpoints under `/api/v1/lifestyle`, registered the router, and added API tests with shared `client` / `authenticated_client` fixtures.

## Files created / modified

| File | Purpose |
|---|---|
| `src/healthPilot/api/endpoints/lifestyle.py` | Four endpoints: today, list, upsert, profile |
| `src/healthPilot/api/routes.py` | Register lifestyle router at `/lifestyle` |
| `src/healthPilot/schemas/lifestyle.py` | Added `DailyLogResponse`, `DailyLogListResponse`, `DailyLogUpsertResponse` |
| `tests/conftest.py` | `client` and `authenticated_client` fixtures |
| `tests/test_lifestyle_api.py` | Auth guard + upsert/profile tests |

## Endpoints

| Method | Path | Behavior |
|---|---|---|
| GET | `/daily/today` | Today's log or 404 |
| GET | `/daily` | List logs (`from_date`, `to_date`, max 90 days) |
| POST | `/daily` | Upsert log; returns log + profile + `material_change` |
| GET | `/profile` | Health profile aggregates or 404 |

All endpoints require `get_current_user`.

## Tests

```text
uv run pytest tests/test_lifestyle_api.py -v
tests/test_lifestyle_api.py::test_lifestyle_daily_requires_auth PASSED
tests/test_lifestyle_api.py::test_lifestyle_upsert_returns_profile PASSED
2 passed
```

## Commit

`feat(phase4): add lifestyle REST API` — not committed (git add skipped in session).

## Concerns

- Task 1/2 files (models, migration, service, repos) remain uncommitted alongside Task 3; commit should include dependency chain for a working tree.
- API tests require live PostgreSQL with migration `004` applied.
- `Decimal` profile fields may serialize as strings in JSON depending on client; tests accept `7`, `7.0`, or `"7.0"`.
