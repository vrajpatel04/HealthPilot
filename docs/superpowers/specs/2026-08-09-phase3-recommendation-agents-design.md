# HealthPilot Phase 3: LangGraph Recommendation Agents Design

**Date:** 2026-08-09  
**Status:** Approved  
**Scope:** Full recommendation pipeline — agents, RAG, triggers, caching, UI  
**Depends on:** Phase 1 (foundation), Phase 2 (events + marketplace UI)

---

## Decisions

| Decision | Choice |
|---|---|
| Scope | Full Phase 3 — all agents, RAG, triggers, cache, UI |
| Architecture | Approach 1 — single recommendation LangGraph + sidecar services |
| Redis | Optional `REDIS_URL`; `NullCache` fallback when unset |
| Redis scope | Recommendations, behavior summary, trigger cooldowns + product list/detail API cache |
| RAG | Bundled markdown in `data/knowledge/` + `scripts/seed_rag.py` |
| UI | Homepage widget + `/recommendations` dedicated page |
| Triggers | Conservative (search, product_return, category + 2 views, manual refresh) |
| Memory | Postgres JSONB (`user_memories` table) |

---

## Phase 3 Scope

### In scope

- Recommendation LangGraph with 6 agent nodes
- Tables: `user_memories`, `recommendations`, `feedback`
- RAG knowledge base in Qdrant (`healthpilot_knowledge`)
- Conservative auto-triggers after event batch ingest
- Optional Redis caching layer
- `/recommendations` web page + homepage widget
- `GET /api/v1/recommendations`, `POST /api/v1/recommendations/refresh`
- Product read API Redis cache (when `REDIS_URL` set)
- Feedback recording on recommendation interactions

### Out of scope (Phase 4)

- Blood report upload/analysis
- Lifestyle signals (Fit/Apple Health)
- Proactive email / scheduled digest delivery
- Qdrant user memory vectors
- Admin RAG document upload UI

---

## Architecture

### New modules

```text
src/healthPilot/
├── agents/
│   ├── recommendation_graph.py
│   ├── recommendation_state.py
│   └── recommendation_nodes.py
├── services/
│   ├── recommendation_orchestrator.py
│   ├── behavior_service.py
│   ├── memory_service.py
│   ├── retrieval_service.py
│   ├── evaluation_service.py
│   └── trigger_service.py
├── cache/
│   └── redis_cache.py
├── rag/
│   ├── ingest.py
│   └── retriever.py
├── models/user_memory.py, recommendation.py, feedback.py
├── api/endpoints/recommendations.py
└── web/recommendations.py

data/knowledge/          # bundled wellness markdown
scripts/seed_rag.py
```

### Orchestration flow

```text
Event batch / manual refresh / page load (cache miss)
        ↓
RecommendationOrchestrator
        ↓ behavior_hash from recent events
        ↓ Redis cooldown? cached rec same hash? → return cached
        ↓
recommendation_graph.invoke(RecommendationState)
        ↓
Postgres: recommendations + user_memories
Redis: cache [if REDIS_URL]
        ↓
Web widget / API / /recommendations page
```

### Optional Redis

```text
REDIS_URL set   → RedisCache (async redis client)
REDIS_URL empty → NullCache (no-op, Postgres-only)
```

---

## LangGraph Topology

### RecommendationState

```python
class RecommendationState(TypedDict):
    user_id: UUID | None
    session_id: str
    events: list[dict]
    behavior_summary: dict
    user_memory: dict
    retrieval_query: str
    product_candidates: list[dict]
    rag_context: list[dict]
    evaluated_candidates: list[dict]
    primary_product_id: UUID | None
    secondary_product_id: UUID | None
    reason: str
    confidence: float
    persuasive_message: str
    behavior_hash: str
    errors: list[str]
```

### Graph flow

```text
START → load_context → behavior_agent → memory_agent → retrieval_agent
      → evaluation_agent → recommendation_agent → persuasion_agent
      → store_recommendation → END
```

### Privacy pipeline

| Node | User-facing | Privacy pipeline |
|---|---|---|
| load_context | No | — |
| behavior_agent | No | Internal LLM (no PII in prompt — structured events only) |
| memory_agent | No | Postgres |
| retrieval_agent | No | Qdrant |
| evaluation_agent | No | Scoring rules |
| recommendation_agent | Yes | Presidio → NeMo → LLM → NeMo → Presidio |
| persuasion_agent | Yes | Presidio → NeMo → LLM → NeMo → Presidio |
| store_recommendation | No | Postgres + Redis |

Event data passed to LLM uses product IDs and categories — no raw user PII in agent prompts.

---

## Data Model

