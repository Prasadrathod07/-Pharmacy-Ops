# Claude Code Implementation Prompts
## Pharmacy Order & Inventory Dashboard
### Controlled End-to-End Build Plan

**Purpose:** This file is the execution playbook for Claude Code.  
**Authoritative product specification:** `pharmacy_order_inventory_master_spec.md`  
**Secrets/config:** `.env`

---

# 0. GLOBAL EXECUTION CONTRACT

Claude Code must follow these rules for every prompt in this document.

## 0.1 Source of Truth

Before changing code in any phase:

1. Read `pharmacy_order_inventory_master_spec.md` completely.
2. Read the current repository structure and existing code.
3. Read the current phase from this file.
4. Treat the master specification as the authoritative product and architecture source.
5. If this file and the master specification conflict, the master specification wins unless the user explicitly approves a change.

## 0.2 Execution Discipline

- Execute **only the explicitly requested PROMPT number**.
- Do **not** automatically continue to the next prompt.
- Inspect and preserve working code from earlier phases.
- Do not rewrite previously correct modules merely for stylistic preference.
- If a required change impacts earlier phases, make the smallest safe change and explain it.
- Do not create hidden scope.
- Do not introduce features outside the approved scope.
- Do not skip tests/checks defined for the current phase.
- Do not mark a phase complete unless its acceptance gate passes.
- If blocked, stop and report the blocker clearly instead of guessing.

## 0.3 Security and Secret Handling

- `.env` exists locally and may contain database credentials.
- Never print `.env` values.
- Never echo secrets into terminal output.
- Never write secret values into code, logs, README, test fixtures, Swagger examples, or frontend bundles.
- Never commit `.env`.
- Ensure `.gitignore` contains `.env`.
- Create `.env.example` containing variable names and safe placeholders only.
- Read secrets only through application configuration.
- The frontend must never receive database credentials.

## 0.4 Approved Technology Direction

### Frontend
- React
- TypeScript
- Vite preferred
- React Router
- TanStack Query
- Professional B2B operational UI
- No marketing-website styling

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- Pytest

### Database
- MySQL 8+
- MySQL is the source of truth

### Optional Enhancements
- Redis
- Server-Sent Events (SSE)
- WebSocket only if there is a compelling reason

## 0.5 Architecture Guardrails

Use a **modular monolith**.

Do not introduce:

- Microservices
- Kafka
- RabbitMQ
- Kubernetes
- Elasticsearch
- Authentication/login
- Role-based access control
- Payment gateway
- Customer ecommerce
- Delivery tracking
- Prescription OCR
- AI/LLM APIs
- Full pharmacy ERP
- Docker as a required dependency
- CI/CD as a required project feature

## 0.6 Business Guardrails

- Inventory shown on the frontend is informational.
- Final stock validation happens on the backend.
- Inventory must never become negative.
- Inventory mutation must happen only through backend service logic.
- MySQL remains authoritative.
- Redis, if added, must never become the source of truth for inventory or order state.
- Waiting orders are persisted in MySQL.
- Pending order fulfilment after restock uses FIFO unless the user explicitly changes the rule.
- Order state transitions must be validated server-side.
- `DISPENSED` and `COMPLETED` are separate states.
- Restocking belongs to Inventory Management, not the Order form.
- Multiple medicines in one prescription/order are supported.
- No core business workflow may depend on realtime transport.

## 0.7 Quality Bar

The implementation should demonstrate experienced full-stack engineering:

- Clear domain modelling
- Safe database transactions
- Concurrency-aware inventory handling
- Clean module boundaries
- Strong validation
- Structured logging
- Consistent error responses
- Testability
- Traceability
- Maintainability
- Clean frontend UX
- Cloud readiness

Avoid overengineering.

## 0.8 Required Completion Report After Every Prompt

At the end of each executed prompt, report:

### PHASE COMPLETION REPORT

**Prompt executed:**  
**Status:** COMPLETE / PARTIAL / BLOCKED

**Files created:**  
- ...

**Files modified:**  
- ...

**Database changes:**  
- ...

**Tests/checks run:**  
- command
- result

**Acceptance criteria:**  
- [x] ...
- [ ] ...

**Master specification requirements completed in this phase:**  
- ...

