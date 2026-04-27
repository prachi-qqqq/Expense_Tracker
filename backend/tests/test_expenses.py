"""Tests for expense creation (idempotency) and listing (filtering)."""

import uuid

from fastapi.testclient import TestClient


class TestCreateExpense:
    """Tests for POST /api/expenses with idempotency."""

    def test_create_expense_success(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Creating an expense with valid data returns 201."""
        key = str(uuid.uuid4())
        response = client.post(
            "/api/expenses",
            json={
                "amount": "150.50",
                "category": "Food",
                "description": "Lunch",
                "date": "2024-06-15",
            },
            headers={**auth_headers, "Idempotency-Key": key},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == "150.50"
        assert data["category"] == "Food"

    def test_idempotency_same_key_same_body(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Same Idempotency-Key + same body returns the same response."""
        key = str(uuid.uuid4())
        payload = {
            "amount": "200.00",
            "category": "Transport",
            "description": "Taxi",
            "date": "2024-06-15",
        }
        headers = {**auth_headers, "Idempotency-Key": key}

        resp1 = client.post("/api/expenses", json=payload, headers=headers)
        resp2 = client.post("/api/expenses", json=payload, headers=headers)

        assert resp1.status_code == 201
        # Second call should return stored response (could be 200 or 201)
        assert resp2.status_code in (200, 201)
        assert resp1.json()["id"] == resp2.json()["id"]

    def test_idempotency_same_key_different_body(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Same Idempotency-Key + different body returns 409 Conflict."""
        key = str(uuid.uuid4())
        headers = {**auth_headers, "Idempotency-Key": key}

        client.post(
            "/api/expenses",
            json={
                "amount": "100.00",
                "category": "Food",
                "date": "2024-06-15",
            },
            headers=headers,
        )

        resp2 = client.post(
            "/api/expenses",
            json={
                "amount": "999.00",
                "category": "Shopping",
                "date": "2024-07-01",
            },
            headers=headers,
        )
        assert resp2.status_code == 409

    def test_create_expense_invalid_amount(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Amount <= 0 should fail validation."""
        key = str(uuid.uuid4())
        response = client.post(
            "/api/expenses",
            json={
                "amount": "-10.00",
                "category": "Food",
                "date": "2024-06-15",
            },
            headers={**auth_headers, "Idempotency-Key": key},
        )
        assert response.status_code == 422

    def test_create_expense_missing_fields(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Missing required fields should fail validation."""
        key = str(uuid.uuid4())
        response = client.post(
            "/api/expenses",
            json={"amount": "50.00"},
            headers={**auth_headers, "Idempotency-Key": key},
        )
        assert response.status_code == 422


class TestListExpenses:
    """Tests for GET /api/expenses with filtering."""

    def _create_expense(
        self,
        client: TestClient,
        headers: dict[str, str],
        amount: str,
        category: str,
        date: str,
    ) -> None:
        """Helper to create an expense."""
        key = str(uuid.uuid4())
        client.post(
            "/api/expenses",
            json={
                "amount": amount,
                "category": category,
                "date": date,
            },
            headers={**headers, "Idempotency-Key": key},
        )

    def test_list_expenses_empty(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Listing with no expenses returns empty list."""
        response = client.get("/api/expenses", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["expenses"] == []

    def test_list_expenses_filter_by_category(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Filtering by category returns only matching expenses."""
        self._create_expense(client, auth_headers, "100.00", "Food", "2024-06-15")
        self._create_expense(client, auth_headers, "50.00", "Transport", "2024-06-16")
        self._create_expense(client, auth_headers, "75.00", "Food", "2024-06-17")

        response = client.get(
            "/api/expenses?category=Food", headers=auth_headers
        )
        data = response.json()
        assert data["count"] == 2
        assert all(e["category"] == "Food" for e in data["expenses"])

    def test_list_expenses_sort_newest_first(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Default sort returns newest expenses first."""
        self._create_expense(client, auth_headers, "100.00", "Food", "2024-01-01")
        self._create_expense(client, auth_headers, "200.00", "Food", "2024-12-31")

        response = client.get("/api/expenses", headers=auth_headers)
        data = response.json()
        dates = [e["date"] for e in data["expenses"]]
        assert dates == sorted(dates, reverse=True)

    def test_list_expenses_total_matches_visible(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Total should match the sum of visible (filtered) expenses."""
        self._create_expense(client, auth_headers, "100.00", "Food", "2024-06-15")
        self._create_expense(client, auth_headers, "50.00", "Transport", "2024-06-16")

        # Total for all
        response = client.get("/api/expenses", headers=auth_headers)
        assert response.json()["total"] == "150.00"

        # Total for Food only
        response = client.get("/api/expenses?category=Food", headers=auth_headers)
        assert response.json()["total"] == "100.00"


class TestAuth:
    """Tests for authentication endpoints."""

    def test_register_success(self, client: TestClient) -> None:
        """Registration with valid data returns 201 + token."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "password": "securepass123",
                "name": "New User",
            },
        )
        assert response.status_code == 201
        assert "access_token" in response.json()

    def test_register_duplicate_email(self, client: TestClient) -> None:
        """Registration with existing email returns 409."""
        payload = {
            "email": "dup@example.com",
            "password": "securepass123",
            "name": "User",
        }
        client.post("/api/auth/register", json=payload)
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 409

    def test_login_success(self, client: TestClient) -> None:
        """Login with valid credentials returns a token."""
        client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "securepass123",
                "name": "Login User",
            },
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "securepass123"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client: TestClient) -> None:
        """Login with wrong password returns 401."""
        client.post(
            "/api/auth/register",
            json={
                "email": "wrong@example.com",
                "password": "securepass123",
                "name": "User",
            },
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "wrong@example.com", "password": "badpassword"},
        )
        assert response.status_code == 401

    def test_protected_route_no_token(self, client: TestClient) -> None:
        """Accessing expenses without a token returns 403."""
        response = client.get("/api/expenses")
        assert response.status_code == 403
