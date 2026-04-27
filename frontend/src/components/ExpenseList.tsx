"use client";

import type { Expense } from "@/types/expense";

interface ExpenseListProps {
  expenses: Expense[];
  isLoading: boolean;
}

function formatCurrency(amount: string): string {
  const num = parseFloat(amount);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
  }).format(num);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr + "T00:00:00").toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

// Category color mapping for visual variety
const categoryColors: Record<string, string> = {
  food: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  transport: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  shopping: "bg-pink-500/20 text-pink-400 border-pink-500/30",
  entertainment: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  health: "bg-red-500/20 text-red-400 border-red-500/30",
  bills: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  education: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
};

function getCategoryStyle(category: string): string {
  const key = category.toLowerCase();
  return (
    categoryColors[key] || "bg-gray-500/20 text-gray-400 border-gray-500/30"
  );
}

export default function ExpenseList({
  expenses,
  isLoading,
}: ExpenseListProps) {
  if (isLoading) {
    return (
      <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-8 shadow-xl">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 text-sm">Loading expenses...</p>
        </div>
      </div>
    );
  }

  if (expenses.length === 0) {
    return (
      <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-8 shadow-xl text-center">
        <div className="w-16 h-16 mx-auto mb-4 bg-gray-800 rounded-2xl flex items-center justify-center">
          <svg
            className="w-8 h-8 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
        </div>
        <p className="text-gray-400 text-lg font-medium">No expenses yet</p>
        <p className="text-gray-500 text-sm mt-1">
          Add your first expense to get started
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl shadow-xl overflow-hidden">
      <div className="p-6 border-b border-gray-800">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <span className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center text-blue-400 text-sm">
            📋
          </span>
          Expenses
          <span className="ml-auto text-sm font-normal text-gray-500">
            {expenses.length} {expenses.length === 1 ? "item" : "items"}
          </span>
        </h2>
      </div>

      {/* Mobile: Cards | Desktop: Table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full" id="expense-table">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                Date
              </th>
              <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                Category
              </th>
              <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                Description
              </th>
              <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                Amount
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/50">
            {expenses.map((expense) => (
              <tr
                key={expense.id}
                className="hover:bg-gray-800/30 transition-colors"
              >
                <td className="px-6 py-4 text-sm text-gray-300 whitespace-nowrap">
                  {formatDate(expense.date)}
                </td>
                <td className="px-6 py-4">
                  <span
                    className={`inline-block px-3 py-1 text-xs font-medium rounded-full border ${getCategoryStyle(expense.category)}`}
                  >
                    {expense.category}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-400 max-w-xs truncate">
                  {expense.description || "—"}
                </td>
                <td className="px-6 py-4 text-sm text-white font-semibold text-right whitespace-nowrap">
                  {formatCurrency(expense.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden divide-y divide-gray-800/50">
        {expenses.map((expense) => (
          <div key={expense.id} className="p-4 hover:bg-gray-800/30 transition-colors">
            <div className="flex justify-between items-start mb-2">
              <span
                className={`inline-block px-3 py-1 text-xs font-medium rounded-full border ${getCategoryStyle(expense.category)}`}
              >
                {expense.category}
              </span>
              <span className="text-white font-semibold">
                {formatCurrency(expense.amount)}
              </span>
            </div>
            {expense.description && (
              <p className="text-sm text-gray-400 mb-1">{expense.description}</p>
            )}
            <p className="text-xs text-gray-500">{formatDate(expense.date)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
