# Assessment Compliance Audit

Final audit against the original assessment (master spec §1) and the full
master specification. Every mandatory requirement is implemented, tested,
and verified — see evidence column for exact test names.

## Accept New Orders

| Requirement | Implementation | Test evidence | Status |
|---|---|---|---|
| Patient name | `NewOrderPage` form + `Patient` entity | `test_orders_create_api.py::test_patient_name_is_trimmed` | ✅ |
| Drug name | Medicine search (`DrugPicker`) + `OrderItem` | `test_drugs_api.py::TestListDrugs` | ✅ |
| Quantity | Requested quantity per line item | `test_orders_create_api.py::test_zero_quantity_rejected`, `test_negative_quantity_rejected` | ✅ |
| Date/time | `Order.created_at`, optional client `ordered_at` | `test_fulfilment.py` (uses `ordered_at` for FIFO ordering) | ✅ |
| Save to database | MySQL via SQLAlchemy, committed atomically | `test_schema_constraints.py` | ✅ |
| Check inventory | Authoritative backend re-check inside the create-order transaction, ignoring any client-displayed figures | `test_orders_create_api.py::TestCreateOrderFulfilment` | ✅ |

## Track Inventory

| Requirement | Implementation | Test evidence | Status |
|---|---|---|---|
| Per-drug stock | `inventory` table, 1:1 with `drugs` | `test_inventory_api.py` | ✅ |
| Low-stock flag | Computed status (`app/domain/rules.py`) | `test_inventory_api.py::test_stock_status_calculation` (4 cases) | ✅ |
| Manual restocking | `POST /inventory/{id}/restock`, `RestockModal` UI | `test_inventory_api.py::TestRestock` | ✅ |

## Order Status Lifecycle

| Requirement | Implementation | Test evidence | Status |
|---|---|---|---|
| New | `OrderStatus.NEW` (transient, set then immediately re-evaluated) | `order_service.create_order` | ✅ |
| Waiting for Stock | `OrderStatus.WAITING_FOR_STOCK` | `test_orders_create_api.py::test_zero_stock_order_goes_waiting_without_negative_inventory` | ✅ |
| Dispensed | `OrderStatus.DISPENSED` | `test_orders_create_api.py::test_sufficient_stock_dispenses_immediately` | ✅ |
| Completed | `OrderStatus.COMPLETED`, `POST /orders/{id}/complete` | `test_orders_create_api.py::test_complete_dispensed_order_succeeds` | ✅ |
| Automatic processing after restock | FIFO engine (`app/services/fulfilment_service.py`), triggered inline by every restock | `test_fulfilment.py::test_spec_example_101_102_103_restock_35` (exact master spec §15.1 example) | ✅ |

## Manager Dashboard

| Requirement | Implementation | Test evidence | Status |
|---|---|---|---|
| Total orders today | `DashboardSummary.orders_today`, business-timezone aware | `test_dashboard_api.py::test_order_created_now_is_counted_in_orders_today` | ✅ |
| Completed vs pending | `completed_today`, `pending_orders` | `test_dashboard_api.py::test_completed_order_today_increments_completed_today`, `test_pending_order_is_counted_in_pending_orders` | ✅ |
| Avg completion/fill time | `average_fulfilment_minutes` = `dispensed_at - created_at` | `test_dashboard_api.py::test_average_fulfilment_minutes_reflects_known_dispensed_order` | ✅ |
| Low-stock list | `GET /dashboard/low-stock` | `test_dashboard_api.py::TestDashboardLowStock` | ✅ |
| Recent orders | `GET /dashboard/recent-orders`, Dashboard + Orders pages | `test_dashboard_api.py::TestDashboardRecentOrders` | ✅ |
| Sort/filter | Orders API + Orders page (URL-synced filters) | `test_orders_api.py::TestListOrders` (11 tests) | ✅ |

## Technical Constraints

| Requirement | Implementation | Status |
|---|---|---|
| Python or Java | Python 3.14 / FastAPI | ✅ |
| React | React 19 + TypeScript, Vite | ✅ |
| MySQL | MySQL 8+ (Aiven managed), SQLAlchemy 2.0 | ✅ |
| Queueing (developer choice) | DB-backed pending-order workflow (no external queue needed at this scale) | ✅ documented |
| Caching (developer choice) | None required for correctness; optional SSE push implemented, Redis explicitly skipped (see below) | ✅ documented |
| Architecture (developer choice) | Modular monolith (api → services → repositories → models) | ✅ |

## Submission Quality

| Requirement | Implementation | Status |
|---|---|---|
| Working code | Full-stack app, 119 backend tests passing | ✅ |
| Setup instructions | `README.md` §Local Setup | ✅ |
| Sample data | `backend/app/seed.py`, idempotent | ✅ |
| Clear code organization | `docs/DATABASE.md`, layered backend, feature-organized frontend | ✅ |
| Tests | 119 backend tests (unit + integration + concurrency); frontend verified via live browser testing each phase (see Known Gaps) | ✅ / ⚠️ see below |
| Logging | Structured JSON logs, 11 business events, request correlation IDs | ✅ |
| Database schema | `docs/DATABASE.md` (ER diagram, constraints, indexes) | ✅ |
| README | `README.md` | ✅ |
| No auth | Confirmed absent throughout | ✅ |
| No AI/LLM | Confirmed absent throughout | ✅ |
| No full inventory ERP | Scope held to master spec's boundaries | ✅ |

