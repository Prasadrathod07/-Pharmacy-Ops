# Pharmacy Order & Inventory Dashboard
## Master Engineering Specification / Single Source of Truth

**Document Status:** Final development context  
**Primary Purpose:** This document is the authoritative business, product, architecture, database, API, frontend, testing, deployment, and implementation specification for the Pharmacy Order & Inventory Dashboard coding assessment.

---

# 0. How to Use This Document

This file must be treated as the **single source of truth** for implementation.

Any coding agent, developer, reviewer, or AI coding tool using this project should:

1. Read this document fully before writing code.
2. Preserve the original assessment requirements.
3. Distinguish clearly between:
   - **Mandatory Assessment Requirement**
   - **Documented Project Assumption**
   - **Engineering Enhancement**
4. Do not introduce out-of-scope features unless this document is explicitly revised.
5. Do not replace MySQL with PostgreSQL/Supabase or another database.
6. Do not introduce microservices, Kafka, Kubernetes, authentication, payments, AI/LLMs, delivery tracking, or full ERP features.
7. Keep the business scope intentionally focused while making the implementation production-minded.
8. Prefer correctness, maintainability, auditability, and clarity over unnecessary technical complexity.
9. Ensure all business-critical rules are enforced on the backend, never only in the frontend.
10. Treat MySQL as the authoritative source of truth for orders and inventory.

---

# 1. Original Assessment

## 1.1 Problem Title

**Pharmacy Order & Inventory Dashboard**

## 1.2 Business Problem

A pharmacy chain needs a system to track prescription orders and inventory in real time.

The original workflow is:

1. A customer walks in or calls with a prescription.
2. Pharmacy staff enters the prescription/order into the system.
3. The system checks whether enough of the requested drug is available.
4. If enough stock exists, the order is dispensed.
5. If stock is insufficient, the order waits until stock arrives.
6. The manager uses a dashboard to monitor:
   - Orders received today
   - Filled/completed vs pending orders
   - Low-stock drugs
   - Average order fulfilment time
   - Drugs requiring urgent reorder

## 1.3 Mandatory System Capabilities

### Accept New Orders

The system must allow staff to capture:

- Patient name
- Drug name
- Quantity
- Date/time

The order must be persisted in the database.

The system must check inventory.

### Track Inventory

The system must:

- Track available stock for each drug
- Flag low-stock drugs
- Allow manual restocking

### Update Order Status

Expected lifecycle from the assessment:

**New → Waiting for Stock → Dispensed → Completed**

If a restock resolves the stock shortage blocking an order, the system must automatically process that order toward dispensing.

### Manager Dashboard

The manager must be able to see:

- Total orders today
- Orders completed vs pending
- Average time to complete/fill an order
- Low-stock drugs
- Recent orders
- Sorting and filtering of recent orders

## 1.4 Technical Constraints from the Assessment

- **Backend language:** Python or Java
- **Frontend:** React
- **Database:** MySQL
- **Queueing:** Developer choice
- **Caching:** Developer choice
- **Architecture:** Developer choice

## 1.5 Required Deliverables

The submission must include:

1. Working code
2. Setup instructions
3. Sample data
4. Clear code organization
5. Tests
6. Logging
7. Database schema
8. README/documentation

## 1.6 Timeline

Expected assessment duration:

**3–5 days**

Quality is more important than speed.

## 1.7 Explicit Non-Requirements

Do not spend time building:

- Fancy marketing UI
- Authentication/login
- Full inventory ERP
- AI/LLM APIs

---

# 2. Product Interpretation

## 2.1 Product Definition

This project will be implemented as a:

> **Pharmacy Order Fulfilment & Inventory Operations Platform**

It is an internal operations system for pharmacy staff and managers.

It is **not** a customer ecommerce marketplace.

## 2.2 Primary Users

### Pharmacy Staff

Responsibilities:

- Create a prescription/order
- Search medicines
- View current availability
- Enter requested quantities
- Confirm orders
- View order status

### Pharmacy Manager

Responsibilities:

- Monitor operational KPIs
- Monitor low and critical stock
- View pending orders
- Restock inventory
- Review recent orders
- Review inventory movement history

## 2.3 Customer Role

The customer is part of the business process but is **not an application user** in this assessment.

No customer account, login, payment, delivery, or ecommerce experience is required.

---

# 3. Key Business Interpretation

The original wording says a customer may walk in or call.

The phrase **"order waits until stock arrives"** is interpreted as:

> The order remains operationally pending in the system because inventory is unavailable.

It does **not** mean that a walk-in customer must physically remain at the pharmacy.

This project intentionally models the inventory and fulfilment workflow, not the physical customer waiting experience.

---

# 4. Scope

## 4.1 In Scope

- Medicine catalogue
- Patient/order capture
- Multi-item prescription/order support
- Live inventory visibility while building an order
- Final backend stock validation at order confirmation
- Order persistence
- Inventory persistence
- Stock deduction
- Pending stock workflow
- Manual restocking
- Automatic re-evaluation of pending orders after restock
- FIFO pending fulfilment rule
- Order state transitions
- Dashboard KPIs
- Recent orders
- Search, filtering, sorting
- Pagination
- Low-stock and urgent-reorder status
- Inventory transaction ledger
- Structured logging
- Validation
- Transaction-safe stock handling
- Concurrency protection
- Database migrations
- Seed/sample data
- Unit and integration testing
- Cloud deployment
- API documentation
- Responsive professional frontend

## 4.2 Engineering Enhancements

These are not mandatory in the assessment but are approved enhancements:

- Inventory audit ledger
- Concurrency-safe stock mutation
- Rich validation
- Pagination
- Better operational analytics
- Health endpoint
- Structured application logs
- Request correlation IDs
- Real-time dashboard updates
- Redis for a justified purpose
- Better API documentation
- Strong loading, error, and empty states

## 4.3 Explicitly Out of Scope

Do not build:

- Authentication/login
- Role-based access control
- Customer accounts
- Shopping cart
- Payment gateway
- Delivery tracking
- Shipping/logistics
- Prescription OCR
- AI drug recognition
- AI/LLM APIs
- Insurance claims
- Doctor verification
- GST/billing
- Supplier procurement ERP
- Multi-warehouse logistics
- Full pharmacy ERP
- Kubernetes
- Kafka
- RabbitMQ
- Elasticsearch
- Microservices
- CI/CD pipelines
- Docker as a mandatory deliverable