**Known issues / follow-ups:**  
- ...

**Ready for next prompt:** YES / NO

Do not start the next prompt.

---

# PROMPT 00 — Repository Audit, Environment Safety, and Implementation Plan

## Objective

Prepare the repository safely before writing application features.

## Tasks

1. Read:
   - `pharmacy_order_inventory_master_spec.md`
   - this prompt file
   - `.env` variable names only, without printing values

2. Inspect the repository:
   - existing files
   - existing Git state if available
   - existing package/config files
   - existing backend/frontend folders

3. Verify `.gitignore` exists.
   - Add `.env`
   - Add Python cache/build artifacts
   - Add Node build artifacts
   - Add local IDE artifacts where appropriate

4. Create `.env.example` with safe placeholders for:
   - APP_NAME
   - APP_ENV
   - LOG_LEVEL
   - MYSQL_HOST
   - MYSQL_PORT
   - MYSQL_DATABASE
   - MYSQL_USER
   - MYSQL_PASSWORD
   - FRONTEND_ORIGIN
   - BUSINESS_TIMEZONE
   - REDIS_URL
   - ENABLE_REALTIME

5. Decide the exact repository structure consistent with the master spec:
   - `backend/`
   - `frontend/`
   - master spec
   - prompt file
   - README placeholder if needed

6. Do not yet implement business features.

7. Produce a concise implementation plan mapping:
   - database phase
   - backend domain phases
   - frontend phases
   - tests
   - deployment

8. Identify any environment blocker:
   - missing MySQL credentials
   - unreachable database
   - unsupported Python/Node version
   - invalid `.env`

## Important

Do not reveal secret values.

## Acceptance Gate

- `.env` is ignored
- `.env.example` exists
- repository structure is clear
- environment blockers are identified
- no business logic implemented yet
- completion report provided

---

# PROMPT 01 — Project Foundation and Core Configuration

## Objective

Create the backend and frontend foundations without implementing business features.

## Backend Tasks

1. Create FastAPI project structure following the master spec.

2. Add configuration system:
   - Pydantic settings or equivalent
   - environment-driven config
   - safe validation
   - no secret logging

3. Build MySQL connection configuration from separate environment variables.

4. Configure SQLAlchemy session management.

5. Configure Alembic.

6. Configure structured logging.

7. Add:
   - FastAPI app
   - API version prefix `/api/v1`
   - CORS based on `FRONTEND_ORIGIN`
   - global exception scaffolding
   - request ID/correlation ID middleware if practical

8. Add health endpoint:
   - `GET /api/v1/health`
   - application status
   - database connectivity
   - do not expose credentials

9. Create requirements/pyproject configuration.

## Frontend Tasks

1. Create React + TypeScript + Vite application.

2. Configure:
   - React Router
   - TanStack Query
   - API client base URL from `VITE_API_BASE_URL`
   - common error handling
   - core app layout placeholder

3. Create initial routes:
   - `/`
   - `/orders`
   - `/orders/new`
   - `/inventory`

4. Do not implement final page functionality yet.

## Checks

Backend:
- app starts
- health endpoint works
- database connectivity is verified safely

Frontend:
- app starts
- routes render placeholders

## Acceptance Gate

- FastAPI starts successfully
- React starts successfully
- MySQL connectivity works
- Alembic initialized
- structured logging initialized
- no secrets exposed
- no business feature drift

---

# PROMPT 02 — MySQL Schema, Models, Constraints, and Alembic Migration

## Objective

Implement the approved domain schema exactly and safely.

## Required Entities

Create:

1. `patients`
2. `drugs`
3. `inventory`
4. `orders`
5. `order_items`
6. `inventory_transactions`

## Required Model Behaviour

### patients
- id
- full_name
- created_at
- updated_at

### drugs
- id
- code unique
- name
- strength nullable
- dosage_form nullable
- is_active
- created_at
- updated_at

### inventory
- id
- drug_id unique FK
- quantity_on_hand >= 0
- low_stock_threshold >= 0
- reorder_threshold >= 0
- last_restocked_at nullable
- timestamps
- enforce reorder_threshold <= low_stock_threshold

### orders
- id
- order_number unique
- patient_id FK
- status
- created_at
- dispensed_at nullable
- completed_at nullable
- cancelled_at nullable
- updated_at