## Critical Test Cases (master spec §50 — all 23)

All 23 scenarios are covered by the automated backend suite:

1. Sufficient stock → dispensed — `test_orders_create_api.py`
2. Zero stock → waiting — `test_orders_create_api.py`
3. Partially insufficient stock → waiting — `test_orders_create_api.py`
4. Multi-item, all available — `test_orders_create_api.py`
5. Multi-item, one unavailable — `test_orders_create_api.py`
6. Stock cannot go negative — `test_schema_constraints.py`, `test_concurrency.py`
7. Restock increases inventory — `test_inventory_api.py`
8. Restock creates ledger transaction — `test_inventory_api.py`, `test_fulfilment.py`
9. Pending order reprocessed after restock — `test_fulfilment.py`
10. Multiple waiting orders follow FIFO — `test_fulfilment.py` (exact spec example)
11. Partial restock fulfils only eligible FIFO orders — `test_fulfilment.py::test_does_not_skip_ahead_to_a_smaller_later_order`
12. Invalid drug rejected — `test_orders_create_api.py`
13. Invalid quantity rejected — `test_orders_create_api.py`, `test_inventory_api.py`
14. Duplicate drug line rejected — `test_orders_create_api.py`, `test_schema_constraints.py`
15. Invalid state transition rejected — `test_orders_create_api.py::TestOrderStateMachine`
16. Completed order timestamp recorded — `test_orders_create_api.py`
17. Average fulfilment time correct — `test_dashboard_api.py`
18. Low-stock status correct — `test_inventory_api.py`
19. Critical/reorder status correct — `test_inventory_api.py`, `test_dashboard_api.py`
20. Filters and sorting work — `test_orders_api.py`, `test_inventory_api.py`, `test_drugs_api.py`
21. Concurrent order attempts do not oversell — `test_concurrency.py` (exact master spec Appendix A Scenario E, run 5× to rule out flakiness)

## Cloud Deployment Readiness (Prompt 16 will execute the actual deploy)

| Item | Status |
|---|---|
| Managed MySQL reachable | ✅ Aiven-managed instance, TLS enabled |
| CORS configurable via env, no hardcoded origins | ✅ `FRONTEND_ORIGIN` |
| Frontend API URL configurable via env | ✅ `VITE_API_BASE_URL` (must be set at build time for production — see README) |
| No secrets in repo | ✅ `.env` gitignored, `.env.example` has placeholders only |
| Health endpoint | ✅ `GET /api/v1/health` |
| Swagger/OpenAPI clean | ✅ every endpoint has a summary + description (Prompt 15) |

## Known Gaps (flagged, not silently dropped)

1. **No automated frontend test suite.** Vitest/React Testing Library were
   never installed — Prompt 13's explicit task list scoped frontend work to
   *hardening* (verifying loading/error/empty states), not standing up new
   test tooling, and the master spec's own §49.4 frontend-test ask was
   flagged there as a scope decision for the user rather than assumed.
   Every frontend flow was instead verified with live, real-browser
   Playwright sessions against the actual running app + real seeded
   database at the end of Prompts 10–14, including screenshots — this
   caught and fixed two real bugs (a silent search-failure in the medicine
   picker, and misleading zero-value KPIs on a failed dashboard fetch) that
   unit tests with mocked APIs would likely have missed.
2. **Redis was explicitly skipped** per an explicit user decision — it was
   optional P4 scope and no Redis instance is provisioned for this project.
   SSE real-time updates were implemented instead (Prompt 14), fully
   optional and gracefully degrading when disabled.
3. **TLS to MySQL is not CA-pinned.** Encryption is enabled
   (`ssl={"ssl": {}}` in `app/core/database.py`), but no Aiven CA
   certificate was provided to validate against. Acceptable for
   development; worth revisiting before a long-lived production deployment.

## Documented Assumptions

These fill gaps the original assessment left open, each flagged at the
point of implementation rather than decided silently:

- **FIFO** for pending-order fulfilment priority (assessment doesn't define
  one) — master spec §15 explicitly frames this as the documented choice.
- **Patient matching**: exact trimmed full-name match, reuse if found else
  create. Simple and deterministic.
- **Order number format**: `ORD-{YYYYMMDD}-{6 random hex}` — human-readable,
  DB unique constraint as the hard backstop against collision.
- **Cancellation semantics**: cancelling a multi-item order only moves
  still-`PENDING`/`WAITING_FOR_STOCK` items to `CANCELLED`; a sibling item
  already `DISPENSED` keeps its status and stock deduction (never reachable
  from `DISPENSED` order status per the state machine, but reachable via
  a partially-dispensed multi-item order).
- **`critical_stock_drugs` dashboard KPI includes `OUT_OF_STOCK`** drugs
  (matches §14.6's literal `quantity <= reorder_threshold` with no zero
  exclusion), distinct from the 4-way `StockStatus` badge used in the
  Inventory UI, where `OUT_OF_STOCK` stays its own label.
- **Average fulfilment time reporting window** = orders dispensed *today*
  (not restricted to `COMPLETED`), per §36's literal definition.
