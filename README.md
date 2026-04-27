# Expense Tracker

A full-stack personal expense tracking application built with **FastAPI**, **PostgreSQL**, and **Next.js**.

Built for real-world conditions: idempotent API operations, Decimal money arithmetic, JWT-based authentication, and a resilient UI that handles slow networks, failed requests, and duplicate submissions gracefully.

**Live:** https://expense-tracker-taupe-rho.vercel.app
**API Docs:** https://expense-tracker-tr3i.onrender.com/docs

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

---

## Notes

### Key design decisions

| Decision | Why |
|----------|-----|
| **Idempotent POST** | The biggest correctness risk is duplicate entries from retries, double-clicks, or refreshes. Every `POST /expenses` takes an `Idempotency-Key` header; the backend stores the key + response atomically and replays it on retries — no duplicates regardless of how many times the client retries. |
| **Decimal, not float** | Floats cannot represent most decimal fractions exactly. Money uses `decimal.Decimal` in Python, `NUMERIC(10,2)` in PostgreSQL, and is sent as a string over the wire to avoid JSON precision loss. |
| **PostgreSQL** | ACID transactions ensure the expense row and idempotency record are always written together or not at all. Also provides `NUMERIC` for exact money storage and enforces a `CHECK (amount > 0)` constraint at the DB level. |
| **Thin routes, logic in services** | Routes handle only HTTP concerns. All business logic lives in `services/` so it can be tested directly without going through HTTP. |

### Trade-offs made because of the timebox

| Trade-off | What was skipped and why |
|-----------|--------------------------|
| **No pagination** | The list is unbounded per user. Acceptable at personal scale; cursor-based pagination would be the next addition. |
| **localStorage for JWT** | Simpler than `httpOnly` cookies + CSRF tokens. A production app would use `httpOnly` cookies to protect against XSS. |
| **No token refresh** | Tokens expire after 60 min and redirect to login. A refresh flow was deprioritised in favour of correctness features. |
| **No rate limiting** | Would be added via middleware or an API gateway before real production use. |

### Intentionally not done

| Item | Reason |
|------|--------|
| **Managed category resource** | Categories are free-text strings. A `POST /categories` endpoint would add normalisation overhead without improving the core feature. |
| **Email verification** | Out of scope — registration accepts any valid email format. |
| **CI/CD pipeline** | Pushes to `main` auto-deploy via Render and Vercel hooks, which is sufficient here. A GitHub Actions workflow with test gating would be the obvious next step. |

---

## Features

- Add expenses with amount, category, description, and date
- View all expenses in a sortable, filterable table
- Filter by category; sort by date (newest or oldest first)
- Total of currently visible expenses updates with filters
- Per-category spending breakdown with proportional bars
- Idempotent expense creation — safe to retry or double-submit
- JWT authentication — each user sees only their own data
- Full input validation on both frontend and backend

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
│   │   ├── api/          # Routes + dependency injection
│   │   ├── core/         # Config (env vars), structured logging
│   │   ├── db/           # Engine, session factory, declarative base
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic v2 request/response schemas
│   │   ├── services/     # Business logic (expense, auth)
│   │   └── utils/        # Idempotency key hashing
│   ├── alembic/          # Database migrations
│   ├── tests/            # pytest integration test suite (25 tests)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── start.sh          # Runs migrations then starts uvicorn
├── frontend/
│   └── src/
│       ├── app/          # Next.js App Router pages
│       ├── components/   # ExpenseForm, ExpenseList, Filters, TotalBar, CategorySummary
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

### Expenses (require `Authorization: Bearer <token>`)

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

PostgreSQL was chosen for financial data because it provides:

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

The `POST /api/expenses` endpoint is fully idempotent via a client-provided `Idempotency-Key` header:

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

JWT (HS256) with 60-minute expiry. Passwords are hashed with `bcrypt` directly. Tokens are stored in `localStorage`; any 401 response auto-redirects to the login page. The `user_id` on every expense is set from the verified JWT — never from the request body — so users are strictly isolated.

---

## Reliability Scenarios

