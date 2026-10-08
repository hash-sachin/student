import React from 'react'

interface ErrorMessageProps {
  message?: string
  retry?: () => void
}

export function ErrorMessage({ message = 'Something went wrong.', retry }: ErrorMessageProps) {
  return (
    <div role="alert" className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
      <p>{message}</p>
      {retry && (
        <button
          onClick={retry}
          className="mt-2 text-red-600 underline hover:no-underline focus:outline-none focus:ring-2 focus:ring-red-500 rounded"
        >
          Retry
        </button>
      )}
    </div>
  )
}
