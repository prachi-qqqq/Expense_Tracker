# 🚀 Fenmo — Production-Grade Expense Tracker

A full-stack expense tracking application built with **FastAPI**, **PostgreSQL**, and **Next.js**, featuring idempotent operations, JWT authentication, and Docker deployment.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

---

## 📦 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Ports **3000**, **8000**, and **5432** available

### Run

```bash
# Clone and start
cd fenmo
docker-compose up --build
```

| Service    | URL                        |
|------------|----------------------------|
| Frontend   | http://localhost:3000       |
| Backend    | http://localhost:8000       |
| API Docs   | http://localhost:8000/docs  |
| Health     | http://localhost:8000/health|

---

## 🏗️ Architecture

```
fenmo/
├── backend/           # FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── api/       # Routes (thin) + Dependencies
│   │   ├── core/      # Config, Logging
│   │   ├── db/        # Engine, Session, Base
│   │   ├── models/    # SQLAlchemy models (DB only)
│   │   ├── schemas/   # Pydantic v2 (validation only)
│   │   ├── services/  # Business logic
│   │   └── utils/     # Idempotency helpers
│   ├── alembic/       # Database migrations
│   ├── tests/         # pytest suite
│   └── Dockerfile
├── frontend/          # Next.js App Router + TypeScript
│   ├── src/
│   │   ├── app/       # Pages (login, register, dashboard)
│   │   ├── components/# ExpenseForm, ExpenseList, Filters, TotalBar
│   │   ├── contexts/  # AuthContext (JWT + localStorage)
│   │   ├── lib/       # API client
│   │   └── types/     # TypeScript interfaces
│   └── Dockerfile
├── docker-compose.yml
└── .env
```

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **FastAPI** | Async-capable, type-safe with Pydantic, automatic OpenAPI docs, excellent DI system |
| **PostgreSQL** | ACID compliance for financial data, CHECK constraints, JSONB for idempotency responses |
| **Decimal (not float)** | Floats introduce rounding errors in monetary calculations. `Numeric(10,2)` in SQL + Python `Decimal` ensures exact arithmetic |
| **SQLAlchemy 2.0** | Typed mapped columns, modern Pythonic API, excellent ecosystem |
| **Next.js App Router** | Server components, built-in routing, TypeScript-first, optimized production builds |
| **JWT (not sessions)** | Stateless auth scales horizontally, no server-side session store needed |

---

## 🔁 Idempotency Strategy

The POST `/api/expenses` endpoint is **fully idempotent** via the `Idempotency-Key` header:

```
POST /api/expenses
Headers: { "Idempotency-Key": "uuid-v4", "Authorization": "Bearer <token>" }
```

### How It Works

1. **Hash the request body** using stable JSON serialization (sorted keys) + SHA-256
2. **Check if the idempotency key exists** in the `idempotency_keys` table:
   - ✅ **Key exists + hash matches** → Return the stored response (replay)
   - ❌ **Key exists + hash differs** → Return `409 Conflict`
   - 🆕 **Key doesn't exist** → Process the request
3. **Atomically** create the expense AND store the idempotency record in a single database transaction

### Why This Matters

- **Double-click submit**: Second click replays the first response
- **Network retry**: Same request gets the same result
- **Page refresh**: Data is already persisted
- **Different payload with same key**: Caught as a conflict

---

## 🔐 Authentication

- **Registration**: `POST /api/auth/register` → bcrypt-hashed password + JWT
- **Login**: `POST /api/auth/login` → JWT access token (60min expiry)
- **Protected routes**: All `/api/expenses` endpoints require `Bearer <token>`
- **Expense isolation**: Each user only sees their own expenses

---

## 💰 Money Handling

| Layer | Type |
|-------|------|
| Database | `NUMERIC(10,2)` with `CHECK (amount > 0)` |
| Backend | Python `Decimal` — never `float` |
| API | String serialization (`"150.50"` not `150.5`) |
| Frontend | `Intl.NumberFormat("en-IN")` with INR currency |

---

## ⚠️ Reliability Scenarios Handled

| Scenario | Solution |
|----------|----------|
| Double click submit | `isSubmitting` state disables button |
| Retry same request | Idempotency key returns stored response |
| Page refresh after submit | Data persisted in PostgreSQL |
| Slow backend | Loading states + spinner UI |
| Failed API calls | Error display + retry button |
| Token expiry | Auto-redirect to login on 401 |

---

## 🧪 Testing

```bash
# Run backend tests (inside Docker)
docker-compose exec backend pytest -v

# Or locally with SQLite (no Docker needed)
cd backend
pip install -r requirements.txt
pytest -v
```

### Test Coverage

- ✅ Expense creation (valid data)
- ✅ Idempotency: same key + same body → same response
- ✅ Idempotency: same key + different body → 409
- ✅ Validation: negative amount returns 422
- ✅ Validation: missing fields returns 422
- ✅ Filtering by category
- ✅ Sort order (newest first)
- ✅ Total matches visible expenses
- ✅ Auth: register, login, duplicate email, wrong password
- ✅ Protected routes: 403 without token

---

## 🔐 Security

- **Input validation**: Pydantic enforces field types, lengths, and constraints
- **SQL injection**: Prevented by SQLAlchemy ORM (parameterized queries)
- **Password hashing**: bcrypt via passlib
- **No sensitive logs**: Stack traces never exposed in API responses
- **CORS**: Configured for frontend origin only
- **JWT**: Signed with HS256, configurable expiry

---

## ⚖️ Tradeoffs

| Tradeoff | Rationale |
|----------|-----------|
| **No pagination** | Acceptable for MVP; list is bounded by user's expenses. Add cursor-based pagination for scale. |
| **Simple UI** | Focus is on correct backend behavior (idempotency, Decimal). UI is functional and polished but not a design showcase. |
| **LocalStorage for JWT** | Simpler than httpOnly cookies. For production, consider httpOnly cookie + CSRF token. |
| **SQLite for tests** | Fast test execution without Docker. Production uses PostgreSQL. Some edge cases (JSONB) may behave differently. |
| **No rate limiting** | Would add in production to prevent abuse. |

---

## 🚀 Future Improvements

- [ ] **Pagination**: Cursor-based pagination for the expense list
- [ ] **Caching**: Redis for frequently accessed data
- [ ] **Rate limiting**: Per-user rate limits on POST endpoints
- [ ] **Refresh tokens**: Token rotation with short-lived access tokens
- [ ] **Total per category**: Aggregated spending by category
- [ ] **Export**: CSV/PDF export of expenses
- [ ] **Dark/Light theme**: Theme toggle
- [ ] **PWA**: Offline support with service workers
- [ ] **CI/CD**: GitHub Actions pipeline with automated tests

---

## 📄 Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Backend | PostgreSQL connection string |
| `SECRET_KEY` | Backend | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Backend | Token expiry (default: 60) |
| `CORS_ORIGINS` | Backend | Allowed CORS origins |
| `POSTGRES_USER` | DB | PostgreSQL username |
| `POSTGRES_PASSWORD` | DB | PostgreSQL password |
| `POSTGRES_DB` | DB | Database name |
| `NEXT_PUBLIC_API_URL` | Frontend | Backend API base URL |

---

## 📝 License

MIT
