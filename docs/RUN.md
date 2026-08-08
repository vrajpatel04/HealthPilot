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
