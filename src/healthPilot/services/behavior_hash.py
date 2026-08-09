import hashlib
import json
from typing import Any


def compute_behavior_hash(events: list[dict[str, Any]]) -> str:
    payload = json.dumps(events, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def actor_key(*, user_id: str | None, session_id: str) -> str:
    return user_id or session_id
