import React from 'react'

interface EmptyStateProps {
  title: string
  description?: string
  action?: React.ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="text-center py-16 text-gray-400">
      <p className="text-4xl mb-3" aria-hidden="true">⊘</p>
      <p className="font-medium text-gray-600">{title}</p>
      {description && <p className="text-sm mt-1">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