---

# 5. Product Design Principle

The product must be:

- Simple enough to understand quickly
- Deep enough to demonstrate mature engineering
- Operational rather than decorative
- Backend-authoritative
- Transaction-safe
- Audit-friendly
- Cloud-demo ready

Primary engineering principle:

> **Enterprise engineering quality with assignment-sized business scope.**

---

# 6. Core User Journeys

## 6.1 New Order / Prescription Flow

1. Staff opens **New Order**
2. Staff enters patient details
3. Staff searches for a medicine
4. Search results show current stock availability
5. Staff adds medicine
6. Staff enters requested quantity
7. System shows:
   - Requested quantity
   - Current displayed stock
   - Estimated shortage
   - Availability state
8. Staff can add additional medicines
9. System shows prescription/order summary
10. Staff confirms the order
11. Backend performs an authoritative stock validation inside a transaction
12. Backend decides each item/order status
13. Inventory is deducted only when allowed by business rules
14. Order becomes:
   - DISPENSED / COMPLETED if fulfillable, or
   - WAITING_FOR_STOCK if blocked by stock
15. Dashboard reflects the updated operational state

## 6.2 Restock Flow

1. Manager opens Inventory
2. Manager searches/selects a drug
3. Current inventory is displayed
4. Manager enters restock quantity
5. Backend validates restock quantity
6. Restock inventory movement is recorded
7. Inventory increases
8. Pending orders for that drug are evaluated in FIFO order
9. Fulfillable waiting orders are processed
10. Inventory decreases as pending orders are fulfilled
11. Remaining unfulfillable orders stay WAITING_FOR_STOCK
12. Dashboard updates

## 6.3 Dashboard Flow

Manager can see:

- Orders today
- Completed orders
- Pending orders
- Average fulfilment time
- Low-stock drug count
- Critical/urgent reorder count
- Recent orders
- Low-stock list
- Pending order list

## 6.4 Order Search Flow

Staff/manager can filter by:

- Patient name
- Drug name
- Order number
- Status
- Date range

Results can be sorted and paginated.

---

# 7. Order Management UX

The New Order screen should behave as an **Order Fulfilment Workspace**, not a simple form.

## 7.1 Patient / Order Information

Required:

- Patient name
- Order date/time

Optional UI-only future-ready fields may be added only if they do not expand scope significantly.

## 7.2 Medicine Search

As the user types:

- Show matching medicine names
- Show dosage/form if available
- Show currently known available quantity
- Show stock status

Example:

| Drug | Current Stock | Requested | Result |
|---|---:|---:|---|
| Paracetamol 500 mg | 120 | 20 | Available |
| Amoxicillin 500 mg | 8 | 20 | Insufficient |
| Vitamin D3 | 0 | 10 | Out of Stock |

## 7.3 Important Rule

The inventory quantity shown in the UI is **informational**.

It is not authoritative.

The backend must validate stock again when the order is confirmed because another user may have changed inventory since the search result was displayed.

## 7.4 Order Confirmation

Before confirmation, show:

- Patient
- Number of medicines
- Each medicine
- Requested quantity
- Displayed availability
- Overall fulfilment summary

Then:

**Confirm Order**

## 7.5 Inventory Mutation Rule

The Order screen may display inventory.

The Order screen must **not** allow staff to arbitrarily edit stock quantities.

Restocking and inventory adjustment belong in Inventory Management.

---

# 8. Inventory Management UX

The Inventory page should show:

- Drug
- SKU/code
- Current on-hand stock
- Low-stock threshold
- Urgent reorder threshold
- Stock status
- Last restocked time
- Last movement time

## 8.1 Inventory Status

Suggested statuses:

- HEALTHY
- LOW_STOCK
- CRITICAL
- OUT_OF_STOCK

## 8.2 Manual Restock

Manager can:

- Select drug
- Enter positive restock quantity
- Enter optional note/reference
- Confirm restock

After restock, backend runs pending-order fulfilment logic.

## 8.3 Inventory History

For each drug, show a movement ledger:

- RESTOCK
- DISPENSE
- ADJUSTMENT if supported
- AUTO_FULFIL_PENDING

Every movement should include:

- Quantity delta
- Previous stock
- New stock
- Related order if applicable
- Timestamp
- Note/source

---

# 9. Dashboard UX

## 9.1 KPI Cards

Required:

- Total Orders Today
- Completed Today
- Pending / Waiting for Stock
- Average Fulfilment Time
- Low Stock Drugs
- Critical / Urgent Reorder Drugs

## 9.2 Recent Orders Table

Columns:

- Order number
- Patient
- Items count
- Status
- Created time
- Dispensed/completed time
- Fulfilment time

Capabilities:

- Search
- Filter
- Sort
- Pagination

## 9.3 Low Stock Panel

Display:

- Drug
- Current stock
- Low threshold
- Reorder threshold
- Status

## 9.4 Pending Orders Panel

Display:

- Order number
- Patient
- Blocking medicine(s)
- Quantity needed
- Created time
- Waiting duration

---

# 10. Domain Model

## 10.1 Core Entities

- Patient
- Drug
- Inventory
- Order
- OrderItem
- InventoryTransaction

Optional if useful:

- RestockBatch or RestockEvent

A separate RestockEvent table is optional because restocks can be represented cleanly through InventoryTransaction.

Recommended approach:

**Use InventoryTransaction as the canonical stock movement ledger.**

---

# 11. Order State Model

## 11.1 Order Status Enum

Recommended values:

- `NEW`
- `WAITING_FOR_STOCK`
- `DISPENSED`
- `COMPLETED`
- `CANCELLED`

## 11.2 Meaning

### NEW

Order exists but has not yet completed fulfilment evaluation.

This may be very short-lived internally.

### WAITING_FOR_STOCK

One or more required items cannot currently be fulfilled.

### DISPENSED

All required inventory has been successfully allocated/deducted and the medicine has been dispensed or marked ready as defined by this assessment.

### COMPLETED

The order lifecycle is finalized.

### CANCELLED

Optional but useful operational state.

## 11.3 Allowed Transitions

```text
NEW
 ├──> WAITING_FOR_STOCK
 └──> DISPENSED

WAITING_FOR_STOCK
 ├──> DISPENSED
 └──> CANCELLED

DISPENSED
 └──> COMPLETED

NEW
 └──> CANCELLED
```

