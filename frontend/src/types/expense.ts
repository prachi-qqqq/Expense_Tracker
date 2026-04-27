/** Types for Expense entities — shared between API and UI */

export interface Expense {
  id: string;
  amount: string;
  category: string;
  description: string | null;
  date: string;
  created_at: string;
  user_id: string;
}

export interface ExpenseCreate {
  amount: string;
  category: string;
  description?: string;
  date: string;
}

export interface ExpenseListResponse {
  expenses: Expense[];
  total: string;
  count: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ValidationErrorItem {
  loc: string[];
  msg: string;
  type: string;
}

export interface ApiError {
  detail: string | ValidationErrorItem[];
}
