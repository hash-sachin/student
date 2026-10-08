/**
 * Tests that HypotheticalBanner always renders the mandatory text.
 * Acceptance criterion #8: present in 100% of simulation UI outputs.
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import { HypotheticalBanner } from '@/components/HypotheticalBanner'
import { describe, it, expect } from 'vitest'

describe('HypotheticalBanner', () => {
  it('renders the HYPOTHETICAL SCENARIO banner text', () => {
    render(<HypotheticalBanner />)
    expect(screen.getByText(/HYPOTHETICAL SCENARIO/)).toBeInTheDocument()
    expect(screen.getByText(/NOT AN ACTUAL RESULT/)).toBeInTheDocument()
  })

  it('has role="alert" for screen reader announcement', () => {
    render(<HypotheticalBanner />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('mentions arithmetic consequences, not causal claims', () => {
    render(<HypotheticalBanner />)
    expect(screen.getByText(/arithmetic consequences/i)).toBeInTheDocument()
  })
})
