# HealthPilot Phase 1: Foundation Design

**Date:** 2026-08-08  
**Status:** Approved  
**Scope:** Database, auth, product CRUD, dual-write PostgreSQL ↔ Qdrant sync

---

## Context

HealthPilot AI is an agentic wellness recommendation platform. The full vision (behavioral tracking, LangGraph agents, RAG, blood reports, etc.) is documented in `docs/Updated Project Idea.md`.

**Current codebase state:**
- FastAPI backend with embedded privacy pipeline (Presidio → NeMo → LLM)
- Basic coach LangGraph wired to privacy pipeline
- No PostgreSQL, Qdrant, auth, products, or frontend yet

**Phase 1 strategy:** Foundation-first — build database, auth, product CRUD, and dual-write vector sync before layering AI on top.

---

## Decisions

| Decision | Choice |
|---|---|
| Build order | Foundation-first, AI in later phases |
| Phase 1 UI | Backend/API only (FastAPI + Swagger) |
| PostgreSQL | Cloud service (Neon) via `DATABASE_URL` in `.env` |
| Qdrant | Local Docker (`http://localhost:6333`) |
| Dual-write failure | Postgres wins; mark `pending`; APScheduler background retry |
| Embeddings | Mesh API (same provider as LLM) |
| Authentication | HTTP-only session cookies (Starlette SessionMiddleware) |
| Background sync | APScheduler in-process, 30s interval |
| Architecture | Layered monolith with status column on products (Approach 1) |

---

## Phase 1 Scope

### In scope

- PostgreSQL (Neon) + Alembic migrations
- User registration and login (session cookies)
- Admin product CRUD
- Public product read endpoints
- Qdrant product collection (Docker)
- Dual-write with `vector_sync_status` + APScheduler retry
- Mesh API embeddings for products
- Admin bootstrap via env vars
- Extended `/health` check (Postgres + Qdrant)

### Out of scope (Phase 2+)

- Jinja2 frontend
- Behavioral event tracking
- Recommendation agents (LangGraph)
- RAG knowledge base
- Blood report upload
- Coach chat endpoints
- Lifestyle signals
- Tables: `events`, `recommendations`, `feedback`, `health_profiles`, `blood_reports`

---

## Architecture

### Layered structure

Extends the existing codebase under `src/healthPilot/`:

```text
src/healthPilot/
├── api/endpoints/
│   ├── auth.py              # register, login, logout, me
│   ├── products.py          # public read
│   └── admin/
│       ├── products.py      # admin CRUD
│       └── sync.py          # manual resync
├── core/
│   ├── config.py            # + DATABASE_URL, QDRANT_*, SESSION_SECRET, etc.
│   ├── database.py          # async SQLAlchemy engine + session
│   └── security.py          # password hash, session helpers
├── models/                  # SQLAlchemy ORM (User, Product)
├── schemas/                 # Pydantic request/response
├── services/
│   ├── auth_service.py
│   ├── product_service.py
│   └── vector_sync_service.py
├── repositories/
│   ├── user_repository.py
│   └── product_repository.py
├── vector/
│   ├── qdrant_client.py
│   └── embedding_client.py  # Mesh API embeddings
├── jobs/
│   └── vector_sync_job.py   # APScheduler sweep
└── privacy/ ... agents/ ... # unchanged in Phase 1
```

### Request flow (admin creates product)

```text
POST /api/v1/admin/products
        ↓
   Auth middleware (session cookie → admin role check)
        ↓
   ProductService.create()
        ↓
   Postgres INSERT (vector_sync_status = pending)
        ↓
   VectorSyncService.sync_product()  ← immediate attempt
        ↓
   Mesh API embedding → Qdrant upsert
        ↓
   Update status → synced (or failed on error)
        ↓
   Return product JSON to admin
```

APScheduler runs every 30s as a safety net for `pending`/`failed` products.

### Tech stack (Phase 1 additions)

| Component | Choice |
|---|---|
| ORM | SQLAlchemy 2.0 async |
| Migrations | Alembic |
| DB driver | asyncpg |
| Password hashing | passlib[bcrypt] |
| Sessions | Starlette SessionMiddleware + signed cookie |
| Vector store | qdrant-client |
| Embeddings | Mesh API via httpx (OpenAI-compatible `/embeddings`) |
| Scheduler | APScheduler 3.x (started/stopped in FastAPI lifespan) |

