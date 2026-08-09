# HealthPilot — Run Guide

Backend API with PostgreSQL, Qdrant vector sync, session auth, and embedded privacy pipeline.

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| [uv](https://docs.astral.sh/uv/) | Python dependencies |
| Python 3.12+ | Backend runtime |
| Neon (or other) PostgreSQL | Primary database |
| Docker | Local Qdrant |

---

## 1. Configure environment

```powershell
cd D:\Projects\HealthPilot
copy .env.example .env
```

Set at minimum:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname?sslmode=require
SESSION_SECRET=generate-a-long-random-string
ADMIN_EMAIL=admin@healthpilot.local
ADMIN_PASSWORD=change-me-on-first-run
QDRANT_URL=http://localhost:6333
OPENAI_BASE_URL=https://api.meshapi.ai/v1
OPENAI_API_KEY=rsk_your-key-here
EMBEDDING_MODEL=text-embedding-3-small
```

---

## 2. Start Qdrant (Docker)

```powershell
docker run -p 6333:6333 qdrant/qdrant
```

---

## 3. Install dependencies

```powershell
uv sync
```

---

## 4. Run database migrations

```powershell
uv run alembic upgrade head
```

---

## 5. Start the backend

```powershell
uv run python app.py
```

Backend: **http://localhost:8000**  
Swagger: **http://localhost:8000/docs**

On startup you should see PostgreSQL, Qdrant, Presidio, and NeMo status lines. The admin user is bootstrapped from `ADMIN_EMAIL` / `ADMIN_PASSWORD` if no admin exists.

---

## Phase 1 API overview

| Area | Base path |
|------|-----------|
| Auth | `/api/v1/auth` |
| Public products | `/api/v1/products` |
| Admin products | `/api/v1/admin/products` |
| Admin sync | `/api/v1/admin/sync` |
| Privacy coach | `/api/v1/privacy` |
| Health | `/health` |

### Quick test flow (Swagger)

1. `POST /api/v1/auth/login` with admin credentials (sets session cookie)
2. `POST /api/v1/admin/products` to create a product
3. `GET /api/v1/admin/products` to verify `vector_sync_status: synced`
4. `GET /api/v1/products` to list public catalog

---

## Tests

```powershell
uv sync --extra dev
uv run pytest tests/ -v
```

---

## Privacy pipeline

User-facing coach requests still use:

```text
Presidio → NeMo input → LLM → NeMo output → Presidio de-anonymize
```

See `/api/v1/privacy/coach` and `/api/v1/privacy/health`.

---

## Phase 2 — Web UI & event tracking

After migrations (`alembic upgrade head` includes the `events` table):

| Pages | URL |
|-------|-----|
| Home | http://localhost:8000/ |
| Marketplace | http://localhost:8000/products |
| Login | http://localhost:8000/login |
| Admin dashboard | http://localhost:8000/admin/products |

### Rahul demo flow

1. Visit `/` anonymously (sets `hp_anon_session` cookie)
2. Browse `/products?category=sleep` or search `?q=sleep`
3. Open a product detail page (scroll to fire `description_scroll`)
4. Register / log in at `/register` → `/login`
5. Revisit the same product → `product_return` event
6. Log in as admin → `/admin/products/new` to add a product

Events are stored in Postgres via `POST /api/v1/events/batch` (automatic from `event-tracker.js`).

Keyword search: `/products?q=sleep` or `GET /api/v1/products?q=sleep`.

### Seed sample products

```powershell
uv run python scripts/seed_products.py
```

Adds 8 wellness products from the project spec (skips any that already exist). Each product is synced to Qdrant via Mesh embeddings.

---

## Phase 3 — Recommendations & RAG

Run migration `003` (creates `user_memories`, `recommendations`, `feedback`):

```powershell
uv run alembic upgrade head
```

### Optional Redis

```powershell
docker run -p 6379:6379 redis:7
```

Set in `.env`:

```env
REDIS_URL=redis://localhost:6379/0
```

Without Redis, recommendations still work via Postgres-only caching.

### Seed RAG knowledge base

```powershell
uv run python scripts/seed_rag.py
```

Populates `healthpilot_knowledge` in Qdrant from `data/knowledge/*.md`.

### Phase 3 URLs

| Pages / API | URL |
|-------------|-----|
| For You page | http://localhost:8000/recommendations |
| Recommendations API | `GET /api/v1/recommendations` |
| Force refresh | `POST /api/v1/recommendations/refresh` |
| Feedback | `POST /api/v1/recommendations/feedback` |

### Rahul journey (Phase 3)

1. Browse anonymously and search `sleep improvement` → background trigger may generate a recommendation
2. Visit `/` — homepage widget shows top pick when available
3. Open `/recommendations` — full message, secondary pick, and “Why recommended?”
4. Click **Interested** or **Not for me** to record feedback
5. Click **Refresh recommendations** after more browsing
6. Log in — future recommendations link to your `user_id`

Conservative auto-triggers: new search, product return, or category filter + 2 views in 30 minutes (5-minute cooldown between runs).
