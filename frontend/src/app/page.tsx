"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import ProtectedRoute from "@/components/ProtectedRoute";
import ExpenseForm from "@/components/ExpenseForm";
import ExpenseList from "@/components/ExpenseList";
import Filters from "@/components/Filters";
import TotalBar from "@/components/TotalBar";
import CategorySummary from "@/components/CategorySummary";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/api";
import type { Expense } from "@/types/expense";

function Dashboard() {
  const { user, logout } = useAuth();
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [total, setTotal] = useState("0.00");
  const [count, setCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [sort, setSort] = useState("date_desc");

  const fetchExpenses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listExpenses(
        selectedCategory || undefined,
        sort
      );
      setExpenses(data.expenses);
      setTotal(data.total);
      setCount(data.count);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load expenses"
      );
    } finally {
      setIsLoading(false);
    }
  }, [selectedCategory, sort]);

  useEffect(() => {
    fetchExpenses();
  }, [fetchExpenses]);

  // Compute unique categories from all expenses for the filter dropdown
  const categories = useMemo(() => {
    const cats = new Set(expenses.map((e) => e.category));
    return Array.from(cats).sort();
  }, [expenses]);

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-gray-800/50 bg-gray-950/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <span className="text-lg font-bold text-white">₹</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Expense Tracker</h1>
              <p className="text-xs text-gray-500">Personal Finance</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:block text-right">
              <p className="text-sm font-medium text-white">{user?.name}</p>
              <p className="text-xs text-gray-500">{user?.email}</p>
            </div>
            <button
              id="logout-button"
              onClick={logout}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white border border-gray-700 hover:border-gray-600 rounded-xl transition-all hover:bg-gray-800/50"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Form + Category Summary */}
          <div className="lg:col-span-1 space-y-6">
            <ExpenseForm onSuccess={fetchExpenses} />
            <CategorySummary expenses={expenses} isLoading={isLoading} />
          </div>

          {/* Right Column: List + Filters */}
          <div className="lg:col-span-2 space-y-6">
            <TotalBar total={total} count={count} isLoading={isLoading} />
            <Filters
              categories={categories}
              selectedCategory={selectedCategory}
              onCategoryChange={setSelectedCategory}
              sort={sort}
              onSortChange={setSort}
            />

            {error && (
              <div className="flex items-center justify-between px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl">
                <span className="text-red-400 text-sm">{error}</span>
                <button
                  id="retry-button"
                  onClick={fetchExpenses}
                  className="px-3 py-1 text-xs font-medium text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/10 transition-colors"
                >
                  Retry
                </button>
              </div>
            )}

            <ExpenseList expenses={expenses} isLoading={isLoading} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default function HomePage() {
  return (
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  );
}