### order_items
- id
- order_id FK
- drug_id FK
- requested_quantity > 0
- status
- dispensed_quantity >= 0
- timestamps
- unique `(order_id, drug_id)`

### inventory_transactions
- id
- drug_id FK
- order_id nullable FK
- order_item_id nullable FK
- movement_type
- source
- quantity_delta
- quantity_before
- quantity_after
- note nullable
- created_at

## Enums / Constants

Create explicit backend enums for:

### OrderStatus
- NEW
- WAITING_FOR_STOCK
- DISPENSED
- COMPLETED
- CANCELLED

### OrderItemStatus
- PENDING
- WAITING_FOR_STOCK
- DISPENSED
- CANCELLED

### InventoryMovementType
- RESTOCK
- DISPENSE
- ADJUSTMENT

### InventoryMovementSource
- NEW_ORDER
- PENDING_FULFILMENT
- MANUAL_RESTOCK
- MANUAL_ADJUSTMENT

Use database-safe storage strategy.

## Indexes

Implement indexes described in the master spec, including:

- order number
- order status + created_at
- patient_id
- order_items order_id
- order_items drug_id + status
- drug code unique
- inventory drug_id unique
- inventory transaction drug_id + created_at
- transaction order_id
- transaction order_item_id

## Migration

Create Alembic migration.

Run migration against the configured MySQL database.

## Tests / Verification

Verify:
- tables created
- foreign keys exist
- uniqueness works
- negative inventory rejected
- zero/negative requested quantity rejected
- invalid thresholds rejected
- duplicate order drug line rejected

## Acceptance Gate

- migration succeeds
- schema matches master spec
- constraints are real, not only comments
- indexes exist
- models import cleanly
- tests/checks pass

---

# PROMPT 03 — Seed Data and Demo Dataset

## Objective

Create deterministic sample data for development and demonstration.

## Requirements

Create an idempotent seed script.

Seed drugs such as:

- Paracetamol 500 mg
- Amoxicillin 500 mg
- Azithromycin 250 mg
- Metformin 500 mg
- Atorvastatin 10 mg
- Cetirizine 10 mg
- Vitamin D3
- Omeprazole 20 mg

Create inventory examples covering:

- HEALTHY
- LOW_STOCK
- CRITICAL
- OUT_OF_STOCK

Create sample patients.

Create representative orders:

- COMPLETED
- DISPENSED
- WAITING_FOR_STOCK

Create inventory transaction history consistent with seeded inventory where practical.

## Requirements

- Seed script must be safe to re-run.
- Do not duplicate seed rows.
- Use deterministic drug codes.
- Demo data must support dashboard testing immediately.

## Verification

After seed:
- inventory screen can show all stock states
- dashboard has meaningful data
- at least one waiting order exists
- at least one completed order exists

## Acceptance Gate

- seed command documented
- seed is idempotent
- sample data is coherent
- no fake credentials embedded

---

# PROMPT 04 — Inventory Domain and Inventory APIs

## Objective

Implement the inventory module completely before order fulfilment.

## Backend Responsibilities

Create:

- inventory repository
- inventory service
- inventory schemas
- inventory routes

## Stock Status Rules

Implement one centralized function/service for stock status:

- OUT_OF_STOCK when quantity == 0
- CRITICAL when quantity <= reorder_threshold and quantity > 0
- LOW_STOCK when quantity <= low_stock_threshold and above reorder threshold
- HEALTHY otherwise

Do not duplicate this logic across API routes.

## APIs

### GET `/api/v1/inventory`

Support:
- search
- status
- low_stock_only
- critical_only
- sort
- pagination

Return:
- drug metadata
- quantity_on_hand
- thresholds
- computed stock status
- last_restocked_at

### GET `/api/v1/inventory/{drug_id}`

Return:
- drug
- inventory
- thresholds
- status
- recent transactions

### GET `/api/v1/inventory/{drug_id}/transactions`

Support:
- pagination
- movement type filter
- date filter

### POST `/api/v1/inventory/{drug_id}/restock`

Validate:
- drug exists
- inventory exists
- quantity > 0

