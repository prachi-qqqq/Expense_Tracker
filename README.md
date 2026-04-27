# Expense Tracker

A full-stack personal expense tracking application built with **FastAPI**, **PostgreSQL**, and **Next.js**.

Designed for real-world conditions: idempotent API operations, Decimal money arithmetic, JWT authentication, and resilient UI behaviour under slow or failed network requests.

**Live:** https://expense-tracker-taupe-rho.vercel.app  
**API:** https://expense-tracker-tr3i.onrender.com/docs

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

---

## What Was Built

### Acceptance Criteria Coverage

| # | Requirement | Status |
|---|-------------|--------|
| 1 | Create expense with amount, category, description, date | ✅ |
| 2 | View a list of expenses | ✅ |
| 3 | Filter expenses by category | ✅ |
| 4 | Sort expenses by date (newest first) | ✅ |
| 5 | Display total of currently visible expenses | ✅ |
| + | Idempotent POST (safe retries / double-submit) | ✅ |
| + | Backend + frontend validation | ✅ |
| + | Loading and error states in UI | ✅ |
| + | Automated backend test suite (pytest) | ✅ |

---

## Quick Start (Docker)

```bash
git clone https://github.com/prachi-qqqq/Expense_Tracker.git
cd Expense_Tracker
cp .env.example .env
docker-compose up --build
```

| Service  | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend  | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health   | http://localhost:8000/health |

---

## Project Structure

```
Expense_Tracker/
├── backend/
│   ├── app/
│   │   ├── api/          # Routes (thin) + dependency injection
│   │   ├── core/         # Config (env vars), structured logging
│   │   ├── db/           # Engine, session factory, declarative base
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic v2 request/response schemas
│   │   ├── services/     # Business logic (expense, auth)
│   │   └── utils/        # Idempotency key hashing
│   ├── alembic/          # Database migrations
│   ├── tests/            # pytest integration test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── start.sh          # Runs migrations then starts uvicorn
├── frontend/
│   └── src/
│       ├── app/          # Next.js App Router pages
│       ├── components/   # ExpenseForm, ExpenseList, Filters, TotalBar
│       ├── contexts/     # AuthContext — JWT + localStorage
│       ├── lib/          # API client, validation utilities
│       └── types/        # TypeScript interfaces
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Reference

### Authentication

```
POST /api/auth/register   { email, password, name } → { access_token, user }
POST /api/auth/login      { email, password }        → { access_token, user }
```

### Expenses (all require `Authorization: Bearer <token>`)

```
POST /api/expenses
  Headers: Idempotency-Key: <uuid>
  Body:    { amount, category, description?, date }
  → 201 Created | 200 OK (replay) | 409 Conflict (key reused with different body)

GET /api/expenses?category=Food&sort=date_desc
  → { expenses: [...], total: "150.00", count: 3 }
```

---

## Key Design Decisions

### Persistence: PostgreSQL

PostgreSQL was chosen over SQLite or an in-memory store for:

- **ACID transactions** — the expense record and idempotency record are written atomically. A crash mid-write cannot produce a half-committed expense without a matching idempotency key.
- **NUMERIC(10,2)** — native fixed-point decimal type. Floats are never used for money at any layer.
- **JSON column** — the idempotency response body is stored as JSON (JSONB in the PostgreSQL migration), allowing the exact original response to be replayed without re-querying the expenses table.
- **CHECK constraint** — `CHECK (amount > 0)` enforced at the database level as a last line of defence.

### Money Handling

Floating-point arithmetic is not used for money at any layer:

| Layer | Type |
|-------|------|
| Database | `NUMERIC(10, 2)` with `CHECK (amount > 0)` |
| Python | `decimal.Decimal` — validated and rounded via `ROUND_HALF_UP` |
| API wire format | String (`"150.50"`) — never a JSON number |
| Frontend display | `Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" })` |

### Idempotency on POST /expenses

The assignment explicitly calls out unreliable networks, browser refreshes, and retries. The `POST /api/expenses` endpoint is made fully idempotent via a client-provided `Idempotency-Key` header:

