/**
 * StatCard — dashboard metric card with metric label.
 * Every displayed number carries its MetricLabel per spec Section 3.
 */
import React from 'react'
import { MetricBadge } from './MetricBadge'
import type { MetricLabel } from '@/types'

interface StatCardProps {
  title: string
  value: string | number | null
  label: MetricLabel
  description?: string
  trend?: 'up' | 'down' | 'stable' | null
  trendValue?: string
  loading?: boolean
}

export function StatCard({
  title,
  value,
  label,
  description,
  trend,
  trendValue,
  loading,
}: StatCardProps) {
  const trendColor =
    trend === 'up'
      ? 'text-green-600'
      : trend === 'down'
      ? 'text-red-600'
      : 'text-gray-500'
  const trendIcon = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-2 shadow-sm">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-gray-500 leading-tight">{title}</p>
        <MetricBadge label={label} />
      </div>

      {loading ? (
        <div className="h-8 bg-gray-100 rounded animate-pulse w-20" aria-busy="true" />
      ) : (
        <p className="text-2xl font-bold text-gray-900 tabular-nums">
          {value ?? <span className="text-gray-400 text-base">—</span>}
        </p>
      )}

      <div className="flex items-center gap-2 mt-1">
        {trendValue && trend && (
          <span className={`text-xs font-medium ${trendColor}`} aria-label={`Trend: ${trend}`}>
            <span aria-hidden="true">{trendIcon}</span> {trendValue}
          </span>
        )}
        {description && (
          <span className="text-xs text-gray-400">{description}</span>
        )}
      </div>
    </div>
  )
}