Invalid transitions must be rejected on the backend.

---

# 12. Order Item State

Because a prescription may contain multiple medicines, each item should have its own fulfilment state.

Suggested item statuses:

- `PENDING`
- `WAITING_FOR_STOCK`
- `DISPENSED`
- `CANCELLED`

The parent order status is derived from the aggregate item state.

Recommended rules:

- All items DISPENSED → order DISPENSED
- At least one item WAITING_FOR_STOCK → order WAITING_FOR_STOCK
- All items CANCELLED → order CANCELLED

For assignment simplicity, partial dispensing can be visually represented but the implementation should remain deterministic and well documented.

---

# 13. Multi-Medicine Prescription Design

A real prescription may contain multiple medicines.

Therefore:

```text
Order
  ├── OrderItem: Drug A × 10
  ├── OrderItem: Drug B × 20
  └── OrderItem: Drug C × 5
```

This is preferred over creating one order record per drug.

Benefits:

- Better domain modelling
- Better UI
- Easier patient/order history
- More realistic prescription support
- Future extensibility

---

# 14. Inventory Business Rules

## 14.1 Source of Truth

MySQL inventory is authoritative.

Redis, frontend state, or cached values must never decide final stock availability.

## 14.2 Stock Validation

At order confirmation:

For each item:

```text
requested_quantity <= current_inventory
```

must be evaluated inside the same transaction used for stock mutation.

## 14.3 No Negative Inventory

Inventory quantity must never become negative.

Database/service constraints must prevent this.

## 14.4 Stock Mutation

Stock may change only through controlled backend service operations.

No frontend direct database mutation.

## 14.5 Low Stock

A drug is LOW_STOCK when:

```text
current_stock <= low_stock_threshold
```

and above the urgent reorder threshold.

## 14.6 Critical / Urgent Reorder

A drug is CRITICAL when:

```text
current_stock <= reorder_threshold
```

Suggested rule:

```text
reorder_threshold <= low_stock_threshold
```

## 14.7 Out of Stock

```text
current_stock == 0
```

---

# 15. Pending Order Fulfilment Rule

When stock is insufficient, the affected order remains WAITING_FOR_STOCK.

When stock is added:

1. Query waiting order items for that drug
2. Sort by oldest order creation timestamp
3. Apply FIFO
4. Lock required rows/perform safe transactional evaluation
5. Fulfil only orders/items that can be satisfied
6. Deduct stock
7. Record inventory transaction
8. Update item status
9. Recompute parent order status
10. Stop naturally when inventory cannot satisfy the next waiting item

## 15.1 FIFO Example

Pending:

- ORD-101 requires 10
- ORD-102 requires 20
- ORD-103 requires 20

Restock:

- +35

Result:

- ORD-101 → fulfilled
- Remaining stock = 25
- ORD-102 → fulfilled
- Remaining stock = 5
- ORD-103 → remains waiting

FIFO is a documented project assumption because the original assessment does not define priority.

---

# 16. Concurrency Strategy

Inventory is concurrency-sensitive.

## 16.1 Problem

Initial stock:

```text
10
```

Two staff members simultaneously request:

```text
Staff A: 8
Staff B: 8
```

Both must not succeed.

## 16.2 Required Behaviour

One transaction succeeds first.

The second transaction sees the updated inventory and follows the insufficient-stock rule.

## 16.3 Implementation Strategy

Use one of:

- `SELECT ... FOR UPDATE` row locking, or
- An equivalent atomic conditional update

Recommended with SQLAlchemy/MySQL:

1. Begin transaction
2. Lock inventory row
3. Read current stock
4. Validate requested quantity
5. Deduct safely
6. Insert inventory transaction
7. Update order/item status
8. Commit

## 16.4 Important Rule

Do not rely on frontend values for concurrency.

---

# 17. Transaction Boundaries

The following must be atomic:

## 17.1 Successful Order Fulfilment

Inside one transaction:

- Create/update order
- Validate inventory
- Deduct inventory
- Create inventory ledger movement
- Update order item state
- Update parent order state

## 17.2 Restocking

Inside one transaction or controlled sequence of short transactions:

- Increase inventory
- Record RESTOCK ledger movement
- Commit restock safely

Then process waiting orders using safe transactions.

## 17.3 Failure Behaviour

If any critical mutation fails:

- Roll back
- Do not leave inventory and order states inconsistent

---

# 18. Inventory Transaction Ledger

## 18.1 Purpose

The ledger answers:

> Why is this drug's stock currently at this value?

## 18.2 Transaction Types

Suggested:

- `RESTOCK`
- `DISPENSE`
- `ADJUSTMENT`
- `AUTO_FULFIL_PENDING`

If AUTO_FULFIL_PENDING is functionally equivalent to DISPENSE, either:
- Keep one DISPENSE type and include source metadata, or
- Use separate types for readability

Recommended:

Use:

- RESTOCK
- DISPENSE
- ADJUSTMENT

and include:

`source = NEW_ORDER | PENDING_FULFILMENT | MANUAL_ADJUSTMENT`

## 18.3 Required Fields

- id
- drug_id
- order_id nullable
- order_item_id nullable
- movement_type
- source
- quantity_delta
- quantity_before
- quantity_after
- note nullable
- created_at

---

# 19. System Architecture

## 19.1 Architecture Style

**Modular Monolith**

Reason:

- Appropriate for project size
- Easier to understand
- Easier to test
- Easier to deploy
- Avoids distributed-system complexity
- Still supports strong modular boundaries

## 19.2 High-Level Architecture

```text
┌──────────────────────────────┐
│ React + TypeScript Frontend  │
│ Operational Web Application  │
└──────────────┬───────────────┘
               │ HTTPS REST
               │ optional SSE
               ▼
┌──────────────────────────────┐
│ FastAPI Backend              │
│                              │
│ API Layer                    │
│ Service/Application Layer    │
│ Domain Rules                 │
│ Repository/Persistence       │
│ Events                       │
│ Logging                      │
└──────────────┬───────────────┘
               │ SQLAlchemy
               ▼
┌──────────────────────────────┐
│ MySQL                        │
│ Authoritative Data Store     │
└──────────────────────────────┘

Optional:
FastAPI → Redis
```

---

# 20. Technology Stack

## 20.1 Frontend

- React
- TypeScript
- Vite recommended
- TanStack Query
- React Router
- Component library: choose one modern library or build a focused internal design system
- Form library optional
- Zod optional for client-side validation

