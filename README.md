# Pharmacy Order & Inventory Dashboard

A production-minded internal operations platform for a pharmacy chain to
capture prescription orders, track inventory in real time, and
automatically fulfil orders as stock arrives — built with React, FastAPI,
and MySQL.

---

## 1. Project Overview

Pharmacy staff capture a prescription order for a patient, selecting one
or more medicines and quantities. The system checks live inventory: if
enough stock exists, the order is dispensed immediately; if not, it waits.
Managers restock inventory manually, which automatically re-evaluates
every waiting order for that drug in FIFO order and dispenses whatever it
now can. A manager dashboard surfaces today's order volume, completion
rate, average fulfilment time, and which drugs need attention.

This is an internal operations tool for pharmacy staff and managers — not
a customer-facing ecommerce application. There is no login, no payment,
and no AI involved anywhere in the system.

## 2. Business Problem

> A pharmacy chain needs a system to track prescription orders and
> inventory in real time. Staff enter a prescription; the system checks
> stock; if available, it's dispensed; if not, the order waits until
> restocked. A manager dashboard shows orders today, completion status,
> low-stock drugs, average fulfilment time, and drugs needing urgent
> reorder.

## 3. Features

- **Order capture** — patient name, one or more medicines with quantities,
  live (informational) stock preview while building the order
- **Authoritative backend validation** — the backend re-checks real stock
  inside a database transaction at confirmation time; it never trusts
  whatever the browser last displayed
- **Automatic waiting-order fulfilment (FIFO)** — restocking a drug
  immediately re-evaluates every order waiting on it, oldest first
- **Inventory management** — current stock, configurable low-stock/reorder
  thresholds, computed status badges, manual restock with an audit note
- **Full inventory ledger** — every stock movement (restock, dispense,
  adjustment) recorded with quantity before/after and the order it's tied
  to, if any
- **Manager dashboard** — orders today, completed vs. pending, average
  fulfilment time, low/critical stock, recent orders, pending orders
- **Search, filter, sort, paginate** — on both the Orders and Inventory
  pages, state synced to the URL (bookmarkable/shareable)
