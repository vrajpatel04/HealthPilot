# Task 3 Brief: Lifestyle REST API

**Repo:** `d:\Projects\HealthPilot`

## Consumes (Task 2)

- `LifestyleService.upsert_daily_log(user_id, log_date, responses) -> tuple[LifestyleDailyLog, HealthProfile, bool]`
- Schemas in `src/healthPilot/schemas/lifestyle.py`: `DailyLogUpsertRequest`, `HealthProfileResponse`, etc.

## Endpoints (all require `get_current_user` from `healthPilot.api.deps`)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/lifestyle/daily/today` | Today's log or 404 |
| GET | `/api/v1/lifestyle/daily` | List logs; query `from_date`, `to_date` (max 90 days) |
| POST | `/api/v1/lifestyle/daily` | Upsert `{ log_date, responses }` |
| GET | `/api/v1/lifestyle/profile` | Health profile aggregates |

## Files

- Create: `src/healthPilot/api/endpoints/lifestyle.py`
- Modify: `src/healthPilot/api/routes.py`
- Create: `tests/test_lifestyle_api.py`

## Auth test (required)

```python
@pytest.mark.asyncio
async def test_lifestyle_daily_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/lifestyle/daily",
        json={
            "log_date": "2026-08-09",
            "responses": {
                "sleep_hours": 7,
                "water_glasses": 8,
                "activity_level": "moderate",
                "screen_hours": 3,
                "mood": 4,
                "stress": 2,
                "energy": 4,
            },
        },
    )
    assert resp.status_code == 401
```

Use existing `client` / `authenticated_client` fixtures from `tests/conftest.py` if present; otherwise create minimal conftest fixtures following project patterns.

## Register router

```python
from healthPilot.api.endpoints import lifestyle
v1_router.include_router(lifestyle.router, prefix="/lifestyle", tags=["lifestyle"])
```

## Commit

`feat(phase4): add lifestyle REST API`

## Report

`.superpowers/sdd/2026-08-09-phase4-health-signals/task-3-report.md`