## 20.2 Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- MySQL driver compatible with deployment
- Pytest

## 20.3 Database

- MySQL 8+

## 20.4 Optional Infrastructure

- Redis
- SSE or WebSocket for real-time updates

## 20.5 Deployment

Recommended:

- Frontend: Vercel
- Backend: Railway, Render, or comparable Python/container platform
- Database: Managed MySQL provider

Cloud deployment is required for this project because the developer needs browser-based demonstration without relying on a local laptop.

---

# 21. Backend Modules

Recommended modules:

- `orders`
- `patients`
- `drugs`
- `inventory`
- `fulfilment`
- `dashboard`
- `audit`
- `core`

---

# 22. Backend Folder Structure

Recommended:

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── orders.py
│   │       ├── drugs.py
│   │       ├── inventory.py
│   │       ├── dashboard.py
│   │       └── health.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── patient.py
│   │   ├── drug.py
│   │   ├── inventory.py
│   │   ├── order.py
│   │   ├── order_item.py
│   │   └── inventory_transaction.py
│   │
│   ├── schemas/
│   │   ├── patient.py
│   │   ├── drug.py
│   │   ├── inventory.py
│   │   ├── order.py
│   │   └── dashboard.py
│   │
│   ├── repositories/
│   │   ├── orders.py
│   │   ├── drugs.py
│   │   └── inventory.py
│   │
│   ├── services/
│   │   ├── order_service.py
│   │   ├── inventory_service.py
│   │   ├── fulfilment_service.py
│   │   └── dashboard_service.py
│   │
│   ├── domain/
│   │   ├── enums.py
│   │   ├── rules.py
│   │   └── state_machine.py
│   │
│   └── events/
│       ├── publisher.py
│       └── handlers.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── alembic/
├── alembic.ini
├── requirements.txt / pyproject.toml
└── README.md
```

---

# 23. Frontend Architecture

Frontend responsibilities:

- Render UI
- Handle user interaction
- Display live/near-live inventory
- Perform client validation
- Submit requests
- Display backend validation/errors
- Manage API cache
- Never decide authoritative inventory outcomes

---

# 24. Frontend Folder Structure

Recommended:

```text
frontend/
├── src/
│   ├── app/
│   │   ├── router.tsx
│   │   └── providers.tsx
│   │
│   ├── pages/
│   │   ├── DashboardPage.tsx
│   │   ├── OrdersPage.tsx
│   │   ├── NewOrderPage.tsx
│   │   ├── OrderDetailsPage.tsx
│   │   └── InventoryPage.tsx
│   │
│   ├── features/
│   │   ├── orders/
│   │   ├── inventory/
│   │   ├── dashboard/
│   │   └── drugs/
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   └── feedback/
│   │
│   ├── api/
│   │   ├── client.ts
│   │   ├── orders.ts
│   │   ├── inventory.ts
│   │   └── dashboard.ts
│   │
│   ├── types/
│   ├── utils/
│   └── main.tsx
│
└── package.json
```

---

# 25. Database Design

## 25.1 Design Goals

The database must support:

- Multi-item orders
- Reliable inventory tracking
- Auditability
- Fast pending-order lookup
- Dashboard metrics
- Concurrency-safe inventory
- Filtering and sorting

---

# 26. Database Schema

## 26.1 `patients`

| Column | Type | Rules |
|---|---|---|
| id | BIGINT | PK |
| full_name | VARCHAR(150) | NOT NULL |
| created_at | DATETIME/TIMESTAMP | NOT NULL |
| updated_at | DATETIME/TIMESTAMP | NOT NULL |

Notes:

The assessment only requires patient name. Keep the entity intentionally minimal.

---

## 26.2 `drugs`

| Column | Type | Rules |
|---|---|---|
| id | BIGINT | PK |
| code | VARCHAR(50) | UNIQUE, NOT NULL |
| name | VARCHAR(200) | NOT NULL |
| strength | VARCHAR(100) | NULL |
| dosage_form | VARCHAR(100) | NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | DATETIME/TIMESTAMP | NOT NULL |
| updated_at | DATETIME/TIMESTAMP | NOT NULL |

Examples:

- PARACETAMOL-500-TAB
- AMOXICILLIN-500-CAP

---

## 26.3 `inventory`

| Column | Type | Rules |
|---|---|---|
| id | BIGINT | PK |
| drug_id | BIGINT | FK drugs.id, UNIQUE |
| quantity_on_hand | INT | NOT NULL, >= 0 |
| low_stock_threshold | INT | NOT NULL, >= 0 |
| reorder_threshold | INT | NOT NULL, >= 0 |
| last_restocked_at | DATETIME/TIMESTAMP | NULL |
| created_at | DATETIME/TIMESTAMP | NOT NULL |
| updated_at | DATETIME/TIMESTAMP | NOT NULL |

Constraint:

```text
reorder_threshold <= low_stock_threshold
```

---

## 26.4 `orders`

| Column | Type | Rules |
|---|---|---|
| id | BIGINT | PK |
| order_number | VARCHAR(40) | UNIQUE, NOT NULL |
| patient_id | BIGINT | FK patients.id |
| status | VARCHAR/ENUM | NOT NULL |
| created_at | DATETIME/TIMESTAMP | NOT NULL |
| dispensed_at | DATETIME/TIMESTAMP | NULL |
| completed_at | DATETIME/TIMESTAMP | NULL |
| cancelled_at | DATETIME/TIMESTAMP | NULL |
| updated_at | DATETIME/TIMESTAMP | NOT NULL |

---

## 26.5 `order_items`

| Column | Type | Rules |
|---|---|---|
| id | BIGINT | PK |
| order_id | BIGINT | FK orders.id |
| drug_id | BIGINT | FK drugs.id |
| requested_quantity | INT | NOT NULL, > 0 |
| status | VARCHAR/ENUM | NOT NULL |
| dispensed_quantity | INT | NOT NULL DEFAULT 0 |
| created_at | DATETIME/TIMESTAMP | NOT NULL |
| updated_at | DATETIME/TIMESTAMP | NOT NULL |

Recommended unique constraint:

```text
(order_id, drug_id)
```

This prevents duplicate drug lines within one order.

---

## 26.6 `inventory_transactions`

| Column | Type | Rules |
|---|---|---|
| id | BIGINT | PK |
| drug_id | BIGINT | FK drugs.id |
| order_id | BIGINT | FK orders.id, NULL |
| order_item_id | BIGINT | FK order_items.id, NULL |
| movement_type | VARCHAR/ENUM | NOT NULL |
| source | VARCHAR/ENUM | NOT NULL |
| quantity_delta | INT | NOT NULL |
| quantity_before | INT | NOT NULL |
| quantity_after | INT | NOT NULL |
| note | VARCHAR(500) | NULL |
| created_at | DATETIME/TIMESTAMP | NOT NULL |

---

# 27. Relationships

```text
Patient 1 ─── N Order

