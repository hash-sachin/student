/**
 * HypotheticalBanner — mandatory banner for all what-if simulation outputs.
 * Must appear in 100% of UI simulation outputs (acceptance criterion #8).
 * Uses hatched styling per spec Section 9.
 * WCAG compliant: visible text + role="alert".
 */
import React from 'react'

export function HypotheticalBanner() {
  return (
    <div
      role="alert"
      aria-live="polite"
      className="hypothetical-banner p-3 flex items-center gap-2 mb-4"
    >
      <span className="text-purple-700 font-bold text-sm">⚠</span>
      <span className="text-purple-800 font-semibold text-sm">
        HYPOTHETICAL SCENARIO — NOT AN ACTUAL RESULT
      </span>
      <span className="text-purple-600 text-xs">
        This simulation shows arithmetic consequences of changed marks only.
        No causal or predictive claims are made.
      </span>
    </div>
  )
}
