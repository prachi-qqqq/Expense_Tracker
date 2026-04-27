"use client";

import type { Expense } from "@/types/expense";

interface FiltersProps {
  categories: string[];
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
  sort: string;
  onSortChange: (sort: string) => void;
}

export default function Filters({
  categories,
  selectedCategory,
  onCategoryChange,
  sort,
  onSortChange,
}: FiltersProps) {
  return (
    <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-4 shadow-xl">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
        {/* Category Filter */}
        <div className="flex-1 w-full sm:w-auto">
          <label
            htmlFor="filter-category"
            className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1.5"
          >
            Category
          </label>
          <select
            id="filter-category"
            value={selectedCategory}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all appearance-none cursor-pointer"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {/* Sort */}
        <div className="flex-1 w-full sm:w-auto">
          <label
            htmlFor="filter-sort"
            className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1.5"
          >
            Sort by Date
          </label>
          <select
            id="filter-sort"
            value={sort}
            onChange={(e) => onSortChange(e.target.value)}
            className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all appearance-none cursor-pointer"
          >
            <option value="date_desc">Newest First</option>
            <option value="date_asc">Oldest First</option>
          </select>
        </div>
      </div>
    </div>
  );
}