Order 1 ─── N OrderItem

Drug 1 ─── 1 Inventory

Drug 1 ─── N OrderItem

Drug 1 ─── N InventoryTransaction

Order 1 ─── N InventoryTransaction
```

---

# 28. Database Constraints

Must enforce:

- Inventory cannot be negative
- Requested quantity must be > 0
- Dispensed quantity must be >= 0
- Drug code unique
- Order number unique
- One inventory row per drug
- Thresholds non-negative
- Reorder threshold <= low stock threshold
- Duplicate drug lines not allowed in one order

Some constraints may be implemented at both application and DB level.

---

# 29. Indexing Strategy

Recommended indexes:

## Orders

- `orders(order_number)` unique
- `orders(status, created_at)`
- `orders(created_at)`
- `orders(patient_id)`

## Order Items

- `order_items(order_id)`
- `order_items(drug_id, status)`
- `order_items(status, created_at)` if supported/needed

## Drugs

- `drugs(name)`
- `drugs(code)` unique

## Inventory

- `inventory(drug_id)` unique
- optionally `(quantity_on_hand, low_stock_threshold)` not always necessary

## Inventory Transactions

- `inventory_transactions(drug_id, created_at)`
- `inventory_transactions(order_id)`
- `inventory_transactions(order_item_id)`

---

# 30. API Design

Base path:

```text
/api/v1
```

---

# 31. Drug APIs

## `GET /api/v1/drugs`

Purpose:

- Search medicines
- Support order creation
- Display inventory-aware results

Query params:

- `search`
- `page`
- `page_size`
- `active`

Response should include:

- drug metadata
- current inventory
- stock status

---

## `GET /api/v1/drugs/{drug_id}`

Returns:

- drug details
- inventory details
- status

---

# 32. Order APIs

## `POST /api/v1/orders`

Creates and processes an order.

Request example:

```json
{
  "patient_name": "John Doe",
  "ordered_at": "2026-09-22T14:00:00Z",
  "items": [
    {
      "drug_id": 1,
      "quantity": 10
    },
    {
      "drug_id": 2,
      "quantity": 20
    }
  ]
}
```

Backend responsibilities:

- Validate patient
- Validate drugs
- Validate quantities
- Create order
- Lock inventory rows as needed
- Evaluate availability
- Deduct inventory where allowed
- Record inventory transactions
- Set order item statuses
- Set order status
- Commit atomically

---

## `GET /api/v1/orders`

Query params:

- `search`
- `status`
- `drug_id`
- `date_from`
- `date_to`
- `sort_by`
- `sort_order`
- `page`
- `page_size`

---

## `GET /api/v1/orders/{order_id}`

Returns:

- order
- patient
- items
- item statuses
- timestamps
- fulfilment time
- inventory movement references if useful

---

## `POST /api/v1/orders/{order_id}/complete`

Transitions:

`DISPENSED → COMPLETED`

Reject invalid state transitions.

---

## `POST /api/v1/orders/{order_id}/cancel`

Optional but recommended.

Allowed only from valid states.

---

# 33. Inventory APIs

## `GET /api/v1/inventory`

Query params:

- `search`
- `status`
- `low_stock_only`
- `critical_only`
- `page`
- `page_size`
- sorting params

---

## `GET /api/v1/inventory/{drug_id}`

Returns:

- drug
- quantity
- thresholds
- stock status
- recent transactions

---

## `POST /api/v1/inventory/{drug_id}/restock`

Request:

```json
{
  "quantity": 100,
  "note": "Supplier restock"
}
```

Backend:

- Validate positive quantity
- Lock inventory
- Increase stock
- Create RESTOCK transaction
- Commit
- Trigger pending fulfilment flow

---

## `GET /api/v1/inventory/{drug_id}/transactions`

Supports:

- pagination
- movement type filter
- date filter

---

# 34. Dashboard APIs

## `GET /api/v1/dashboard/summary`

Returns:

```json
{
  "orders_today": 124,
  "completed_today": 96,
  "pending_orders": 18,
  "average_fulfilment_minutes": 11.4,
  "low_stock_drugs": 6,
  "critical_stock_drugs": 2
}
```

---

## `GET /api/v1/dashboard/recent-orders`

Returns recent orders with pagination/filtering support.

---

## `GET /api/v1/dashboard/low-stock`

Returns low/critical stock list.

---

# 35. Health API

## `GET /api/v1/health`

Returns:

```json
{
  "status": "ok",
  "database": "connected"
}
```

Do not expose credentials.

---

# 36. Dashboard Metrics Definitions

## Orders Today

Orders where:

```text
created_at is within current business day
```

## Completed Today

Orders where:

```text
status = COMPLETED
and completed_at is within current business day
```

## Pending Orders

Orders where:

```text
status = WAITING_FOR_STOCK
```

## Average Fulfilment Time

Recommended primary metric:

```text
dispensed_at - created_at
```

for orders dispensed during the relevant reporting window.

Reason:

The assessment asks for average time to fill an order.

A secondary completion-time metric may be:

```text
completed_at - created_at
```

Document clearly in UI/help text.

---

# 37. Validation Rules

## Order

- Patient name required
- Patient name trimmed
- At least one item required
- Quantity > 0
- Drug must exist
- Drug must be active
- No duplicate drug in same order
- Date/time must be valid

## Restock

- Quantity must be integer
- Quantity > 0
- Drug must exist
- Inventory row must exist

## Pagination

- Page >= 1
- Reasonable page_size limit such as <= 100

---

# 38. Error Handling

Use consistent error structure.

Suggested:

```json
{
  "error": {
    "code": "INVENTORY_CONFLICT",
    "message": "Inventory changed while processing the order.",
    "details": {
      "drug_id": 2
    },
    "request_id": "..."
  }
}
```

HTTP status guidance:

- 400 → malformed/invalid business input
- 404 → resource not found
- 409 → inventory/state conflict
- 422 → schema validation
- 500 → unexpected server error

Do not expose stack traces to frontend.

---

# 39. Logging Strategy

Use structured logs.

Every request should ideally include:

- timestamp
- log level
- request ID
- endpoint
- method
- duration
- status code

Important business events:

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

Example:

```text
event=INVENTORY_SHORTAGE
order_id=ORD-1042
drug_id=18
requested=30
available=8
```

---

# 40. Audit Trail vs Application Logs

These are different.

## Application Logs

Used for:

- debugging
- request tracing
- failures
- application events

## Inventory Transaction Ledger

Used for:

- business traceability
- stock history
- operational audit

Do not use application logs as the only inventory history.

---

# 41. Redis Strategy

Redis is an approved optional enhancement.

## 41.1 Allowed Responsibilities

Redis may be used for:

- Dashboard metric caching
- Event distribution for realtime UI
- Background task coordination

## 41.2 Forbidden Responsibilities

Redis must **not** be the authoritative source for:

- Inventory quantity
- Order state
- Patient/order data

## 41.3 Failure Behaviour

If Redis is unavailable:

- Core order creation must continue
- Inventory processing must continue
- Restocking must continue
- Dashboard may fall back to database queries
- Realtime updates may temporarily degrade

---

# 42. Real-Time Strategy

Real-time is a nice-to-have enhancement.

Recommended approach:

**SSE first**

Reason:

Dashboard updates are primarily server → browser.

Possible events:

- `order.created`
- `order.updated`
- `inventory.updated`
- `dashboard.updated`

WebSocket is acceptable but not required.

## Important Rule

Realtime transport must never become the mechanism that guarantees business correctness.

The database and backend services remain authoritative.

---

# 43. Frontend Data Fetching

Use TanStack Query.

Recommended principles:

- Query keys by feature
- Invalidate/refetch after mutations
- Optimistic UI only where safe
- Do not optimistically mutate authoritative inventory
- Display backend conflict errors clearly
- Use periodic refetch if realtime is not implemented

---

# 44. UI / Visual Design Direction

The frontend should feel like:

- modern B2B SaaS + Light theme
- operational
- professional
- clean
- trustworthy
- information-dense without clutter

Avoid:

- decorative landing-page aesthetics
- excessive animations
- gaming-style visual effects
- unnecessary gradients
- excessive charts

The evaluator should immediately understand the workflow.

---

# 45. UI States

Every major screen must include:

## Loading

- Skeleton or clear progress indicator

## Empty State

Examples:

- No orders found
- No low-stock drugs
- No inventory movements

## Error State

- Human-readable message
- Retry where appropriate

## Success Feedback

- Order created
- Restock successful
- Order completed

---

# 46. Responsive Behaviour

Primary target:

- Desktop

Secondary:

- Tablet
- Mobile should remain usable but does not need full mobile-first optimization

Tables may convert to horizontal scrolling or stacked cards on narrow screens.

---

# 47. Security Basics

Even without authentication:

- Use environment variables for secrets
- Never commit DB credentials
- Restrict CORS to expected frontend domains
- Validate all input
- Use ORM/query parameterization
- Avoid raw untrusted SQL
- Sanitize error output
- Use HTTPS in cloud
- Use DB TLS if provider supports/requires it

---

# 48. Performance Principles

Use:

- Pagination
- Proper indexes
- Efficient joins
- Aggregate queries for dashboard metrics
- Avoid N+1 queries
- Limit transaction scope
- Avoid loading entire inventory/order history into memory

Redis caching should only be added after correctness.

---

# 49. Testing Strategy

Testing is mandatory.

## 49.1 Unit Tests

Test:

- Stock status calculation
- Threshold logic
- State transition validation
- Fulfilment decisions
- Dashboard metric calculations where isolated

## 49.2 Integration Tests

Test against a test database:

- Order creation
- Successful fulfilment
- Insufficient inventory
- Inventory deduction
- Restocking
- Pending fulfilment
- FIFO
- Inventory ledger creation
- Order completion
- Filtering/sorting

## 49.3 Concurrency Test

Important:

Two simultaneous order attempts against limited stock must not oversell inventory.

## 49.4 Frontend Tests

At minimum:

- Critical order form logic
- Inventory restock interaction
- Dashboard rendering if feasible

## 49.5 E2E

Optional but valuable:

One end-to-end scenario:

1. Create order
2. Goes waiting
3. Restock drug
4. Order becomes dispensed
5. Complete order
6. Dashboard updates

---

# 50. Critical Test Cases

1. Create order when stock is sufficient
2. Create order when stock is zero
3. Create order when stock is partially insufficient
4. Multiple medicines, all available
5. Multiple medicines, one unavailable
6. Stock cannot become negative
7. Restock increases inventory
8. Restock creates transaction ledger
9. Pending order reprocessed after restock
10. Multiple waiting orders follow FIFO
11. Partial restock fulfils only eligible FIFO orders
12. Invalid drug rejected
13. Invalid quantity rejected
14. Duplicate drug line rejected
15. Invalid state transition rejected
16. Completed order timestamp recorded
17. Average fulfilment time correct
18. Low-stock status correct
19. Critical/reorder status correct
20. Filters and sorting work
21. Concurrent order attempts do not oversell

---

# 51. Seed / Sample Data

Provide enough data to demonstrate:

## Drugs

Examples:

- Paracetamol 500 mg
- Amoxicillin 500 mg
- Azithromycin 250 mg
- Metformin 500 mg
- Atorvastatin 10 mg
- Cetirizine 10 mg
- Vitamin D3
- Omeprazole 20 mg

## Inventory States

Seed:

- Healthy stock
- Low stock
- Critical stock
- Out-of-stock

## Orders

Seed:

- Completed orders
- Dispensed orders
- Waiting-for-stock orders

This makes dashboard immediately useful after deployment.

---

# 52. Cloud Deployment

Cloud deployment is a core project requirement for demonstration.

## 52.1 Recommended Architecture

```text
Frontend:
React + TypeScript
Vercel