| Scenario | How it is handled |
|----------|------------------|
| User double-clicks Submit | `isSubmitting` disables button and all form inputs immediately |
| Network retry of completed POST | Idempotency key returns the stored response, no duplicate created |
| Page refresh after submit | Data persisted in PostgreSQL; re-fetched on mount |
| Slow API response | Spinner shown, inputs disabled, button shows "Adding..." |
| Failed API call | Error banner shown with a Retry button |
| JWT expiry | Any 401 clears localStorage and redirects to `/login` |
| Pydantic validation error (422) | Error messages extracted and shown in the form |

---

## Validation

**Backend (Pydantic v2 + DB constraints):**
- `amount` — must be > 0, max 10 digits, 2 decimal places, rounded with `ROUND_HALF_UP`
- `category` — 1–50 characters, required
- `description` — optional, max 255 characters
- `date` — required ISO date
- DB `CHECK (amount > 0)` and `NOT NULL` constraints as a final backstop

**Frontend (`src/lib/validation.ts`):**
- Mirrors backend rules so the user sees errors immediately, without a round-trip
- Inputs are disabled during in-flight requests to prevent concurrent submissions

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

**25 tests, all passing.**

**POST /api/expenses**

| Test | What it verifies |
|------|-----------------|
| `test_create_success_returns_201` | Valid expense → 201, correct fields in response |
| `test_idempotency_same_key_same_body_replays` | Same key + same body → stored response, no duplicate row |
| `test_idempotency_same_key_different_body_returns_409` | Same key + different body → 409 Conflict |
| `test_negative_amount_returns_422` | Negative amount rejected |
| `test_zero_amount_returns_422` | Zero amount rejected — must be strictly positive |
| `test_missing_category_returns_422` | Missing required field → 422 |
| `test_missing_date_returns_422` | Missing date → 422 |
| `test_missing_idempotency_key_header_returns_400` | Missing required header → 400 |
| `test_unauthenticated_returns_403` | No token → 403 |

**GET /api/expenses**

| Test | What it verifies |
|------|-----------------|
| `test_empty_list` | No expenses → empty list, zero total |
| `test_filter_by_category` | Only expenses matching category returned |
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

## Trade-offs

| Decision | Rationale |
|----------|-----------|
| **No pagination** | List is bounded per-user; not a scalability concern at this size. Cursor-based pagination would be the next addition. |
| **localStorage for JWT** | Simpler than `httpOnly` cookies + CSRF tokens. In production, `httpOnly` cookies are safer against XSS. |
| **SQLite for tests** | Eliminates Docker dependency. Tests use SQLAlchemy's generic `JSON` type so idempotency storage works on both SQLite and PostgreSQL. |
| **No rate limiting** | Would be added in production via middleware or an API gateway. |
| **No refresh tokens** | Single 60-minute JWT is acceptable here. Production would add token rotation. |

---

## Security

- **SQL injection** — prevented by SQLAlchemy ORM parameterised queries
- **Password hashing** — `bcrypt` with per-password salt
- **Input validation** — Pydantic enforces types, lengths, and ranges at the API boundary
- **CORS** — restricted to the configured frontend origin only
- **No stack traces in responses** — global exception handler returns generic 500 messages
- **JWT signing** — HS256 with a configurable `SECRET_KEY` env var

---

## Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Backend | PostgreSQL connection string (`postgresql+psycopg://...`) |
| `SECRET_KEY` | Backend | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Backend | Token lifetime (default: 60) |
| `CORS_ORIGINS` | Backend | Comma-separated allowed origins |
| `POSTGRES_USER` | DB | PostgreSQL username |
| `POSTGRES_PASSWORD` | DB | PostgreSQL password |
| `POSTGRES_DB` | DB | Database name |
| `NEXT_PUBLIC_API_URL` | Frontend | Backend base URL (baked in at build time) |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | FastAPI 0.111 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Database | PostgreSQL 15 |
| DB driver | psycopg 3 |
| Validation | Pydantic v2 |
| Auth | python-jose + bcrypt |
| Frontend | Next.js 16 + React 19 + TypeScript |
| Styling | Tailwind CSS v4 |
| Containerisation | Docker + Compose |
| Backend hosting | Render |
| Frontend hosting | Vercel |
