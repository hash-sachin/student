/**
 * Tests for MetricBadge — verifies all four label types render with text (not color alone).
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import { MetricBadge } from '@/components/MetricBadge'
import { describe, it, expect } from 'vitest'

describe('MetricBadge', () => {
  it('renders OFFICIAL label', () => {
    render(<MetricBadge label="OFFICIAL" />)
    expect(screen.getByText('OFFICIAL')).toBeInTheDocument()
  })

  it('renders CALCULATED label', () => {
    render(<MetricBadge label="CALCULATED" />)
    expect(screen.getByText('CALCULATED')).toBeInTheDocument()
  })

  it('renders ESTIMATED label', () => {
    render(<MetricBadge label="ESTIMATED" />)
    expect(screen.getByText('ESTIMATED')).toBeInTheDocument()
  })

  it('renders HYPOTHETICAL label', () => {
    render(<MetricBadge label="HYPOTHETICAL" />)
    expect(screen.getByText('HYPOTHETICAL')).toBeInTheDocument()
  })

  it('includes aria-label with description', () => {
    const { container } = render(<MetricBadge label="OFFICIAL" />)
    const el = container.querySelector('[aria-label]')
    expect(el?.getAttribute('aria-label')).toContain('OFFICIAL')
    expect(el?.getAttribute('aria-label')).toContain('source document')
  })
})