- **Optional live updates (SSE)** — open pages refresh automatically when
  another user changes data, with graceful degradation if disabled or
  disconnected (see [§9](#9-fifo-restock-behaviour))

## 4. Architecture

**Modular monolith** — right-sized for this project: strong module
boundaries (API → services → repositories → models) without
distributed-system overhead.

```text
┌───────────────────────────────┐
│ React + TypeScript Frontend   │
│ (Vite, TanStack Query)        │
└──────────────┬─────────────────┘
               │ HTTPS REST + optional SSE
               ▼
┌───────────────────────────────┐
│ FastAPI Backend                │
│  api/      thin controllers    │
│  services/ business logic      │
│  repositories/ query layer     │
│  domain/   rules, state machine│
│  events/   optional SSE bus    │
└──────────────┬─────────────────┘
               │ SQLAlchemy
               ▼
┌───────────────────────────────┐
│ MySQL — authoritative store    │
└───────────────────────────────┘
```

MySQL is the single source of truth for every order and inventory
decision. The frontend's displayed stock is informational only.

## 5. Technology Stack

**Backend:** Python 3.11+, FastAPI, Pydantic, SQLAlchemy 2.0, Alembic,
PyMySQL, Pytest

**Frontend:** React 19, TypeScript, Vite, React Router, TanStack Query,
CSS Modules (a small internal design system, no heavy UI kit)

**Database:** MySQL 8+

**Optional:** Server-Sent Events for live updates (implemented, off by
default). Redis was considered and explicitly skipped for this project.

## 6. Folder Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, lifespan, middleware
│   │   ├── api/v1/             # Thin route handlers, one file per resource
│   │   ├── core/                # config, database, logging, exceptions
│   │   ├── domain/              # enums, business rules, state machine
│   │   ├── events/              # optional SSE broadcaster
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── repositories/        # query layer
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── services/            # business logic, transactions
│   │   └── seed.py              # idempotent demo data
│   ├── alembic/                 # migrations
│   ├── tests/{unit,integration}/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                 # typed fetch functions per resource
│       ├── app/                 # router, providers, error boundary
│       ├── components/{ui,layout,feedback}/  # shared design system
│       ├── features/{orders,inventory,dashboard,drugs}/  # TanStack Query hooks
│       ├── pages/                # one component per route
│       ├── types/                # wire-format TypeScript types
│       └── utils/
```

## 7. Database Schema Summary

Six tables: `patients`, `drugs`, `inventory` (1:1 with drugs),
`orders`, `order_items`, `inventory_transactions` (the stock ledger).
Stock status (`HEALTHY`/`LOW_STOCK`/`CRITICAL`/`OUT_OF_STOCK`) is computed
from thresholds, never stored, so it can never drift out of sync across
endpoints.

## 8. Order State Model

```text
NEW ──────────────┬──► WAITING_FOR_STOCK ──► DISPENSED ──► COMPLETED
                   │           │
                   └──► DISPENSED
                                └──────────► CANCELLED

NEW ──► CANCELLED
```

- **NEW** — very short-lived; immediately re-evaluated on creation
- **WAITING_FOR_STOCK** — at least one item can't be fulfilled yet
- **DISPENSED** — every item has been allocated/deducted
- **COMPLETED** — terminal, staff-confirmed
- **CANCELLED** — only reachable from `NEW` or `WAITING_FOR_STOCK`

Each `OrderItem` has its own status (`PENDING`/`WAITING_FOR_STOCK`/
`DISPENSED`/`CANCELLED`); the parent order's status is *derived* from its
items, computed in one place (`app/domain/state_machine.py` +
`order_service`/`fulfilment_service`), never duplicated.

Cancelling a multi-item order only moves items still
`PENDING`/`WAITING_FOR_STOCK` to `CANCELLED` — an item already `DISPENSED`
keeps its status and stock deduction (documented assumption — see
[§20](#20-assumptions)).

## 9. FIFO Restock Behaviour

When a drug is restocked, waiting order items for that drug are processed
**oldest order first**, and stop as soon as the next item in line can't be
fully covered — **never skipping ahead** to a smaller, later item, even if
it would otherwise fit.

Example (reproduced exactly by
`test_fulfilment.py::test_spec_example_101_102_103_restock_35`):

```text
Waiting: ORD-101 needs 10, ORD-102 needs 20, ORD-103 needs 20
Restock: +35

ORD-101 fulfilled → remaining 25
ORD-102 fulfilled → remaining 5
ORD-103 stays waiting (needs 20, only 5 left)
```

FIFO was not specified by the original assessment — it's a documented
project assumption (deterministic, fair, simple).

## 10. Concurrency & Inventory Integrity

Inventory is shared mutable state under concurrent access. Every mutation
path (order creation, restock, FIFO fulfilment) follows the same pattern:

1. `SELECT ... FOR UPDATE` locks the relevant inventory row(s) before
   evaluating availability
2. For multi-item orders touching several drugs, locks are acquired in
   **ascending `drug_id` order** — deterministic across all callers, so
   two concurrent orders sharing drugs can never deadlock each other
3. Stock is deducted (or left untouched) based on the row's value *at lock
   time*, never a value read earlier or supplied by the client
4. A transient lock-wait-timeout or deadlock (rare, since ordering
   prevents deadlocks by construction) surfaces as a clean `409
   INVENTORY_CONFLICT`, never an opaque 500

Proven, not just asserted: `test_concurrency.py` fires genuinely
concurrent requests (via `ThreadPoolExecutor`, actual OS threads with
separate DB connections) at a drug with exactly 10 units of stock — two
requests for 8 each. Exactly one succeeds; the other correctly sees the
updated inventory and waits. Run 5× in a row with no flakiness.

## 11. Environment Variables

**Backend** (`.env` at repo root; see `.env.example`):

| Variable | Purpose |
|---|---|
| `APP_NAME`, `APP_ENV`, `LOG_LEVEL` | App metadata, logging verbosity |
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` | Discrete DB connection vars (primary source — see `app/core/config.py`) |
| `DATABASE_URL` | Fallback DSN if discrete vars aren't all set |
| `FRONTEND_ORIGIN` | CORS allow-list |
| `BUSINESS_TIMEZONE` | Used for "today" boundaries in dashboard metrics |
| `REDIS_URL` | Unused (Redis was skipped) — reserved for future use |
| `ENABLE_REALTIME` | `true` to actually publish SSE events (default `false`) |

**Frontend** (`frontend/.env.local`; see `frontend/.env.example`):

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Backend API base URL. **Must be set at build time** — Vite bakes env vars into the production bundle |
| `VITE_ENABLE_REALTIME` | `true` to subscribe to the SSE stream |

Never commit `.env` or `frontend/.env.local` — both are gitignored.

## 12. Local Setup

Prerequisites: Python 3.11+, Node 18+, a reachable MySQL 8+ instance.

```bash
git clone <repo-url>
cd "Pharmacy assessment"
cp .env.example .env              # fill in real MySQL credentials
cp frontend/.env.example frontend/.env.local
```

Then follow §13–16 below in order (migrate → seed → run backend → run
frontend).

## 13. MySQL Migration Commands

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate          # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt

alembic upgrade head
```

## 14. Seed Command

```bash
cd backend
python -m app.seed
```

Idempotent — safe to re-run. Seeds 8 demo drugs covering every stock
status (HEALTHY/LOW_STOCK/CRITICAL/OUT_OF_STOCK) and 5 demo orders
covering every lifecycle state (WAITING_FOR_STOCK, DISPENSED, COMPLETED,
including a multi-item order with mixed item availability).

## 15. Backend Run Command

```bash
cd backend
uvicorn app.main:app --reload
```

- API base: `http://localhost:8000/api/v1`
- Health check: `http://localhost:8000/api/v1/health`

## 16. Frontend Run Command

```bash
cd frontend
npm install
npm run dev
```

- App: `http://localhost:5173`

## 17. Test Commands

```bash
cd backend
pytest              # all 119 tests
pytest tests/unit           # fast, no DB
pytest tests/integration    # exercises the real configured MySQL database
```

Integration tests run against the real database configured in `.env`.
Schema/constraint tests use a per-test transaction that's always rolled
back; other tests create and clean up their own throwaway drugs/orders, so
the suite never disturbs the seeded demo data.

There is currently no automated frontend test suite. Frontend behavior was
instead verified through live, real-browser testing against the running
app and a real seeded database at each development stage.

## 18. API Docs URL Pattern

With the backend running:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Raw OpenAPI schema: `http://localhost:8000/openapi.json`

Every endpoint has a `summary` and a descriptive docstring.

## 19. Cloud Deployment Notes

Not yet deployed live — this repository is deployment-ready but the
actual deploy is a separate, explicit step (recommended platforms below):

| Component | Recommended platform |
|---|---|
| Frontend | Vercel |
| Backend | Railway, Render, or comparable Python/container platform |
| Database | Managed MySQL (already using Aiven for local development) |

Before deploying:
- Set `FRONTEND_ORIGIN` (backend) to the real deployed frontend URL — not
  `localhost`
- Set `VITE_API_BASE_URL` (frontend) to the real deployed backend URL at
  **build time**
- Run `alembic upgrade head` and `python -m app.seed` against the
  production database
- Verify `/api/v1/health`, `/docs`, and the full order → waiting → restock
  → auto-fulfil → complete demo flow against the live URLs

## 20. Assumptions

Documented decisions filling gaps the original assessment left open:

- **FIFO** for pending-order fulfilment priority (not specified by the
  assessment) — deterministic, fair, and simple to reason about.
- **Patient matching**: exact trimmed full-name match; reuses the existing
  patient record if found, otherwise creates one.
- **Order number format**: `ORD-{YYYYMMDD}-{6 random hex characters}` —
  human-readable, with the database's unique constraint as the hard
  backstop against collision.
- **Cancellation semantics**: cancelling a multi-item order only moves
  items still `PENDING`/`WAITING_FOR_STOCK` to `CANCELLED`; an item already
  `DISPENSED` keeps its status and stock deduction.
- **Dashboard "Critical / Urgent Reorder" KPI** includes `OUT_OF_STOCK`
  drugs (a quantity of 0 still satisfies `<= reorder_threshold`) — distinct
  from the 4-way stock-status badge shown on the Inventory page, where
  `OUT_OF_STOCK` stays its own label.
- **Average fulfilment time** covers orders dispensed *today*, not only
  ones that have also been marked `COMPLETED`.

## 21. Scope Boundaries

Explicitly **not** built, matching the original assessment's boundaries:

Authentication/login, role-based access control, customer accounts,
shopping cart, payment gateway, delivery tracking, prescription OCR, AI/LLM
APIs, insurance claims, doctor verification, GST/billing, supplier
procurement ERP, multi-warehouse logistics, full pharmacy ERP, Kubernetes,
Kafka/RabbitMQ, Elasticsearch, microservices, mandatory Docker, mandatory
CI/CD.

Redis was in scope as an *optional* enhancement and was explicitly
descoped (no Redis instance provisioned for this project) — SSE-based live
updates were implemented instead, fully optional and gracefully degrading.
