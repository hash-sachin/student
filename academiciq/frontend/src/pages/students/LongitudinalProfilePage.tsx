/**
 * LongitudinalProfilePage — full academic history, semester timeline,
 * attention scores, detected patterns, and evidence links.
 * All metric values display their MetricBadge label.
 */
import React, { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useProfile } from '@/hooks/useProfile'
import { PageHeader } from '@/components/PageHeader'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { MetricBadge } from '@/components/MetricBadge'
import { AttentionBadge } from '@/components/AttentionBadge'
import { SemesterTrendChart } from '@/charts/SemesterTrendChart'
import type { TimelineEntry } from '@/types'

export default function LongitudinalProfilePage() {
  const { id } = useParams<{ id: string }>()
  const { data: profile, isLoading, isError, refetch } = useProfile(id!)
  const [expandedSem, setExpandedSem] = useState<string | null>(null)

  if (isLoading) return <LoadingSpinner label="Loading longitudinal profile…" />
  if (isError || !profile) return <ErrorMessage retry={refetch} />

  const student = profile.student
  const agg = profile.aggregate_metrics

  // Build chart data
  const chartData = profile.timeline.map((entry, i) => ({
    label: entry.academic_year ?? `Sem ${i + 1}`,
    average: entry.semester_metrics.average,
    passed: entry.semester_metrics.subjects_passed,
    failed: entry.semester_metrics.subjects_failed,
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <PageHeader
        title={`${student.name} — Longitudinal Academic Profile`}
        subtitle={`Register No: ${student.register_number} · ${student.status}`}
        actions={
          <Link
            to={`/simulation/what-if?student_id=${id}`}
            className="px-4 py-2 text-sm bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            ◇ What-If Simulator
          </Link>
        }
      />

      {/* Profile note */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs text-blue-700">
        {profile.profile_note}
      </div>

      {/* Aggregate metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Semesters', value: agg.semesters_with_data, unit: '' },
          { label: 'Overall Average', value: agg.overall_average?.toFixed(2) ?? '—', unit: '' },
          { label: 'Total Arrears', value: agg.total_arrears, unit: '' },
        ].map(item => (
          <div key={item.label} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <p className="text-xs text-gray-500">{item.label}</p>
            <p className="text-2xl font-bold text-gray-900 tabular-nums mt-1">
              {item.value}{item.unit}
            </p>
            <MetricBadge label={agg.metric_label as any} className="mt-2" />
          </div>
        ))}

        {/* Declines / improvements */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <p className="text-xs text-gray-500">Patterns detected</p>
          <p className="text-sm font-semibold text-gray-900 mt-1">
            <span className="text-red-600">{profile.detected_patterns.declines.length} decline(s)</span>
            {' · '}
            <span className="text-green-600">{profile.detected_patterns.improvements.length} improvement(s)</span>
          </p>
          <MetricBadge label="CALCULATED" className="mt-2" />
        </div>
      </div>

      {/* Semester trend chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Semester Average Trend</h3>
            <MetricBadge label="CALCULATED" />
          </div>
          <SemesterTrendChart data={chartData} />
          <p className="text-xs text-gray-400 mt-2">
            Chart is for visual reference. Tabular data available in the timeline below.
          </p>
        </div>
      )}

      {/* Semester timeline */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">Semester Timeline</h3>
        {profile.timeline.length === 0 && (
          <p className="text-sm text-gray-400">No examination data available yet.</p>
        )}
        {profile.timeline.map((entry: TimelineEntry, idx) => {
          const isExpanded = expandedSem === entry.examination_id
          const m = entry.semester_metrics
          return (
            <div key={entry.examination_id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              {/* Semester header — always visible */}
              <button
                onClick={() => setExpandedSem(isExpanded ? null : entry.examination_id)}
                className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
                aria-expanded={isExpanded}
                aria-controls={`sem-${entry.examination_id}`}
              >
                <div className="flex items-center gap-4">
                  <span className="text-sm font-semibold text-gray-900">
                    {entry.academic_year} — {entry.examination_type}
                  </span>
                  <span className="text-sm text-gray-600 tabular-nums">
                    Avg: <strong>{m.average?.toFixed(2) ?? '—'}</strong>
                    <MetricBadge label={m.metric_label as any} className="ml-1" />
                  </span>
                  <span className="text-xs text-gray-500">
                    ✓ {m.subjects_passed} passed · ✗ {m.subjects_failed} failed
                  </span>
                  {entry.attention && (
                    <AttentionBadge
                      band={entry.attention.band as any}
                      score={entry.attention.score ?? undefined}
                      isPartial={entry.attention.is_partial ?? false}
                    />
                  )}
                </div>
                <span className="text-gray-400 text-sm" aria-hidden="true">
                  {isExpanded ? '▲' : '▼'}
                </span>
              </button>

              {/* Expanded subject details */}
              {isExpanded && (
                <div id={`sem-${entry.examination_id}`} className="border-t border-gray-100 px-5 pb-5 pt-3">
                  {/* Attention factors */}
                  {entry.attention && (
                    <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3">
                      <p className="text-xs font-semibold text-amber-800 mb-1">
                        Academic Attention Score: {entry.attention.score?.toFixed(1)} / 100
                        {entry.attention.is_partial && (
                          <span className="ml-2 text-amber-600">
                            * Partial score — factors {entry.attention.missing_factors?.join(', ')} not evaluated
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-amber-700">
                        Algorithm: {entry.attention.algorithm_version} ·{' '}
                        <MetricBadge label="ESTIMATED" />
                      </p>
                    </div>
                  )}

                  {/* Subject results table */}
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-xs" aria-label={`Subject results for ${entry.academic_year}`}>
                      <caption className="sr-only">
                        Subject results — {entry.academic_year}
                      </caption>
                      <thead className="border-b border-gray-100">
                        <tr>
                          {['Subject ID', 'Internal', 'External', 'Total', 'Grade', 'GP', 'Result', 'Attempt'].map(h => (
                            <th key={h} scope="col" className="px-3 py-2 text-left font-semibold text-gray-400 uppercase tracking-wider">
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {entry.subject_results.map((sr, si) => (
                          <tr key={si} className={sr.result_status === 'FAIL' ? 'bg-red-50' : sr.is_absent ? 'bg-gray-50' : ''}>
                            <td className="px-3 py-2 font-mono text-gray-500">{sr.subject_id.slice(0, 8)}…</td>
                            <td className="px-3 py-2 tabular-nums">{sr.internal_marks?.toFixed(1) ?? '—'}</td>
                            <td className="px-3 py-2 tabular-nums">{sr.external_marks?.toFixed(1) ?? '—'}</td>
                            <td className="px-3 py-2 tabular-nums font-semibold">
                              {sr.is_absent ? 'ABSENT' : sr.total_marks?.toFixed(1) ?? '—'}
                            </td>
                            <td className="px-3 py-2">{sr.grade ?? '—'}</td>
                            <td className="px-3 py-2 tabular-nums">{sr.grade_point?.toFixed(2) ?? '—'}</td>
                            <td className="px-3 py-2">
                              <span className={`font-medium ${sr.result_status === 'PASS' ? 'text-green-700' : sr.result_status === 'FAIL' ? 'text-red-700' : 'text-gray-500'}`}>
                                {sr.result_status}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-gray-400">{sr.attempt_number ?? 1}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="mt-2 text-xs text-gray-400">
                    All marks are <MetricBadge label="OFFICIAL" className="inline mx-1" /> — extracted directly from source documents.
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
