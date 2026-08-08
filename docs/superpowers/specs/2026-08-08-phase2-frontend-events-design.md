# HealthPilot Phase 2: Frontend, Events & Admin Dashboard Design

**Date:** 2026-08-08  
**Status:** Approved  
**Scope:** Jinja2 marketplace UI, admin dashboard, behavioral event tracking  
**Depends on:** Phase 1 foundation (auth, products API, dual-write sync)

---

## Decisions

| Decision | Choice |
|---|---|
| Scope | Marketplace UI + event tracking together |
| Admin | Jinja2 admin dashboard (CRUD + sync status) |
| Styling | Tailwind CSS via CDN |
| Events | Spec-aligned (view, search, scroll, return, time-on-page) |
| Search | Keyword search on Postgres (`ILIKE`) |
| Routing | Separate web router; `/api/v1/*` stays JSON |
| Access | Anonymous browse; login optional |
| Architecture | Approach 1 — server-rendered pages + shared services |

---

## Phase 2 Scope

### In scope

- Jinja2 templates + Tailwind CDN
- Public marketplace pages (home, product list, product detail)
- Auth pages (login, register) as HTML forms
- Admin dashboard (product CRUD, sync status, manual resync)
- `events` table + Alembic migration
- `POST /api/v1/events/batch`
- Client-side event tracker (`event-tracker.js`)
- Keyword search (`?q=`) on products API and web
- Anonymous `hp_anon_session` cookie for event attribution

### Out of scope (Phase 3+)

- Recommendation agents and LangGraph workflows
- RAG / semantic (Qdrant) search
- Coach chat UI
- Behavior Agent analysis of events
- Proactive email delivery
- Blood report upload
- Lifestyle signals

---

## Architecture

### Layered structure (extends Phase 1)

```text
src/healthPilot/
├── web/
│   ├── router.py
│   ├── deps.py
│   ├── marketplace.py
│   ├── auth_pages.py
│   └── admin_pages.py
├── templates/
│   ├── base.html
│   ├── marketplace/
│   ├── auth/
│   └── admin/
├── static/
│   ├── js/event-tracker.js
│   └── css/app.css
├── api/endpoints/events.py
├── models/event.py
├── repositories/event_repository.py
├── services/event_service.py
└── schemas/event.py
```

### Request flow

```text
GET /products?q=sleep
    → web/marketplace.py → ProductService → Jinja2

POST /api/v1/events/batch
    → events.py → EventService → Postgres (bulk insert)

GET /admin/products
    → web/admin_pages.py → require_admin → ProductService → Jinja2
```

Web routes call services directly. Event tracker is the only browser → JSON API caller for page flows.

### Tech additions

- FastAPI `Jinja2Templates` + `StaticFiles`
- Existing session cookie for auth; new `hp_anon_session` for anonymous events
- Tailwind via CDN in `base.html` — no npm build step

---

## Pages & Routes

### Public marketplace

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | None | Home — hero + category cards |
| GET | `/products` | None | Product grid; `?category=`, `?q=`, `?page=` |
| GET | `/products/{id}` | None | Product detail + scroll tracker |
| GET | `/login` | None | Login form |
| GET | `/register` | None | Register form |
| POST | `/login` | None | Form POST → session cookie → redirect `/products` |
| POST | `/register` | None | Form POST → redirect `/login` |
| POST | `/logout` | Optional | Clear session → redirect `/` |

