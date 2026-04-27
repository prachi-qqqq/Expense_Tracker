"use client";

import type { Expense } from "@/types/expense";

interface CategorySummaryProps {
  expenses: Expense[];
  isLoading: boolean;
}

export default function CategorySummary({ expenses, isLoading }: CategorySummaryProps) {
  if (isLoading) {
    return (
      <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6">
        <div className="h-4 w-32 bg-gray-800 rounded animate-pulse mb-4" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex justify-between items-center py-2">
            <div className="h-3 w-20 bg-gray-800 rounded animate-pulse" />
            <div className="h-3 w-16 bg-gray-800 rounded animate-pulse" />
          </div>
        ))}
      </div>
    );
  }

  if (expenses.length === 0) return null;

  // Compute total per category from the current expense list
  const categoryMap = new Map<string, number>();
  for (const e of expenses) {
    const prev = categoryMap.get(e.category) ?? 0;
    categoryMap.set(e.category, prev + parseFloat(e.amount));
  }

  const rows = Array.from(categoryMap.entries())
    .map(([category, total]) => ({ category, total }))
    .sort((a, b) => b.total - a.total);

  const grandTotal = rows.reduce((s, r) => s + r.total, 0);

  const fmt = (n: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(n);

  const COLOURS = [
    "bg-emerald-500",
    "bg-teal-500",
    "bg-cyan-500",
    "bg-sky-500",
    "bg-violet-500",
    "bg-pink-500",
    "bg-amber-500",
    "bg-orange-500",
  ];

  return (
    <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6 shadow-xl">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
        By Category
      </h2>
      <ul className="space-y-3">
        {rows.map(({ category, total }, idx) => {
          const pct = grandTotal > 0 ? (total / grandTotal) * 100 : 0;
          const bar = COLOURS[idx % COLOURS.length];
          return (
            <li key={category}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-white truncate max-w-[60%]">{category}</span>
                <span className="text-sm font-medium text-white">{fmt(total)}</span>
              </div>
              <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${bar} transition-all duration-500`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