Behaviour:
- transactionally increase stock
- write RESTOCK inventory transaction
- record before and after quantity
- update last_restocked_at
- do not yet implement pending FIFO processing in this prompt unless required only as a hook/event interface

## Concurrency

Restock must use a safe transaction and appropriate row locking.

## Tests

Test:
- inventory listing
- search
- all stock status calculations
- invalid restock quantity
- valid restock
- ledger creation
- quantity before/after
- nonexistent drug
- pagination

## Acceptance Gate

- inventory API complete
- restock safe
- ledger correct
- tests pass
- no pending-order processing yet unless only as interface stub

---

# PROMPT 05 — Drug Search and Order Query Foundations

## Objective

Build drug lookup and read-only order query capabilities required by the frontend.

## Drug APIs

### GET `/api/v1/drugs`

Support:
- `search`
- `page`
- `page_size`
- `active`

Return:
- id
- code
- name
- strength
- dosage form
- current inventory
- stock status

Use efficient queries.

### GET `/api/v1/drugs/{drug_id}`

Return:
- drug
- inventory
- stock status

## Order Read APIs

Create read/query infrastructure:

### GET `/api/v1/orders`

Support:
- search by order number or patient
- status
- drug_id
- date_from
- date_to
- sort_by
- sort_order
- page
- page_size

### GET `/api/v1/orders/{order_id}`

Return:
- order
- patient
- order items
- drug metadata
- item statuses
- timestamps
- fulfilment time when available

## Important

No final order creation logic yet. This phase establishes query/read paths.

## Tests

- drug search
- inactive drugs filtered appropriately
- order filters
- order sorting
- pagination
- order detail
- nonexistent resource handling

## Acceptance Gate

- drug search ready for New Order UI
- order read APIs stable
- filters/sorting/pagination tested

---

# PROMPT 06 — Order Creation, State Machine, and Transactional Fulfilment

## Objective

Implement the most important core business flow: create an order and safely fulfil it when stock is available.

## Order Creation API

Implement:

### POST `/api/v1/orders`

Request:

- patient_name
- ordered_at/date-time
- items:
  - drug_id
  - quantity

## Validation

- patient name required and trimmed
- at least one item
- quantity > 0
- all drugs exist
- all drugs active
- no duplicate drug IDs in one order
- valid timestamp

## Patient Behaviour

Use a clear documented strategy:
- either create a patient record for each submitted patient name
- or reuse by normalized exact name if intentionally designed

Prefer simple and deterministic behaviour.

## Order Number

Generate a unique, human-readable order number safely.

## Transactional Fulfilment

Inside an appropriate transaction:

1. Create patient/order/order items.
2. Lock relevant inventory rows in deterministic order to reduce deadlock risk.
3. Re-read authoritative inventory.
4. Evaluate each requested item.
5. Do not trust frontend stock.
6. If an item can be fulfilled:
   - deduct inventory
   - set item DISPENSED
   - set dispensed_quantity
   - create DISPENSE inventory transaction
7. If an item cannot be fulfilled:
   - set item WAITING_FOR_STOCK
   - do not make inventory negative
8. Compute parent order status.
9. Set dispensed_at when the entire order is considered dispensed.
10. Commit atomically.

## Important Business Decision

Follow the master spec for multi-item behaviour.

If at least one item is waiting:
- parent order is WAITING_FOR_STOCK

Do not silently invent unsupported reservation logic.

## State Machine

Implement centralized transition validation.

Allowed:
- NEW -> WAITING_FOR_STOCK
- NEW -> DISPENSED
- WAITING_FOR_STOCK -> DISPENSED
- WAITING_FOR_STOCK -> CANCELLED
- DISPENSED -> COMPLETED
- NEW -> CANCELLED

Reject invalid transitions.

## Additional APIs

### POST `/api/v1/orders/{order_id}/complete`

Only:
- DISPENSED -> COMPLETED

Set completed_at.

### POST `/api/v1/orders/{order_id}/cancel`

Allow only valid states.

Do not restore stock on cancellation unless the specific cancelled state has already consumed inventory and the master spec explicitly defines reversal behaviour. If not defined, document the behaviour before implementing.

## Tests

Must cover:
- one item sufficient
- one item insufficient
- multi-item all sufficient
- multi-item one insufficient
- no negative stock
- inventory transaction creation
- timestamps
- invalid drug
- duplicate drug
- zero quantity
- invalid state transitions
- order completion