---

## Data Model

### `users`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Default `gen_random_uuid()` |
| `name` | VARCHAR(255) | Display name |
| `email` | VARCHAR(255) | Unique, indexed |
| `password_hash` | VARCHAR(255) | bcrypt via passlib |
| `role` | ENUM | `user` \| `admin` |
| `created_at` | TIMESTAMPTZ | Default `now()` |

First admin seeded on startup when `ADMIN_EMAIL` + `ADMIN_PASSWORD` are set and no admin exists.

### `products`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Same ID used as Qdrant point ID |
| `title` | VARCHAR(255) | Required |
| `description` | TEXT | Required — primary embedding source |
| `category` | ENUM | `sleep`, `fitness`, `nutrition`, `mental_wellness`, `lifestyle` |
| `price` | NUMERIC(10,2) | Stored in rupees (₹) |
| `metadata` | JSONB | Optional (duration, difficulty, tags) |
| `is_active` | BOOLEAN | Default `true`; soft-hide without delete |
| `vector_sync_status` | ENUM | `synced` \| `pending` \| `failed` |
| `last_sync_error` | TEXT | Nullable |
| `last_synced_at` | TIMESTAMPTZ | Nullable |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | Auto-updated on change |

**Embedding text** (computed at sync time, not stored):

```text
{title}. {category}. {description}
```

### Postgres enums

```sql
CREATE TYPE user_role AS ENUM ('user', 'admin');
CREATE TYPE product_category AS ENUM (
  'sleep', 'fitness', 'nutrition', 'mental_wellness', 'lifestyle'
);
CREATE TYPE vector_sync_status AS ENUM ('synced', 'pending', 'failed');
```

### Qdrant collection: `healthpilot_products`

| Field | Value |
|---|---|
| Point ID | `product.id` (UUID string) |
| Vector | Mesh API embedding of embedding text |
| Payload | `product_id`, `title`, `category`, `price`, `is_active`, `updated_at` |

Collection created on app startup if missing. Vector dimension set from first successful Mesh API embedding response.

---

## API Endpoints

All routes under `/api/v1` (existing `API_V1_STR`).

### Auth — `/api/v1/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/register` | None | Create account (role defaults to `user`) |
| POST | `/login` | None | Validate credentials → set session cookie |
| POST | `/logout` | Session | Clear session cookie |
| GET | `/me` | Session | Current user (id, name, email, role) |

**Session cookie:** `healthpilot_session`, flags `HttpOnly`, `SameSite=Lax`, `Secure` in production. Signed payload: `{ user_id, role }`.

### Products (public) — `/api/v1/products`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | None | Paginated list (filter by category) |
| GET | `/{product_id}` | None | Single product detail |

Query params: `category`, `page` (default 1), `page_size` (default 20, max 100), `is_active` (default true).

Public responses omit `vector_sync_status` and `last_sync_error`.

### Admin products — `/api/v1/admin/products`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/` | Admin | Create → Postgres + immediate Qdrant sync |
| GET | `/` | Admin | List all (includes sync status) |
| GET | `/{product_id}` | Admin | Detail with sync metadata |
| PUT | `/{product_id}` | Admin | Full update → re-sync |
| PATCH | `/{product_id}` | Admin | Partial update → re-sync if embed fields changed |
| DELETE | `/{product_id}` | Admin | Soft-delete + remove Qdrant point |

Embed fields that trigger re-sync: `title`, `description`, `category`.

### Admin sync — `/api/v1/admin/sync`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/retry` | Admin | Sweep all `pending`/`failed` products |
| POST | `/products/{product_id}` | Admin | Force re-sync single product |

### Health (extended)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Postgres + Qdrant + Presidio + NeMo status |

### Error responses

```json
{ "detail": "Human-readable message", "code": "PRODUCT_NOT_FOUND" }
```

| Status | When |
|---|---|
| 401 | No/invalid session |
| 403 | Not admin |
| 404 | Not found |
| 409 | Duplicate email |
| 422 | Validation error |
| 503 | Postgres unavailable |

---

## Dual-Write Sync Flow

### Create / update

1. Save to Postgres with `vector_sync_status = pending`
2. Immediate `VectorSyncService.sync_product(id)`:
   - Build embedding text
   - POST Mesh API `/embeddings`
   - Qdrant upsert (point id = product.id)
   - On success: `synced`, set `last_synced_at`, clear `last_sync_error`
   - On failure: `failed`, store error in `last_sync_error`
