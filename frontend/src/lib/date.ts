// Shared date formatting for reader-facing dates.

/**
 * Format an ISO date as "January 1, 2026", or null if absent/unparseable.
 *
 * The NaN guard is load-bearing: `toLocaleDateString` does NOT throw on an
 * invalid date, it returns the literal string "Invalid Date" — which would
 * render straight to the reader.
 */
export function formatDate(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
}
