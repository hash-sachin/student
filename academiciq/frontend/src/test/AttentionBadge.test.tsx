/**
 * Tests for AttentionBadge — non-stigmatizing language, ESTIMATED label, all bands.
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import { AttentionBadge } from '@/components/AttentionBadge'
import { describe, it, expect } from 'vitest'

describe('AttentionBadge', () => {
  it('renders NORMAL band without stigmatizing language', () => {
    render(<AttentionBadge band="NORMAL" />)
    expect(screen.getByText(/NORMAL/)).toBeInTheDocument()
    // Must not say "weak" or "bad"
    expect(screen.queryByText(/weak/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/bad/i)).not.toBeInTheDocument()
  })

  it('renders HIGH_ATTENTION using supportive language', () => {
    render(<AttentionBadge band="HIGH_ATTENTION" />)
    expect(screen.getByText(/HIGH ATTENTION REQUIRED/)).toBeInTheDocument()
    // Non-stigmatizing: uses "Required" not "Failing"
    expect(screen.queryByText(/failing/i)).not.toBeInTheDocument()
  })

  it('shows ESTIMATED label on every band', () => {
    for (const band of ['NORMAL', 'MONITOR', 'ATTENTION', 'HIGH_ATTENTION'] as const) {
      const { unmount } = render(<AttentionBadge band={band} />)
      expect(screen.getByText(/ESTIMATED/)).toBeInTheDocument()
      unmount()
    }
  })

  it('shows score when provided', () => {
    render(<AttentionBadge band="ATTENTION" score={62} />)
    expect(screen.getByText(/62/)).toBeInTheDocument()
  })

  it('shows partial indicator when isPartial=true', () => {
    render(<AttentionBadge band="MONITOR" score={30} isPartial={true} />)
    expect(screen.getByText(/partial/i)).toBeInTheDocument()
  })
})