1. The frontend generates a `crypto.randomUUID()` per submission attempt.
2. The backend hashes the request body using stable JSON serialisation (sorted keys) + SHA-256.
3. On each request:
   - **Key unseen** → create expense, store `(key, body_hash, response)` atomically.
   - **Key seen + hash matches** → return the stored response (HTTP 200 replay).
   - **Key seen + hash differs** → return 409 Conflict.

This means:
- Double-clicking Submit → second request replays the first, no duplicate row.
- Page refresh after a slow response → retry gets the same result.
- Network retry of a completed request → idempotent, safe.

### Authentication

JWT (HS256) with 60-minute expiry. Passwords are hashed with `bcrypt` directly (not through passlib, which is abandoned and incompatible with bcrypt ≥ 4.x). Tokens are stored in `localStorage`; a 401 response auto-redirects to the login page. Each user only sees their own expenses — the `user_id` foreign key is set from the verified JWT, never from the request body.

---

## Trade-offs Made

| Decision | Rationale |
|----------|-----------|
| **No pagination** | List is bounded per-user; not a scalability concern at this size. Cursor-based pagination would be the next addition. |
| **localStorage for JWT** | Simpler than `httpOnly` cookies + CSRF tokens for a timebox exercise. In production, `httpOnly` cookies are safer against XSS. |
| **SQLite for tests** | Eliminates Docker dependency. Tests use SQLAlchemy's generic `JSON` type so idempotency storage works on both SQLite and PostgreSQL. |
| **No rate limiting** | Would be added in production via middleware or an API gateway. |
| **No refresh tokens** | Single 60-minute JWT is acceptable for a demo. Production would add token rotation. |

---

## Nice-to-Have: What Was and Was Not Done

The assignment listed four optional items. Three were completed:

| Item | Status | Notes |
|------|--------|-------|
| Basic validation (negative amounts, required date) | ✅ Done | Pydantic v2 on backend, mirrored in `validation.ts` on frontend |
| A couple of automated tests | ✅ Done | 25 pytest integration tests covering all core flows |
| Basic error and loading states in UI | ✅ Done | Spinner, disabled inputs, error banners, retry button |
| Summary view (total per category) | ❌ Not done | `GET /expenses` already returns a `total` for the filtered list. A full per-category breakdown would require a separate aggregation endpoint or frontend grouping — deprioritised in favour of getting the core flows solid. |

---

## Reliability Scenarios

| Scenario | How it is handled |
|----------|------------------|
| User double-clicks Submit | `isSubmitting` state disables button and all form inputs immediately |
| Network retry of completed POST | Idempotency key returns the stored response, no duplicate created |
| Page refresh after submit | Data is persisted in PostgreSQL; re-fetch on mount shows the expense |
| Slow API response | Spinner shown, form inputs disabled, button shows "Adding..." |
| Failed API call | Error banner shown with a Retry button |
| JWT expiry | Any 401 response clears localStorage and redirects to `/login` |
| FastAPI validation error (422) | Array of Pydantic error messages joined and shown in the form |

---

## Validation

**Backend (Pydantic v2 + DB constraints):**
- `amount` — must be > 0, max 10 digits, 2 decimal places, rounded with `ROUND_HALF_UP`
- `category` — 1–50 characters, required
- `description` — optional, max 255 characters
- `date` — required ISO date
- DB `CHECK (amount > 0)` and `NOT NULL` constraints as a final backstop

**Frontend (`src/lib/validation.ts`):**
- Mirrors backend rules so the user sees errors immediately, before a round-trip
- Validation runs on submit; form inputs are disabled during in-flight requests

---

## Automated Tests

```bash
# Run locally (SQLite, no Docker needed)
cd backend
pip install -r requirements.txt
pytest -v

# Run inside Docker
docker-compose exec backend pytest -v
```

### Coverage (25 tests, all passing)

**POST /api/expenses**

