/**
 * MetricBadge — shows metric type label on every number displayed.
 * Required by spec: every number shown anywhere carries exactly one label.
 * WCAG 2.1 AA compliant: uses text, not just color.
 */
import React from 'react'
import type { MetricLabel } from '@/types'

const BADGE_CONFIG: Record<MetricLabel, { label: string; className: string; title: string }> = {
  OFFICIAL: {
    label: 'OFFICIAL',
    className: 'bg-blue-100 text-blue-800 ring-1 ring-blue-300',
    title: 'Extracted directly from the source document',
  },
  CALCULATED: {
    label: 'CALCULATED',
    className: 'bg-green-100 text-green-800 ring-1 ring-green-300',
    title: 'Derived deterministically from official data',
  },
  ESTIMATED: {
    label: 'ESTIMATED',
    className: 'bg-amber-100 text-amber-800 ring-1 ring-amber-300',
    title: 'Heuristic or model output — not a verified fact',
  },
  HYPOTHETICAL: {
    label: 'HYPOTHETICAL',
    className: 'bg-purple-100 text-purple-800 ring-1 ring-purple-300',
    title: 'What-if simulation output only — NOT an actual result',
  },
}

interface MetricBadgeProps {
  label: MetricLabel
  className?: string
}

export function MetricBadge({ label, className = '' }: MetricBadgeProps) {
  const config = BADGE_CONFIG[label]
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${config.className} ${className}`}
      title={config.title}
      aria-label={`Metric type: ${config.label}. ${config.title}`}
    >
      {config.label}
    </span>
  )
}
