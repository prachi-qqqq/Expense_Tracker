/** API client for backend communication */

import type {
  ExpenseCreate,
  ExpenseListResponse,
  TokenResponse,
  ApiError,
} from "@/types/expense";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  private authHeaders(): Record<string, string> {
    const token = this.getToken();
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorBody: ApiError = await response.json().catch(() => ({
        detail: `Request failed with status ${response.status}`,
      }));

      if (response.status === 401) {
        // Token expired or invalid — clear and redirect
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
          window.location.href = "/login";
        }
      }

      throw new Error(errorBody.detail);
    }
    return response.json() as Promise<T>;
  }

  // --- Auth ---

  async register(
    email: string,
    password: string,
    name: string
  ): Promise<TokenResponse> {
    const response = await fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name }),
    });
    return this.handleResponse<TokenResponse>(response);
  }

  async login(email: string, password: string): Promise<TokenResponse> {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    return this.handleResponse<TokenResponse>(response);
  }

  // --- Expenses ---

  async createExpense(
    data: ExpenseCreate,
    idempotencyKey: string
  ): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_URL}/api/expenses`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": idempotencyKey,
        ...this.authHeaders(),
      },
      body: JSON.stringify(data),
    });
    return this.handleResponse<Record<string, unknown>>(response);
  }

  async listExpenses(
    category?: string,
    sort: string = "date_desc"
  ): Promise<ExpenseListResponse> {
    const params = new URLSearchParams({ sort });
    if (category) params.set("category", category);

    const response = await fetch(
      `${API_URL}/api/expenses?${params.toString()}`,
      {
        headers: this.authHeaders(),
      }
    );
    return this.handleResponse<ExpenseListResponse>(response);
  }
}

export const api = new ApiClient();
