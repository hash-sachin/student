/**
 * Shared formatting utilities.
 */

/** Format a number as a marks value (1 decimal place, with fallback). */
export function formatMarks(value: number | null | undefined): string {
  if (value == null) return '—'
  return value.toFixed(1)
}

/** Format a percentage (2 decimal places). */
export function formatPercent(value: number | null | undefined): string {
  if (value == null) return '—'
  return `${value.toFixed(2)}%`
}

/** Format bytes to human-readable string. */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/** Format ISO date string to locale date. */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/** Format ISO date string to locale date+time. */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Truncate a UUID to first 8 chars for display. */
export function shortId(id: string): string {
  return id.slice(0, 8) + '…'
}
