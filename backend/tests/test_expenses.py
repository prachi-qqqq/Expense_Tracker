"""Integration tests for expense creation, listing, and authentication."""

import uuid

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_expense(
    client: TestClient,
    headers: dict,
    amount: str = "100.00",
    category: str = "Food",
    date: str = "2024-06-15",
    description: str | None = None,
) -> dict:
    """Create an expense and return the response JSON."""
    payload: dict = {"amount": amount, "category": category, "date": date}
    if description:
        payload["description"] = description
    resp = client.post(
        "/api/expenses",
        json=payload,
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    return resp


def _register_and_login(client: TestClient, email: str) -> dict:
    """Register a fresh user and return auth headers."""
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123", "name": "Test"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# POST /api/expenses — creation and idempotency
# ---------------------------------------------------------------------------

class TestCreateExpense:

    def test_create_success_returns_201(self, client, auth_headers):
        """Valid expense returns 201 with correct fields."""
        resp = _make_expense(client, auth_headers, amount="150.50", category="Food")
        assert resp.status_code == 201
        data = resp.json()
        assert data["amount"] == "150.50"
        assert data["category"] == "Food"
        assert "id" in data
        assert "created_at" in data

    def test_idempotency_same_key_same_body_replays(self, client, auth_headers):
        """Same key + same body returns the same response (no duplicate row)."""
        key = str(uuid.uuid4())
        payload = {"amount": "200.00", "category": "Transport", "date": "2024-06-15"}
        headers = {**auth_headers, "Idempotency-Key": key}

        r1 = client.post("/api/expenses", json=payload, headers=headers)
        r2 = client.post("/api/expenses", json=payload, headers=headers)

        assert r1.status_code == 201
        assert r2.status_code in (200, 201)
        assert r1.json()["id"] == r2.json()["id"]

        # Only one expense should exist
        listing = client.get("/api/expenses", headers=auth_headers).json()
        assert listing["count"] == 1

    def test_idempotency_same_key_different_body_returns_409(self, client, auth_headers):
        """Same key + different body → 409 Conflict."""
        key = str(uuid.uuid4())
        headers = {**auth_headers, "Idempotency-Key": key}

        client.post("/api/expenses",
                    json={"amount": "100.00", "category": "Food", "date": "2024-06-15"},
                    headers=headers)

        resp = client.post("/api/expenses",
                           json={"amount": "999.00", "category": "Shopping", "date": "2024-07-01"},
                           headers=headers)
        assert resp.status_code == 409

    def test_negative_amount_returns_422(self, client, auth_headers):
        """Negative amount is rejected by validation."""
        resp = _make_expense(client, auth_headers, amount="-10.00")
        assert resp.status_code == 422

    def test_zero_amount_returns_422(self, client, auth_headers):
        """Zero amount is rejected — must be strictly positive."""
        resp = _make_expense(client, auth_headers, amount="0.00")
        assert resp.status_code == 422

    def test_missing_category_returns_422(self, client, auth_headers):
        """Missing required field returns 422."""
        resp = client.post(
            "/api/expenses",
            json={"amount": "50.00", "date": "2024-06-15"},
            headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert resp.status_code == 422

    def test_missing_date_returns_422(self, client, auth_headers):
        """Missing date returns 422."""
        resp = client.post(
            "/api/expenses",
            json={"amount": "50.00", "category": "Food"},
            headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert resp.status_code == 422

    def test_missing_idempotency_key_header_returns_400(self, client, auth_headers):
        """Missing Idempotency-Key header returns 400 or 422."""
        resp = client.post(
            "/api/expenses",
            json={"amount": "50.00", "category": "Food", "date": "2024-06-15"},
            headers=auth_headers,
        )
        assert resp.status_code in (400, 422)

    def test_unauthenticated_returns_403(self, client):
        """No token → 403."""
        resp = client.post(
            "/api/expenses",
            json={"amount": "50.00", "category": "Food", "date": "2024-06-15"},
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/expenses — listing, filtering, sorting, totals
# ---------------------------------------------------------------------------

class TestListExpenses:

    def test_empty_list(self, client, auth_headers):
        """No expenses returns empty list with zero total."""
        resp = client.get("/api/expenses", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["expenses"] == []
        assert data["count"] == 0

    def test_filter_by_category(self, client, auth_headers):
        """Only expenses matching the category are returned."""
        _make_expense(client, auth_headers, amount="100.00", category="Food")
        _make_expense(client, auth_headers, amount="50.00", category="Transport")
        _make_expense(client, auth_headers, amount="75.00", category="Food")

        resp = client.get("/api/expenses?category=Food", headers=auth_headers)
        data = resp.json()
        assert data["count"] == 2
        assert all(e["category"] == "Food" for e in data["expenses"])

    def test_filter_by_category_no_match(self, client, auth_headers):
        """Filtering by a category with no expenses returns empty list."""
        _make_expense(client, auth_headers, category="Food")

        resp = client.get("/api/expenses?category=Shopping", headers=auth_headers)
        data = resp.json()
        assert data["count"] == 0
        assert data["expenses"] == []

    def test_sort_newest_first_by_default(self, client, auth_headers):
        """Default sort returns newest expense first."""
        _make_expense(client, auth_headers, amount="100.00", date="2024-01-01")
        _make_expense(client, auth_headers, amount="200.00", date="2024-12-31")

        resp = client.get("/api/expenses", headers=auth_headers)
        dates = [e["date"] for e in resp.json()["expenses"]]
        assert dates == sorted(dates, reverse=True)

    def test_sort_date_desc_explicit(self, client, auth_headers):
        """sort=date_desc returns newest first."""
        _make_expense(client, auth_headers, date="2024-03-01")
        _make_expense(client, auth_headers, date="2024-09-01")

        resp = client.get("/api/expenses?sort=date_desc", headers=auth_headers)
        dates = [e["date"] for e in resp.json()["expenses"]]
        assert dates == sorted(dates, reverse=True)

    def test_sort_date_asc(self, client, auth_headers):
        """sort=date_asc returns oldest first."""
        _make_expense(client, auth_headers, date="2024-09-01")
        _make_expense(client, auth_headers, date="2024-03-01")

        resp = client.get("/api/expenses?sort=date_asc", headers=auth_headers)
        dates = [e["date"] for e in resp.json()["expenses"]]
        assert dates == sorted(dates)

    def test_total_matches_all_expenses(self, client, auth_headers):
        """Total equals sum of all expenses when no filter applied."""
        _make_expense(client, auth_headers, amount="100.00", category="Food")
        _make_expense(client, auth_headers, amount="50.00", category="Transport")

        resp = client.get("/api/expenses", headers=auth_headers)
        assert resp.json()["total"] == "150.00"

    def test_total_matches_filtered_expenses(self, client, auth_headers):
        """Total reflects only the filtered subset, not all expenses."""
        _make_expense(client, auth_headers, amount="100.00", category="Food")
        _make_expense(client, auth_headers, amount="50.00", category="Transport")

        resp = client.get("/api/expenses?category=Food", headers=auth_headers)
        assert resp.json()["total"] == "100.00"

    def test_user_sees_only_own_expenses(self, client):
        """User A cannot see User B's expenses."""
        headers_a = _register_and_login(client, "user_a@example.com")
        headers_b = _register_and_login(client, "user_b@example.com")

        _make_expense(client, headers_a, amount="300.00", category="Food")

        resp = client.get("/api/expenses", headers=headers_b)
        assert resp.json()["count"] == 0

    def test_unauthenticated_returns_403(self, client):
        """No token → 403."""
        assert client.get("/api/expenses").status_code == 403


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class TestAuth:

    def test_register_returns_201_with_token(self, client):
        resp = client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "securepass123", "name": "New User"},
        )
        assert resp.status_code == 201
        assert "access_token" in resp.json()

    def test_register_duplicate_email_returns_409(self, client):
        payload = {"email": "dup@example.com", "password": "securepass123", "name": "User"}
        client.post("/api/auth/register", json=payload)
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 409

    def test_login_valid_credentials_returns_token(self, client):
        client.post("/api/auth/register",
                    json={"email": "login@example.com", "password": "securepass123", "name": "User"})
        resp = client.post("/api/auth/login",
                           json={"email": "login@example.com", "password": "securepass123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password_returns_401(self, client):
        client.post("/api/auth/register",
                    json={"email": "wrong@example.com", "password": "securepass123", "name": "User"})
        resp = client.post("/api/auth/login",
                           json={"email": "wrong@example.com", "password": "badpassword"})
        assert resp.status_code == 401

    def test_login_unknown_email_returns_401(self, client):
        resp = client.post("/api/auth/login",
                           json={"email": "nobody@example.com", "password": "anything"})
        assert resp.status_code == 401

    def test_register_short_password_returns_422(self, client):
        """Password under 8 characters is rejected."""
        resp = client.post("/api/auth/register",
                           json={"email": "short@example.com", "password": "abc", "name": "User"})
        assert resp.status_code == 422
