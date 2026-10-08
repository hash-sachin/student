/**
 * AttentionBadge — displays the Academic Attention Band.
 * Colorblind-safe: uses text labels and patterns, not color alone.
 * WCAG 2.1 AA compliant.
 * Label: ESTIMATED (always shown).
 */
import React from 'react'
import type { AttentionBand } from '@/types'

const BAND_CONFIG: Record<AttentionBand, {
  label: string
  className: string
  icon: string
  description: string
}> = {
  NORMAL: {
    label: 'NORMAL',
    className: 'bg-green-100 text-green-800 ring-1 ring-green-400',
    icon: '●',
    description: 'No academic attention indicated at this time.',
  },
  MONITOR: {
    label: 'MONITOR',
    className: 'bg-amber-100 text-amber-800 ring-1 ring-amber-400',
    icon: '◆',
    description: 'Academic performance warrants monitoring.',
  },
  ATTENTION: {
    label: 'ATTENTION REQUIRED',
    className: 'bg-orange-100 text-orange-800 ring-1 ring-orange-400',
    icon: '▲',
    description: 'Academic Attention Required — please review with faculty.',
  },
  HIGH_ATTENTION: {
    label: 'HIGH ATTENTION REQUIRED',
    className: 'bg-red-100 text-red-800 ring-1 ring-red-400',
    icon: '■',
    description: 'High Academic Attention Required — immediate faculty review recommended.',
  },
}

interface AttentionBadgeProps {
  band: AttentionBand
  score?: number
  isPartial?: boolean
}

export function AttentionBadge({ band, score, isPartial }: AttentionBadgeProps) {
  const config = BAND_CONFIG[band]
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-semibold ${config.className}`}
      title={config.description}
      aria-label={`Academic attention band: ${config.label}${score !== undefined ? `, score: ${score}` : ''}${isPartial ? ' (partial score)' : ''}. ${config.description}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      {config.label}
      {score !== undefined && <span className="ml-1 font-mono">({score})</span>}
      {isPartial && (
        <span
          className="ml-1 text-xs opacity-75"
          title="Score is partial — some factors could not be evaluated due to insufficient history"
        >
          *partial
        </span>
      )}
      <span className="ml-1 text-xs opacity-60">[ESTIMATED]</span>
    </span>
  )
}
