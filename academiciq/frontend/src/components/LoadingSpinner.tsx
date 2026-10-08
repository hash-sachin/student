import React from 'react'

export function LoadingSpinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div
      role="status"
      aria-label={label}
      className="flex items-center justify-center py-12 text-gray-400"
    >
      <svg
        className="animate-spin h-6 w-6 mr-2"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
      </svg>
      <span className="text-sm">{label}</span>
    </div>
  )
}