3. Return product with current sync status (Postgres write always succeeds)

### Delete (soft)

1. Postgres: `is_active = false`
2. Qdrant: delete point by product.id
3. On Qdrant failure: mark `failed`, APScheduler retries delete

### APScheduler job

| Setting | Value |
|---|---|
| Interval | 30 seconds |
| Lifecycle | Started in FastAPI lifespan, stopped on shutdown |
| Query | `vector_sync_status IN ('pending', 'failed')` |
| Retry cap | 10 attempts per product (tracked in `metadata.sync_attempts`); manual resync resets counter |

### Mesh API embedding

```text
POST {OPENAI_BASE_URL}/embeddings
Authorization: Bearer {OPENAI_API_KEY}

{ "model": "{EMBEDDING_MODEL}", "input": "<embedding text>" }
```

### Qdrant point

```json
{
  "id": "<product-uuid>",
  "vector": [0.012, -0.034],
  "payload": {
    "product_id": "<product-uuid>",
    "title": "Sleep Better in 21 Days",
    "category": "sleep",
    "price": 499.00,
    "is_active": true,
    "updated_at": "2026-08-08T12:00:00Z"
  }
}
```

---

## Authentication

- **Mechanism:** Starlette `SessionMiddleware` with `SESSION_SECRET`
- **Password:** bcrypt via passlib; minimum 8 characters
- **Dependencies:** `get_current_user`, `require_admin` FastAPI dependencies
- **Bootstrap:** Create admin from `ADMIN_EMAIL` + `ADMIN_PASSWORD` when no admin exists

---

## Configuration

New `.env` variables:

```env
# PostgreSQL (Neon)
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname?sslmode=require

# Session
SESSION_SECRET=your-secret-key-here

# Admin bootstrap
ADMIN_EMAIL=admin@healthpilot.local
ADMIN_PASSWORD=change-me-on-first-run

# Qdrant (local Docker)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Embeddings (Mesh API — reuses OPENAI_BASE_URL + OPENAI_API_KEY)
EMBEDDING_MODEL=text-embedding-3-small
PRODUCTS_COLLECTION=healthpilot_products

# Sync job
VECTOR_SYNC_INTERVAL_SECONDS=30
VECTOR_SYNC_MAX_ATTEMPTS=10
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Postgres down | 503 |
| Qdrant down on write | Postgres succeeds; status `failed`; scheduler retries |
| Mesh API failure | Same as Qdrant down |
| Invalid session | 401, clear cookie |
| Non-admin on admin route | 403 |
| Duplicate email | 409 |

Extend existing `HealthPilotException` with `AuthError`, `ProductNotFoundError`, `SyncError`.

---

## Testing

| Layer | Coverage |
|---|---|
| Unit | VectorSyncService status transitions (mocked Mesh + Qdrant) |
| Unit | AuthService password hash/verify |
| Unit | ProductService CRUD and soft-delete |
| Integration | Auth flow: register → login → /me → logout |
| Integration | Admin CRUD with test Postgres |
| Integration | Sync job picks up pending after simulated failure |
| Manual | Swagger full admin product lifecycle with Qdrant Docker |

---

## Completion Criteria

- [ ] Alembic migrations create `users` + `products`
- [ ] Admin login via Swagger (session cookie set); user registration works for `user` role
- [ ] Admin CRUD products; public list/view active products
- [ ] Product create/update triggers Qdrant upsert via Mesh embeddings
- [ ] Failed sync marks `failed`; APScheduler retries within 30s
- [ ] Manual resync endpoints work
- [ ] `/health` reports Postgres + Qdrant + privacy pipeline
- [ ] `.env.example` and `docs/RUN.md` updated

---

## Future Phases (reference)

| Phase | Focus |
|---|---|
| Phase 2 | Jinja2 frontend, event tracking, public marketplace UI |
| Phase 3 | LangGraph recommendation agents, RAG, triggers/caching |
| Phase 4 | Blood reports, lifestyle signals, proactive delivery |

---

## Route Registration

```text
/api/v1/auth            → auth.router
/api/v1/products        → products.router
/api/v1/admin/products  → admin/products.router
/api/v1/admin/sync      → admin/sync.router
/api/v1/privacy         → privacy.router (unchanged)
```