## Acceptance Gate

- core order creation works
- stock mutation and order state are atomic
- no negative inventory
- state machine enforced
- tests pass

---

# PROMPT 07 — Concurrency Hardening and Oversell Protection

## Objective

Prove the system is safe under concurrent order creation.

## Required Scenario

Initial stock:

- Drug X = 10

Concurrent requests:

- Request A = 8
- Request B = 8

Expected:

- only one request may consume 8
- the other must see updated inventory and follow insufficient-stock behaviour
- quantity_on_hand must never be negative
- successful deduction has a ledger record
- no duplicate/corrupt transactions

## Tasks

1. Review transaction isolation and row locking.
2. Ensure inventory rows are locked before authoritative evaluation.
3. Ensure locks are acquired in deterministic drug-id order for multi-item orders.
4. Avoid long-running transaction scope.
5. Handle deadlock/conflict exceptions gracefully.
6. Return a consistent error or valid WAITING state according to implemented business flow.
7. Add integration/concurrency test.

## Logging

Log inventory conflicts without exposing sensitive data.

## Acceptance Gate

- concurrent test passes repeatedly
- stock never negative
- no double-spend
- transaction boundaries documented in code comments/docstrings where useful

---

# PROMPT 08 — FIFO Pending-Order Fulfilment After Restock

## Objective

Implement automatic processing of waiting orders when stock arrives.

## Trigger

After successful restock of a drug:

1. Identify waiting order items for that drug.
2. Sort by oldest order creation timestamp, then stable tiebreaker.
3. Process FIFO.
4. Use safe transactions and inventory locking.
5. Fulfil only when enough stock exists for the full waiting item.
6. Deduct stock.
7. Create inventory transaction with source `PENDING_FULFILMENT`.
8. Update item to DISPENSED.
9. Recompute parent order status.
10. If all order items are now DISPENSED:
    - set parent order DISPENSED
    - set dispensed_at
11. Leave remaining orders WAITING_FOR_STOCK.
12. Stop naturally when the next FIFO item cannot be fulfilled.

## Required Example Test

Waiting:
- ORD-101 = 10
- ORD-102 = 20
- ORD-103 = 20

Restock:
- +35

Expected:
- ORD-101 fulfilled
- ORD-102 fulfilled
- ORD-103 waiting
- remaining stock = 5

## Important

- Do not skip an older unfulfillable item to fulfil a younger item unless the master spec is explicitly changed.
- FIFO must be deterministic.
- Restock itself must remain successful even if post-restock processing encounters a recoverable problem; design transaction boundaries deliberately and document them.

## Tests

- one pending order
- multiple pending orders
- insufficient restock
- exact restock
- excess restock
- multi-item parent order recomputation
- no double fulfilment
- ledger correctness

## Acceptance Gate

- original assessment auto-dispense-after-restock requirement works
- FIFO verified
- remaining stock correct
- parent status correct
- tests pass

---

# PROMPT 09 — Dashboard Metrics and Operational APIs

## Objective

Implement the manager dashboard backend completely.

## Summary API

### GET `/api/v1/dashboard/summary`

Return:

- orders_today
- completed_today
- pending_orders
- average_fulfilment_minutes
- low_stock_drugs
- critical_stock_drugs

## Definitions

### Orders Today
Orders created within the configured business day.

### Completed Today
Orders with status COMPLETED and completed_at within the current business day.

### Pending
Orders with status WAITING_FOR_STOCK.

### Average Fulfilment Time
Primary:
- `dispensed_at - created_at`

Use orders dispensed within the relevant reporting window.

### Low Stock
Calculated from inventory threshold rules.

### Critical
Calculated from reorder threshold rules.

## Additional APIs

### GET `/api/v1/dashboard/recent-orders`

- pagination
- sorting
- filtering where useful

### GET `/api/v1/dashboard/low-stock`

Return low and critical inventory.

## Business Timezone

Use `BUSINESS_TIMEZONE`.

Avoid naive date handling.

## Performance

- use aggregate queries
- avoid N+1
- add indexes only if evidence/queries justify additional ones

## Tests