Backend:
FastAPI
Railway / Render / equivalent

Database:
Managed MySQL
```

## 52.2 URLs to Provide

The final submission should have:

- Live frontend URL
- Live backend URL
- Swagger/OpenAPI URL
- GitHub repository URL

---

# 53. Environment Variables

Recommended backend:

```text
APP_ENV
APP_NAME
DATABASE_URL
FRONTEND_ORIGIN
LOG_LEVEL
REDIS_URL            # optional
ENABLE_REALTIME      # optional
```

Frontend:

```text
VITE_API_BASE_URL
```

Never place secrets in frontend environment variables.

---

# 54. No-Laptop Demo Strategy

The full assessment must be demonstrable from a browser.

Recommended presentation flow:

1. Open live frontend
2. Show dashboard
3. Open New Order
4. Search medicine
5. Show availability
6. Create order that has insufficient stock
7. Show WAITING_FOR_STOCK
8. Open Inventory
9. Restock the blocking drug
10. Show automatic pending fulfilment
11. Show inventory history
12. Mark order completed
13. Return to dashboard
14. Show updated metrics
15. Open Swagger docs
16. Briefly show API design
17. Show GitHub/README/schema

---

# 55. Development Priorities

## P0 — Mandatory Assessment Compliance

Complete first:

- Order creation
- Inventory tracking
- Waiting/dispensed/completed
- Restocking
- Automatic processing
- Dashboard
- Filters/sorting
- Tests
- Logs
- DB schema
- README
- Sample data

## P1 — Backend Quality

Then:

- Modular architecture
- Transactions
- Concurrency safety
- Inventory ledger
- Validation
- Consistent errors
- Migrations
- Indexes

## P2 — Product Quality

Then:

- Strong order workspace
- Inventory UX
- Dashboard polish
- Responsive behaviour
- Loading/empty/error states

## P3 — Cloud

Then ensure:

- Live frontend
- Live backend
- Live MySQL
- Swagger

## P4 — Optional Enhancements

Only after P0–P3 are stable:

- Redis
- SSE/WebSocket
- Enhanced analytics

---

# 56. Implementation Sequence

Recommended build order:

## Phase 1 — Project Foundation

1. Create backend project
2. Configure FastAPI
3. Configure MySQL
4. Configure SQLAlchemy
5. Configure Alembic
6. Configure logging
7. Add health endpoint

## Phase 2 — Database

1. Patient model
2. Drug model
3. Inventory model
4. Order model
5. OrderItem model
6. InventoryTransaction model
7. Migrations
8. Seed data

## Phase 3 — Inventory Domain

1. Inventory repository
2. Stock status logic
3. Restock service
4. Inventory ledger
5. Tests

## Phase 4 — Order Domain

1. Order creation
2. Order items
3. Backend stock validation
4. Transactional stock deduction
5. Waiting state
6. Status state machine
7. Tests

## Phase 5 — Pending Fulfilment

1. FIFO query
2. Safe stock processing
3. Restock-triggered processing
4. Tests

## Phase 6 — Dashboard

1. Summary metrics
2. Low stock
3. Recent orders
4. Filtering/sorting/pagination

## Phase 7 — Frontend

1. Layout/navigation
2. Dashboard
3. Orders list
4. New Order workspace
5. Order details
6. Inventory
7. Restock
8. Error/loading/empty states

## Phase 8 — Deployment

1. Managed MySQL
2. Backend deployment
3. Frontend deployment
4. CORS
5. Seed production/demo data
6. Verify Swagger

## Phase 9 — Enhancements

1. Redis if justified
2. SSE/realtime
3. Extra analytics

---

# 57. Acceptance Criteria

## New Order

- Staff can enter patient
- Staff can search drugs
- UI shows stock
- Staff can add quantities
- Multiple medicines supported
- Order can be confirmed
- Backend validates stock authoritatively

## Inventory

- Current stock visible
- Low-stock states visible
- Restock works
- Ledger records movement

## Waiting Orders

- Insufficient stock creates waiting state
- Restock re-evaluates waiting orders
- FIFO respected

## Dashboard

- Correct totals
- Correct completed/pending
- Correct average fulfilment
- Low stock list
- Recent orders
- Filters/sorting

## Engineering

- MySQL used
- Tests exist and pass
- Logs exist
- DB schema documented
- Sample data available
- README available
- Cloud demo live

---

# 58. Definition of Done

The project is done when:

- All mandatory assessment requirements work
- No negative stock is possible
- Concurrent stock mutation is safe
- Pending fulfilment works
- Restock workflow works
- Dashboard metrics are correct
- Filters/sorting/pagination work
- Critical tests pass
- Structured logging exists
- Migrations exist
- Seed data exists
- Live cloud deployment works
- Swagger works
- Documentation is complete
- The evaluator can understand the architecture without asking for missing basics

---

# 59. Assessment Compliance Matrix

| Original Requirement | Implementation |
|---|---|
| Patient name | New Order form + Patient entity |
| Drug name | Drug search + OrderItem |
| Quantity | Requested quantity per OrderItem |
| Date/time | Order timestamps |
| Save to DB | MySQL via SQLAlchemy |
| Check inventory | Backend authoritative validation |
| Track stock | Inventory table |
| Low-stock flag | Threshold/status logic |
| Manual restocking | Inventory restock API/UI |
| Waiting status | WAITING_FOR_STOCK |
| Dispensed | DISPENSED |
| Completed | COMPLETED |
| Auto after restock | Pending FIFO fulfilment engine |
| Total orders today | Dashboard summary |
| Completed vs pending | Dashboard summary |
| Avg completion/fill time | Dashboard summary |
| Low-stock list | Dashboard + Inventory |
| Recent orders | Dashboard/Orders |
| Sort/filter | Orders APIs + UI |
| Python or Java | Python/FastAPI |
| React | React + TypeScript |
| MySQL | MySQL |
| Queue choice | DB-backed pending workflow |
| Cache choice | None initially; Redis optional |
| Structure choice | Modular monolith |
| Working code | Cloud live + repository |
| Setup instructions | README |
| Sample data | Seed script |
| Folder structure | Defined here |
| Tests | Unit + integration + concurrency |
| Logging | Structured logging |
| DB schema | Defined here |
| README | Required |
| No auth | No auth |
| No AI | No AI |
| No full inventory ERP | Scope-controlled |

---

# 60. Key Architectural Decisions and Rationale

## FastAPI

Chosen because:

- Excellent Python API development
- Strong type validation through Pydantic
- Swagger/OpenAPI generation
- Good testing support
- Suitable for clean layered backend

## MySQL

Chosen because:

- Explicit requirement
- Strong transactional support
- Appropriate for inventory consistency
- Managed cloud deployment available

## React + TypeScript

Chosen because:

- React explicitly required
- TypeScript improves reliability
- Suitable for operational dashboards

## Modular Monolith

Chosen because:

- Right-sized architecture
- Easier deployment
- Easier testing
- Strong module boundaries
- Avoids microservice overhead

## Redis Optional

Chosen only if useful.

Not needed for core correctness.

## SSE Optional

Preferred realtime approach because:

- Dashboard is mostly server → browser
- Simpler than WebSocket
- Core system does not depend on it

---

# 61. Trade-offs

## No Authentication

Reason:

Explicitly excluded by assessment.

## No Docker

Reason:

Not necessary for the current cloud-first demonstration strategy.

Can be added later if requested.

## No CI/CD Pipeline

Reason:

Not required and does not materially improve assessment evaluation.

Cloud platforms may still auto-deploy from Git.

## No Microservices

Reason:

Adds operational complexity without solving a current problem.

## No Kafka/RabbitMQ

Reason:

Database-driven pending workflow is sufficient at this scale.

---

# 62. Future Scalability Path

If this became a real large pharmacy platform, future evolution may include:

- Authentication/RBAC
- Multi-store inventory
- Warehouse inventory
- Supplier procurement
- Reservation logic
- Partial fulfilment
- Prescription document storage
- Notifications
- Multi-tenant support
- Event bus
- Distributed workers
- Redis caching
- Search service
- Reporting warehouse
- Real audit/compliance controls
- Monitoring/APM
- CI/CD
- Containers
- Horizontal API scaling

These are intentionally not part of the assessment implementation.

---

# 63. Coding Standards

## Backend

- Type hints
- Pydantic schemas
- Thin API controllers
- Business logic in services/domain layer
- Repository abstraction where useful
- No duplicated stock logic
- Explicit transaction handling
- Clear exceptions
- Structured logs

## Frontend

- TypeScript strictness
- Feature-oriented components
- Reusable UI primitives
- Query logic separated from view logic
- No direct DB assumptions
- Good error display
- Accessible forms

## Naming

Use consistent English naming.

Prefer explicit names over abbreviations.

---

# 64. Coding-Agent Guardrails

Any AI coding agent must follow these rules:

1. Do not change MySQL to PostgreSQL.
2. Do not use Supabase as the database.
3. Do not introduce authentication.
4. Do not introduce customer ecommerce.
5. Do not add payment or delivery.
6. Do not use AI/LLMs.
7. Do not introduce microservices.
8. Do not introduce Kafka/RabbitMQ.
9. Do not introduce Kubernetes.
10. Do not make Redis mandatory for core flows.
11. Do not trust frontend inventory as authoritative.
12. Do not mutate inventory outside backend services.
13. Do not allow stock to become negative.
14. Do not skip DB transactions for fulfilment.
15. Do not silently change FIFO behaviour.
16. Do not silently change status definitions.
17. Do not collapse order and inventory logic into one controller.
18. Do not implement business logic only in frontend.
19. Do not remove tests to move faster.
20. Do not change scope without explicit approval.
21. Preserve all mandatory assessment requirements.
22. Keep optional features isolated from the critical path.
23. Prefer maintainable code over clever code.
24. When ambiguity remains, document the assumption before implementation.

---

# 65. Demo Script

A strong evaluator demo should follow this story:

## Step 1 — Dashboard

Show:

- Orders today
- Completed
- Pending
- Average fulfilment
- Low stock

## Step 2 — Create Order

Patient:

`Alex Johnson`

Items:

- Paracetamol × 10
- Amoxicillin × 20

Assume:

- Paracetamol has enough stock
- Amoxicillin does not

Show:

- Live availability
- Confirm order
- Order goes WAITING_FOR_STOCK

## Step 3 — Inventory

Open Amoxicillin.

Show:

- Current stock
- Low/critical status
- Transaction history

Restock:

`+100`

## Step 4 — Automatic Fulfilment

Show:

- Pending order automatically re-evaluated
- Inventory deducted
- Ledger updated
- Order becomes DISPENSED

## Step 5 — Complete

Complete the order.

Show:

- COMPLETED status
- completed_at

## Step 6 — Dashboard

Return to dashboard.

Show updated:

- Completed count
- Pending count
- Inventory status
- Average fulfilment time

## Step 7 — Engineering

Open Swagger.

Explain:

- REST API
- FastAPI
- MySQL
- Transactions
- FIFO
- Concurrency safety
- Tests
- Logging
- Inventory ledger

---

# 66. Interview Talking Points

Use these explanations when discussing architecture.

## Why is stock displayed before order confirmation?

To help staff make an informed decision during order entry.

But the backend validates again at confirmation because displayed stock may be stale.

## Why separate Inventory page?

Order page needs contextual inventory visibility.

Inventory administration must remain controlled and auditable.

## Why MySQL transactions?

Inventory is shared mutable state.

Without transactional handling, concurrent orders may oversell stock.

## Why FIFO?

The original requirement did not define prioritization.

FIFO is deterministic, fair, simple, and explicitly documented.

## Why inventory ledger?

Current stock alone does not explain how the quantity changed.

The ledger provides business traceability.

## Why modular monolith?

It provides clear boundaries without unnecessary distributed-system overhead.

## Why not Redis first?

Redis does not solve core inventory correctness.

MySQL remains the source of truth.

Redis is only useful after core correctness is established.

## Why SSE instead of WebSocket?

The main realtime need is backend → dashboard updates.

SSE is simpler for that communication pattern.

## Why no Docker/CI/CD?

They are not required for the assessment.

Engineering time is better invested in business correctness, tests, transactions, and cloud demonstration.

---

# 67. Final Product Statement

> **A production-minded Pharmacy Order Fulfilment & Inventory Operations platform built with React, FastAPI, and MySQL. It enables pharmacy staff to capture prescription orders, view medicine availability, safely fulfil or queue orders, manage restocking, automatically process eligible waiting orders, and gives managers a real-time-capable operational dashboard with strong inventory integrity, traceability, testing, and cloud deployment.**

---

# 68. Final Engineering Principle

The submission should make the evaluator think:

> This developer did not add complexity for show.  
> They understood the business problem, preserved the requirements, designed the domain correctly, protected inventory integrity, documented assumptions, tested critical workflows, and delivered a clean production-minded system.

That is the target quality bar.