### `user_memories`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK, unique) | Nullable for anonymous — keyed by session in interim |
| `session_id` | VARCHAR(64) | For pre-login memory |
| `primary_interest` | VARCHAR(255) | |
| `secondary_interest` | VARCHAR(255) | Nullable |
| `preferences` | JSONB | e.g. `{ "content_type": "structured_programs" }` |
| `successful_recommendations` | JSONB | Array of `{ product_id, outcome }` |
| `metadata` | JSONB | Extra memory fields |
| `updated_at` | TIMESTAMPTZ | |

### `recommendations`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK) | Nullable |
| `session_id` | VARCHAR(64) | Always set |
| `primary_product_id` | UUID (FK) | |
| `secondary_product_id` | UUID (FK) | Nullable |
| `product_ids` | JSONB | `[primary, secondary]` |
| `message` | TEXT | Persuasive message (user-facing) |
| `reason` | TEXT | Structured reason |
| `confidence` | NUMERIC(3,2) | 0.00–1.00 |
| `behavior_hash` | VARCHAR(64) | Invalidates cache when behavior changes |
| `behavior_summary` | JSONB | Snapshot at generation time |
| `created_at` | TIMESTAMPTZ | |
| `expires_at` | TIMESTAMPTZ | Default 24h |

### `feedback`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK) | Nullable |
| `recommendation_id` | UUID (FK) | |
| `action` | ENUM | `displayed`, `clicked`, `saved`, `ignored`, `started`, `completed` |
| `timestamp` | TIMESTAMPTZ | |

### Alembic migration `003_recommendations_memory_feedback`

---

## Redis Cache Keys

| Key pattern | TTL | Content |
|---|---|---|
| `rec:latest:{user_id\|session_id}` | 24h | Full recommendation JSON |
| `rec:behavior_hash:{user_id\|session_id}` | 24h | Current behavior hash string |
| `rec:behavior_summary:{user_id\|session_id}` | 1h | Behavior Agent output JSON |
| `trigger:cooldown:{user_id\|session_id}` | 5min | `"1"` — blocks auto-trigger |
| `products:list:{hash}` | 60s | Paginated product list response |
| `products:detail:{product_id}` | 5min | Single product JSON |

**Invalidation:**
- Admin product create/update/delete → `products:*` pattern delete
- New recommendation stored → update `rec:latest:*` and `rec:behavior_hash:*`

**Fallback without Redis:**
- Read latest from `recommendations` WHERE `session_id`/`user_id` ORDER BY `created_at` DESC
- Compare `behavior_hash` in Postgres before re-running graph
- Trigger cooldown stored in Postgres `recommendations.metadata` or lightweight `trigger_log` table

---

## Conservative Trigger Rules

Evaluated async after `POST /api/v1/events/batch` (background task):

| Trigger | Condition |
|---|---|
| Manual | `POST /api/v1/recommendations/refresh` — always runs (respects cooldown optionally bypass) |
| Search | `search` event with query not seen in last 30 min for this user/session |
| Product return | `product_return` event |
| Category interest | `category_filter` + ≥2 `product_view` in same category within 30 min |

**Skip pipeline if:**
- `trigger:cooldown` active (5 min since last run)
- Latest recommendation `behavior_hash` matches current hash
- No events in last 7 days (anonymous cold start — show generic or empty)

---

## RAG Knowledge Base

### Collection: `healthpilot_knowledge`

Bundled docs in `data/knowledge/`:

```text
data/knowledge/
├── sleep-guidelines.md
├── nutrition-guidelines.md
├── physical-activity.md
├── hydration.md
├── stress-management.md
└── healthy-lifestyle.md
```

### Ingest (`scripts/seed_rag.py`)

```text
Markdown files → chunk (1000/200 overlap) → Mesh embeddings → Qdrant upsert
```

Reuses `EMBEDDING_MODEL`, `QDRANT_URL` from `.env`. Idempotent — skips existing chunk IDs.

### Retrieval Agent

- Query = behavior summary primary interest + retrieval query
- Top K=3 chunks from `healthpilot_knowledge`
- Passed to recommendation_agent as grounding context (not shown raw to user)

---

## Qdrant Collections (summary)

| Collection | Purpose | Seeded by |
|---|---|---|
| `healthpilot_products` | Product semantic search | Phase 1 admin/seed_products |
| `healthpilot_knowledge` | RAG wellness docs | `seed_rag.py` |

Retrieval Agent searches **products** collection using embedding of behavior summary query. RAG Agent searches **knowledge** collection separately.

---

## Evaluation Agent

Scores each product candidate:

