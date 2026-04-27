"use client";

interface TotalBarProps {
  total: string;
  count: number;
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

export default function TotalBar({ total, count, isLoading }: TotalBarProps) {
  return (
    <div className="bg-gradient-to-r from-emerald-500/10 to-teal-500/10 backdrop-blur-sm border border-emerald-500/20 rounded-2xl p-6 shadow-xl">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-emerald-400/80 uppercase tracking-wider">
            Total Expenses
          </p>
          <p className="text-3xl font-bold text-white mt-1">
            {isLoading ? (
              <span className="inline-block w-32 h-8 bg-gray-700/50 rounded-lg animate-pulse" />
            ) : (
              formatCurrency(total)
            )}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-400">
            {isLoading ? "—" : `${count} ${count === 1 ? "expense" : "expenses"}`}
          </p>
          <div className="w-12 h-12 mt-2 bg-emerald-500/20 rounded-xl flex items-center justify-center">
            <svg
              className="w-6 h-6 text-emerald-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}