- date boundary
- completed vs pending
- average fulfilment math
- no fulfilled orders case
- low/critical counts
- timezone correctness
- recent orders sorting

## Acceptance Gate

- all assessment dashboard metrics implemented
- calculations documented and tested
- efficient queries

---

# PROMPT 10 — Frontend Foundation and Professional B2B UI System

## Objective

Build a polished but operational frontend foundation.

## Design Direction

The UI should feel like:
- modern healthcare operations software
- clean B2B SaaS
- professional
- trustworthy
- information-dense but uncluttered

Avoid:
- marketing hero sections
- excessive animations
- excessive gradients
- decorative charts with no operational value

## Layout

Create:
- sidebar or top navigation
- app header
- page container
- responsive structure

Navigation:
- Dashboard
- Orders
- New Order
- Inventory

## Shared UI Components

Create reusable components for:
- page header
- KPI card
- status badge
- data table
- pagination
- search input
- filter controls
- modal/dialog
- form controls
- loading skeleton
- empty state
- error state
- confirmation feedback

## API Layer

- central API client
- typed request/response models
- TanStack Query hooks
- consistent error normalization

## Routes

Finalize:
- `/`
- `/orders`
- `/orders/new`
- `/orders/:id`
- `/inventory`

## Acceptance Gate

- professional shell complete
- responsive base
- shared states/components exist
- API client typed
- no business screens left as raw placeholder except those scheduled for later prompts

---

# PROMPT 11 — Order Management Frontend

## Objective

Implement the complete order workflow UI.

## New Order Workspace

Required sections:

### Patient Information
- patient name
- order date/time

### Medicine Search
- autocomplete/search
- display:
  - name
  - strength
  - dosage form
  - current stock
  - stock status

### Order Items
For each selected medicine:
- requested quantity
- displayed current stock
- displayed shortage if any
- displayed availability result
- remove item

Prevent:
- duplicate medicine lines
- invalid quantity

### Order Summary
Show:
- patient
- item count
- each medicine
- requested quantities
- informational availability
- warning that final validation happens at confirmation if appropriate

### Confirm Order

On submit:
- call backend
- handle WAITING_FOR_STOCK
- handle DISPENSED
- handle validation conflicts
- show success
- navigate to order detail

## Orders Page

Implement:
- search
- status filter
- drug filter
- date range
- sorting
- pagination

Columns:
- order number
- patient
- items count
- status
- created
- dispensed/completed
- fulfilment time

## Order Detail

Show:
- order metadata
- patient
- items
- quantities
- statuses
- timestamps
- Complete action when allowed
- Cancel action when allowed

## UX States

- loading
- empty
- backend error
- mutation pending
- success

## Tests

At minimum:
- order form validation
- duplicate medicine prevention
- order submission
- waiting result
- dispensed result
- filters work with query params

## Acceptance Gate

- complete order UX works end-to-end
- no direct inventory mutation
- backend remains authoritative

---

# PROMPT 12 — Inventory and Dashboard Frontend

## Objective

Complete the manager-facing operational UI.

## Dashboard Page

Show KPI cards:
- Orders Today
- Completed Today
- Pending
- Average Fulfilment Time
- Low Stock
- Critical / Urgent Reorder

Sections:
- Recent Orders
- Low/Critical Stock
- Pending Orders if backend/query supports it cleanly

Use meaningful status badges.

Do not create decorative charts unless they add genuine value.

## Inventory Page

Table:
- Drug
- Code
- Current Stock
- Low Threshold
- Reorder Threshold
- Status
- Last Restocked
- Actions

Capabilities:
- search
- status filter
- low-stock filter
- critical filter
- sorting
- pagination

## Restock Interaction

- select drug
- show current stock
- enter positive restock quantity
- optional note
- confirmation
- submit
- refresh/invalidate inventory, dashboard, and affected orders

## Inventory Detail / Transaction History

Can be drawer/modal/page.

Show:
- stock
- thresholds
- status
- recent movements
- movement type
- before
- delta
- after
- related order
- timestamp

## Responsive Behaviour

Desktop-first, usable on tablet/mobile.

## Acceptance Gate

- all dashboard assessment requirements visible
- restock works from UI
- inventory ledger visible
- filters and pagination work
- UI is polished and consistent

