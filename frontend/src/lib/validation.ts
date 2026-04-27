/** Frontend validation rules — mirror backend Pydantic constraints */

export interface ValidationResult {
  valid: boolean;
  message?: string;
}

export function validateAmount(value: string): ValidationResult {
  const n = parseFloat(value);
  if (isNaN(n) || n <= 0) return { valid: false, message: "Amount must be a positive number" };
  if (!/^\d+(\.\d{1,2})?$/.test(value.trim()))
    return { valid: false, message: "Amount must have at most 2 decimal places" };
  if (n > 99_999_999.99)
    return { valid: false, message: "Amount exceeds maximum value" };
  return { valid: true };
}

export function validateCategory(value: string): ValidationResult {
  if (!value.trim()) return { valid: false, message: "Category is required" };
  if (value.length > 50) return { valid: false, message: "Category must be 50 characters or less" };
  return { valid: true };
}

export function validateDescription(value: string): ValidationResult {
  if (value.length > 255) return { valid: false, message: "Description must be 255 characters or less" };
  return { valid: true };
}

export function validateExpenseForm(
  amount: string,
  category: string,
  description: string
): string | null {
  const checks = [
    validateAmount(amount),
    validateCategory(category),
    validateDescription(description),
  ];
  const failed = checks.find((r) => !r.valid);
  return failed?.message ?? null;
}