```text
final_score = (
  0.40 * semantic_relevance      # Qdrant score
  + 0.25 * behavior_match        # category/interest alignment
  + 0.15 * memory_boost          # past successful similar products
  + 0.10 * price_fit             # optional metadata
  + 0.10 * engagement_signal     # high_intent_product match
)
```

Top 2 candidates proceed to recommendation_agent.

---

## API Endpoints

### Recommendations — `/api/v1/recommendations`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | Optional | Latest recommendation (cache → Postgres) |
| POST | `/refresh` | Optional | Force pipeline run |
| POST | `/feedback` | Optional | Record feedback action |

**GET response**
```json
{
  "id": "...",
  "primary_product": { "id": "...", "title": "...", "price": "499.00" },
  "secondary_product": null,
  "message": "You've been exploring sleep...",
  "reason": "High engagement with sleep content",
  "confidence": 0.91,
  "why_recommended": [
    "You searched for sleep improvement",
    "You viewed this course twice"
  ],
  "cached": true,
  "created_at": "2026-08-09T10:00:00Z"
}
```

Anonymous users keyed by `session_id` + `hp_anon_session` cookie.

### Product API cache (Phase 1 extension)

Wrap `ProductService.list_public` and `get_public` with cache decorator when Redis available.

---

## Web UI

### Homepage widget (`/`)

- If recommendation exists: card with title, one-line message, link to product + "See all recommendations"
- If none: "Browse the marketplace" CTA (no error)

### `/recommendations` page

- Primary product card with persuasive message
- Secondary recommendation (if any)
- "Why recommended?" bullet list from `why_recommended`
- **Refresh recommendations** button → `POST /recommendations/refresh` form
- Feedback buttons: "Interested" (clicked), "Not for me" (ignored)

### Nav

- Add "For You" link when user has browsed (any events) or has a recommendation

---

## Configuration (`.env` additions)

```env
# Redis (optional — omit or leave empty to disable)
REDIS_URL=redis://localhost:6379/0

# RAG
KNOWLEDGE_COLLECTION=healthpilot_knowledge
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_RETRIEVAL_K=3

# Recommendations
RECOMMENDATION_TTL_HOURS=24
TRIGGER_COOLDOWN_SECONDS=300
BEHAVIOR_WINDOW_HOURS=168

# Product API cache (when Redis available)
PRODUCT_LIST_CACHE_TTL=60
PRODUCT_DETAIL_CACHE_TTL=300
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Redis unavailable at startup | Log warning; use NullCache |
| Redis error at runtime | Fall through to Postgres |
| Qdrant down during retrieval | Skip vector search; fall back to category-filtered Postgres products |
| RAG empty | Proceed without grounding (log warning) |
| LLM/privacy pipeline blocked | Return safe fallback message; store partial recommendation |
| No products match | Empty recommendation with wellness tip from RAG |

---

## Testing

| Layer | Coverage |
|---|---|
| Unit | Evaluation scoring, behavior_hash computation, trigger rules |
| Unit | RedisCache + NullCache parity |
| Unit | TriggerService conservative rules |
| Integration | Full graph with mocked LLM + Qdrant |
| Integration | GET /recommendations returns cached result |
| Integration | Event batch triggers pipeline (background) |
| Manual | Rahul journey → recommendation on /recommendations |
| Manual | Redis on vs off — same correct results |

---

## Completion Criteria

- [ ] Migration `003` creates `user_memories`, `recommendations`, `feedback`
- [ ] `seed_rag.py` populates knowledge collection
- [ ] Recommendation LangGraph runs end-to-end
- [ ] Privacy pipeline on recommendation + persuasion agent outputs
- [ ] Conservative triggers fire after relevant events
- [ ] Redis caches recommendations + products when `REDIS_URL` set
- [ ] Graceful fallback without Redis
- [ ] `/recommendations` page + homepage widget
- [ ] `GET /api/v1/recommendations` + refresh + feedback
- [ ] `docs/RUN.md` updated with Phase 3 setup (Redis, seed_rag, demo flow)

---

## Demo Flow (Rahul journey — Phase 3)

1. Browse anonymously — events accumulate
2. Search "sleep improvement" → trigger fires (background)
3. Visit `/` — homepage widget shows recommendation
4. Open `/recommendations` — full persuasive message + why bullets
5. Click "Interested" → feedback recorded
6. Log in — recommendation linked to `user_id`
7. Click "Refresh" — new recommendation with updated behavior

---

## Route Registration

```text
GET  /recommendations           → web/recommendations (page)
POST /recommendations/refresh   → web/recommendations (form)
GET  /api/v1/recommendations    → api/recommendations
POST /api/v1/recommendations/refresh
POST /api/v1/recommendations/feedback
```

Existing routes unchanged.