---

# PROMPT 13 — Testing, Logging, Error Handling, and Final Backend Hardening

## Objective

Perform a deliberate quality pass over the entire core system before optional enhancements.

## Testing

Ensure test coverage for:

1. sufficient-stock order
2. zero-stock order
3. insufficient-stock order
4. multi-item all available
5. multi-item mixed availability
6. no negative stock
7. restock
8. ledger creation
9. FIFO
10. partial restock
11. exact restock
12. invalid drug
13. invalid quantity
14. duplicate drug
15. invalid status transition
16. completion timestamps
17. average fulfilment
18. low-stock
19. critical stock
20. filtering
21. sorting
22. pagination
23. concurrency oversell prevention

## Error Contract

Standardize error response:

```json
{
  "error": {
    "code": "SOME_CODE",
    "message": "Human readable message",
    "details": {},
    "request_id": "..."
  }
}
```

Ensure:
- 400/404/409/422/500 used consistently
- no stack traces sent to frontend
- request ID present where feasible

## Structured Logging

Verify events:
- ORDER_CREATED
- ORDER_WAITING_FOR_STOCK
- ORDER_DISPENSED
- ORDER_COMPLETED
- ORDER_CANCELLED
- INVENTORY_RESTOCKED
- INVENTORY_DISPENSED
- PENDING_ORDER_FULFILLED
- INVENTORY_SHORTAGE
- INVENTORY_CONFLICT
- UNEXPECTED_ERROR

## Frontend Hardening

Verify:
- error messages
- disabled states
- loading states
- empty states
- no silent failures
- no raw backend trace shown to user

## Acceptance Gate

- core test suite passes
- no known mandatory requirement broken
- errors consistent
- logs useful
- app ready for optional enhancements

---

# PROMPT 14 — Optional Redis and Real-Time Enhancement

## Objective

Add optional enhancements only if the core system is stable.

## Precondition

Do not execute this prompt if Prompt 13 is not fully complete.

## Redis

Redis must be optional.

Allowed uses:
- dashboard cache
- event distribution
- background coordination

Do not use Redis as:
- inventory source of truth
- order source of truth
- required dependency for core requests

If `REDIS_URL` is absent:
- application must still work fully
- database queries must be used directly

## Real-Time

Prefer SSE for:
- order.created
- order.updated
- inventory.updated
- dashboard.updated

Frontend:
- subscribe only when enabled
- invalidate relevant TanStack Query keys
- gracefully fall back to normal refetch if stream fails

Do not send sensitive data over events unnecessarily.

## Cache Invalidation

If caching dashboard summary:
- invalidate/update after order creation
- completion
- cancellation
- restock
- pending fulfilment

## Tests

- app works without Redis
- app works with Redis if configured
- realtime disconnect does not break core UI
- dashboard eventually reflects DB truth

## Acceptance Gate

- optional infrastructure does not become critical path
- core app works when Redis disabled
- realtime cleanly degrades

---

# PROMPT 15 — Final Assessment Compliance Audit, README, and Deployment Readiness

## Objective

Perform the final audit against the original assessment and master specification.

Do not assume the project is complete. Verify it.

## Part A — Compliance Audit

Create a checklist mapping every original requirement to:
- backend implementation
- frontend implementation
- test proving it
- status

Verify:

### Accept New Orders
- patient name
- drug
- quantity
- date/time
- database save
- inventory check

### Track Inventory
- per-drug stock
- low stock
- manual restocking

### Status
- New
- Waiting for Stock
- Dispensed
- Completed
- auto processing after restock

### Dashboard
- total orders today
- completed vs pending
- average completion/fill time
- low-stock list
- recent orders
- sorting
- filtering

### Technical
- Python/FastAPI
- React
- MySQL

### Submission Quality
- working code
- setup instructions
- sample data
- folder structure
- tests
- logging
- database schema
- README

Fix any missing mandatory item before marking complete.

## Part B — README

Create a professional README containing:

1. Project overview
2. Business problem
3. Features
4. Architecture
5. Technology stack
6. Folder structure
7. Database schema summary
8. Order state model
9. FIFO restock behaviour
10. Concurrency/inventory integrity explanation
11. Environment variables
12. Local setup
13. MySQL migration commands
14. Seed command
15. Backend run command
16. Frontend run command
17. Test commands
18. API docs URL pattern
19. Cloud deployment notes
20. Assumptions
21. Scope boundaries