### Admin dashboard

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/admin/products` | Admin | Product table with sync status badges |
| GET | `/admin/products/new` | Admin | Create form |
| POST | `/admin/products/new` | Admin | Create → redirect list |
| GET | `/admin/products/{id}/edit` | Admin | Edit form |
| POST | `/admin/products/{id}/edit` | Admin | Update → redirect list |
| POST | `/admin/products/{id}/delete` | Admin | Soft-delete → redirect list |
| POST | `/admin/sync/retry` | Admin | Trigger sweep → flash message |
| POST | `/admin/sync/products/{id}` | Admin | Force resync single product |

Admin uses HTML form POSTs. Reuses `ProductService` and `VectorSyncService`.

### JSON API changes

| Method | Path | Change |
|---|---|---|
| GET | `/api/v1/products` | Add `?q=` keyword search (`ILIKE` on title + description) |
| POST | `/api/v1/events/batch` | **New** — batch event ingest |
| Other `/api/v1/*` | Unchanged — Swagger/testing still supported |

### Layout (`base.html`)

- Tailwind CDN + minimal `app.css`
- Nav: logo, category links, search bar, login/logout
- Admin nav link when `user.role == admin`
- `event-tracker.js` on marketplace pages only
- Flash messages for admin actions

---

## Events Data Model

### `events` table

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | `gen_random_uuid()` |
| `user_id` | UUID (FK → users) | Nullable when anonymous |
| `session_id` | VARCHAR(64) | From `hp_anon_session`; always set |
| `event_type` | ENUM | See below |
| `product_id` | UUID (FK → products) | Nullable |
| `metadata` | JSONB | Event-specific payload |
| `timestamp` | TIMESTAMPTZ | Client time |
| `created_at` | TIMESTAMPTZ | Server insert time |

### Event type enum

```text
page_view
product_view
search
category_filter
description_scroll
product_return
time_on_page
```

### Metadata examples

```json
{ "query": "sleep improvement", "results_count": 4 }
{ "scroll_percent": 72 }
{ "visit_count": 2 }
{ "duration_seconds": 48, "page": "/products/abc" }
{ "category": "sleep" }
```

### Anonymous session

- Cookie: `hp_anon_session` (UUID, HttpOnly, SameSite=Lax, 30-day expiry)
- Set on first HTML response if missing
- After login: events include both `session_id` and `user_id`

---

## Batch API

### `POST /api/v1/events/batch`

**Request**
```json
{
  "events": [
    {
      "event_type": "product_view",
      "product_id": "550e8400-e29b-41d4-a716-446655440000",
      "metadata": {},
      "timestamp": "2026-08-08T14:30:00Z"
    }
  ]
}
```

**Rules**
- Auth optional; `user_id` from session when logged in
- `session_id` from `hp_anon_session` cookie (required)
- Max 50 events per batch
- Reject timestamps > 5 minutes in the future
- Response: `202 Accepted` `{ "accepted": 12 }`
- No LLM calls — Postgres INSERT only

---

## JS Event Tracker

### Flow

```text
Page load → EventTracker.init({ pageType, productId? })
         → in-memory queue
         → flush every 5s | ≥10 events | beforeunload (sendBeacon)
         → POST /api/v1/events/batch (credentials: include)
```

### Per-page events

| Page | Events |
|---|---|
| Any marketplace page | `page_view` |
| `/products? q=` | `search` |
| `/products?category=` | `category_filter` |
| `/products/{id}` | `product_view` |
| Product detail scroll | `description_scroll` at 25/50/75/100% |
| Product revisit (session) | `product_return` via localStorage |
| Page unload | `time_on_page` |

### Throttling

- Scroll: max 1 event per 25% band per visit
- Search: debounce 500ms; 1 per submitted search
- Flush: 5s interval, 10-event cap, `sendBeacon` on unload

Admin pages do not load the tracker.

---

## Keyword Search

Extend `ProductRepository.list_products()`:

```sql
WHERE (title ILIKE '%' || :q || '%' OR description ILIKE '%' || :q || '%')
  AND is_active = true
```

Web search bar: `GET /products?q=...` (server-rendered).  
`search` event fired on results page with query + count in metadata.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Invalid event_type | 422 |
| Batch > 50 events | 422 |
| Missing session cookie | 400 |
| Future timestamp (>5 min) | 422 for that event; skip or reject batch |
| Non-admin on `/admin/*` | Redirect to `/login` with flash |
| Product not found (web) | 404 HTML page |

---

## Testing

| Layer | Coverage |
|---|---|
| Unit | `EventService.ingest_batch` validation and bulk insert |
| Unit | Keyword search filter in `ProductRepository` |
| Integration | POST `/api/v1/events/batch` with session cookie |
| Integration | Web login form sets session; admin guard redirects |
| Manual | Browse products anonymously → events in DB |
| Manual | Login → product views attributed to `user_id` |
| Manual | Admin CRUD via dashboard; sync badges update |

---

## Completion Criteria

- [ ] Alembic migration creates `events` table
- [ ] Marketplace pages render at `/`, `/products`, `/products/{id}`
- [ ] Login/register/logout work via HTML forms + session cookies
- [ ] Admin dashboard: product CRUD + sync status + manual resync
- [ ] Keyword search works on web and API (`?q=`)
- [ ] Event tracker fires spec-aligned events; batches land in Postgres
- [ ] Anonymous events use `hp_anon_session`; logged-in events include `user_id`
- [ ] `docs/RUN.md` updated with Phase 2 setup and demo flow

---

## Demo Flow (Rahul journey)

1. Visit `/` anonymously → `page_view`
2. Click Sleep category → `category_filter`
3. Search "sleep improvement" → `search`
4. Open product → `product_view`
5. Scroll description → `description_scroll`
6. Register/login → later events get `user_id`
7. Return to same product → `product_return`
8. Admin adds product via `/admin/products/new` → sync badge shows `synced`

---

## Route Registration

```text
/                       → web/marketplace (home)
/products               → web/marketplace
/products/{id}          → web/marketplace
/login, /register       → web/auth_pages
/admin/*                → web/admin_pages
/api/v1/events          → api/endpoints/events
/api/v1/*               → unchanged JSON API
/static/*               → StaticFiles
```