| Test | What it verifies |
|------|-----------------|
| `test_create_success_returns_201` | Valid expense → 201, correct fields in response |
| `test_idempotency_same_key_same_body_replays` | Same key + same body → stored response, no duplicate row |
| `test_idempotency_same_key_different_body_returns_409` | Same key + different body → 409 Conflict |
| `test_negative_amount_returns_422` | Negative amount rejected by validation |
| `test_zero_amount_returns_422` | Zero amount rejected — must be strictly positive |
| `test_missing_category_returns_422` | Missing required field → 422 |
| `test_missing_date_returns_422` | Missing date → 422 |
| `test_missing_idempotency_key_header_returns_400` | Missing required header → 400/422 |
| `test_unauthenticated_returns_403` | No token → 403 |

**GET /api/expenses**

| Test | What it verifies |
|------|-----------------|
| `test_empty_list` | No expenses → empty list, zero total |
| `test_filter_by_category` | Only expenses matching category are returned |
| `test_filter_by_category_no_match` | Filter with no matches → empty list |
| `test_sort_newest_first_by_default` | Default sort → newest date first |
| `test_sort_date_desc_explicit` | `sort=date_desc` → newest first |
| `test_sort_date_asc` | `sort=date_asc` → oldest first |
| `test_total_matches_all_expenses` | Total equals sum of all expenses |
| `test_total_matches_filtered_expenses` | Total reflects filtered subset only |
| `test_user_sees_only_own_expenses` | User A cannot see User B's expenses |
| `test_unauthenticated_returns_403` | No token → 403 |

**Authentication**

| Test | What it verifies |
|------|-----------------|
| `test_register_returns_201_with_token` | New user registration → JWT |
| `test_register_duplicate_email_returns_409` | Duplicate email → 409 |
| `test_login_valid_credentials_returns_token` | Correct credentials → JWT |
| `test_login_wrong_password_returns_401` | Wrong password → 401 |
| `test_login_unknown_email_returns_401` | Unknown email → 401 |
| `test_register_short_password_returns_422` | Password < 8 chars → 422 |

---

## Security

- **SQL injection** — prevented by SQLAlchemy ORM parameterised queries
- **Password hashing** — `bcrypt` with per-password salt (cost factor 12)
- **Input validation** — Pydantic enforces types, lengths, and ranges at the API boundary
- **CORS** — restricted to the configured frontend origin only
- **No stack traces in responses** — global exception handler returns generic 500 messages
- **JWT signing** — HS256 with a configurable `SECRET_KEY` env var

---

## Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Backend | PostgreSQL connection string (`postgresql+psycopg://...`) |
| `SECRET_KEY` | Backend | JWT signing secret — use a long random string in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Backend | Token lifetime (default: 60) |
| `CORS_ORIGINS` | Backend | Comma-separated allowed origins |
| `POSTGRES_USER` | DB | PostgreSQL username |
| `POSTGRES_PASSWORD` | DB | PostgreSQL password |
| `POSTGRES_DB` | DB | Database name |
| `NEXT_PUBLIC_API_URL` | Frontend | Backend base URL (baked in at build time) |

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend framework | FastAPI 0.111 | Type-safe, async-capable, auto OpenAPI docs, excellent DI |
| ORM | SQLAlchemy 2.0 | Typed mapped columns, modern Pythonic API |
| Migrations | Alembic | Schema versioning, reproducible deploys |
| Database | PostgreSQL 15 | ACID, NUMERIC type, JSONB |
| DB driver | psycopg 3 | Native async support, binary protocol |
| Validation | Pydantic v2 | Fast, declarative, integrates with FastAPI |
| Auth | python-jose + bcrypt | Standard JWT + safe password hashing |
| Frontend | Next.js 16 + React 19 | App Router, TypeScript-first, Vercel-native |
| Styling | Tailwind CSS v4 | Utility-first, no runtime overhead |
| Containerisation | Docker + Compose | Reproducible local environment |
| Backend hosting | Render | Docker-native deploys, managed PostgreSQL |
| Frontend hosting | Vercel | Zero-config Next.js, global CDN |