Never include real secret values.

## Part C — Database Documentation

Create ER diagram using Mermaid if practical.

Document:
- tables
- relationships
- major constraints
- indexes

## Part D — API Documentation

Verify Swagger/OpenAPI is clean and understandable.

Add meaningful endpoint summaries/descriptions.

## Part E — Production Configuration Review

Verify:
- CORS
- frontend API URL env
- DB env
- logging level
- health endpoint
- no debug secrets
- no hardcoded localhost in production path

## Part F — Demo Data

Ensure deployed/demo database has:
- healthy inventory
- low inventory
- critical inventory
- out-of-stock inventory
- completed orders
- waiting orders

## Acceptance Gate

- all mandatory requirements proven
- README complete
- no secret leakage
- app ready to deploy
- compliance matrix fully green

---

# PROMPT 16 — Cloud Deployment and End-to-End Demo Verification

## Objective

Deploy and verify the application using the user's chosen cloud providers.

## Preconditions

- MySQL managed database exists
- Prompt 15 is complete
- `.env` contains required connection information locally

## Backend Deployment

Deploy FastAPI to the selected platform.

Configure:
- production env
- database variables
- frontend origin
- logging
- optional Redis
- realtime flag

Run:
- migrations
- seed/demo data if appropriate

Verify:
- `/api/v1/health`
- `/docs`
- representative APIs

## Frontend Deployment

Deploy React frontend.

Configure:
- `VITE_API_BASE_URL`

Verify:
- no localhost production URL
- CORS works
- order creation works
- inventory works
- dashboard works

## End-to-End Demo Test

Run this exact flow:

1. Open Dashboard
2. Note metrics
3. Create order with:
   - one available medicine
   - one unavailable/insufficient medicine
4. Confirm order is WAITING_FOR_STOCK
5. Open Inventory
6. Restock blocking medicine
7. Verify waiting order is automatically reprocessed
8. Verify inventory ledger
9. Verify order becomes DISPENSED
10. Mark order COMPLETED
11. Return to Dashboard
12. Verify updated metrics
13. Verify Recent Orders
14. Verify Low Stock
15. Verify Swagger
16. Verify logs contain meaningful events

## Final Output Required

Report:
- frontend URL
- backend URL
- Swagger URL
- health URL
- any deployment caveats
- final compliance status

Do not expose secret values.

## Acceptance Gate

The assessment is considered finished only when the complete business flow works on the deployed application.

---

# APPENDIX A — Mandatory Business Scenarios

These scenarios must remain working throughout all phases.

## Scenario A — Immediate Fulfilment

Stock = 50  
Requested = 20

Expected:
- order created
- stock -> 30
- inventory transaction created
- order DISPENSED
- can be completed

## Scenario B — Waiting for Stock

Stock = 5  
Requested = 20

Expected:
- order created
- item WAITING_FOR_STOCK
- parent WAITING_FOR_STOCK
- inventory does not become negative

## Scenario C — Restock and Auto Fulfil

Waiting item requires 20  
Stock = 5  
Restock = 30

Expected:
- restock ledger created
- stock increases
- FIFO processor runs
- item becomes DISPENSED
- parent becomes DISPENSED if all items fulfilled
- stock correct after deduction

## Scenario D — FIFO

Waiting:
- A = 10
- B = 20
- C = 20

Restock = 35

Expected:
- A fulfilled
- B fulfilled
- C waiting
- stock = 5

## Scenario E — Concurrency

Stock = 10

Concurrent:
- A requests 8
- B requests 8

Expected:
- no oversell
- no negative inventory
- exactly one valid deduction of 8
- other order/request follows insufficient-stock behaviour

---

# APPENDIX B — Definition of Complete

The project is complete when:

- all original requirements work
- database schema is migrated
- inventory integrity is safe
- waiting orders auto-process after restock
- dashboard calculations are correct
- frontend is complete and professional
- filters/sorting/pagination work
- tests pass
- logs are useful
- README is complete
- live deployment works
- Swagger works
- no secrets are exposed
- final compliance audit is green

