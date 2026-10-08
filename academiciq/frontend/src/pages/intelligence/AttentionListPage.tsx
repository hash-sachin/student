/**
 * AttentionListPage — students flagged for academic attention.
 * Shows: band, score, contributing factors. Label: ESTIMATED.
 * Non-stigmatizing language per spec Section 3.
 * Never shows "weak" or "bad" — uses "Academic Attention Required".
 */
import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { PageHeader } from '@/components/PageHeader'
import { AttentionBadge } from '@/components/AttentionBadge'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { EmptyState } from '@/components/EmptyState'
import { MetricBadge } from '@/components/MetricBadge'
import type { AttentionBand } from '@/types'
import { useQuery } from '@tanstack/react-query'
import { intelligenceApi } from '@/api/endpoints'

const BANDS: Array<{ value: AttentionBand | ''; label: string }> = [
  { value: '', label: 'All bands' },
  { value: 'HIGH_ATTENTION', label: 'High Attention Required' },
  { value: 'ATTENTION', label: 'Attention Required' },
  { value: 'MONITOR', label: 'Monitor' },
  { value: 'NORMAL', label: 'Normal' },
]

export default function AttentionListPage() {
  const [examinationId, setExaminationId] = useState('')
  const [selectedBand, setSelectedBand] = useState<AttentionBand | ''>('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['attention-list', examinationId, selectedBand],
    queryFn: () =>
      intelligenceApi.attention(examinationId, selectedBand || undefined).then(r => r.data),
    enabled: !!examinationId,
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Academic Attention"
        subtitle="Students who may benefit from academic support — all scores are ESTIMATED indicators"
      />

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-800">
        <p className="font-semibold mb-1">Important</p>
        <p>
          Academic Attention indicators are <MetricBadge label="ESTIMATED" className="mx-1" /> decision
          support tools. They are not official evaluations. All recommended interventions require
          faculty review and approval. No automatic action is taken on any student.
          Language used here follows a non-stigmatizing framework — "Academic Attention Required"
          means the student may benefit from academic support.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div>
          <label htmlFor="exam-id" className="block text-xs font-medium text-gray-500 mb-1">
            Examination ID
          </label>
          <input
            id="exam-id"
            type="text"
            placeholder="Paste examination UUID…"
            value={examinationId}
            onChange={e => setExaminationId(e.target.value.trim())}
            className="w-80 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono"
          />
        </div>
        <div>
          <label htmlFor="band-filter" className="block text-xs font-medium text-gray-500 mb-1">
            Filter by band
          </label>
          <select
            id="band-filter"
            value={selectedBand}
            onChange={e => setSelectedBand(e.target.value as AttentionBand | '')}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {BANDS.map(b => (
              <option key={b.value} value={b.value}>{b.label}</option>
            ))}
          </select>
        </div>
      </div>

      {!examinationId && (
        <EmptyState
          title="Enter an examination ID"
          description="Paste an examination UUID above to view attention indicators for that exam."
        />
      )}

      {isLoading && examinationId && <LoadingSpinner label="Computing attention scores…" />}

      {isError && (
        <div role="alert" className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          Could not load attention data. Check that the examination ID is valid.
        </div>
      )}

      {data && data.length === 0 && (
        <EmptyState
          title="No attention indicators for this examination"
          description="All students are in the NORMAL band, or scores have not been computed yet."
        />
      )}

      {data && data.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700">
              {data.length} student{data.length !== 1 ? 's' : ''} flagged
            </span>
            <MetricBadge label="ESTIMATED" />
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm" aria-label="Academic attention scores">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {['Student ID', 'Band', 'Score / 100', 'Partial?', 'Missing Factors', 'Algorithm', 'Actions'].map(h => (
                    <th key={h} scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map((s: any) => (
                  <tr key={s.student_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-600">{s.student_id.slice(0, 8)}…</td>
                    <td className="px-4 py-3">
                      <AttentionBadge band={s.band} score={s.raw_score} isPartial={s.is_partial_score} />
                    </td>
                    <td className="px-4 py-3 tabular-nums font-medium text-gray-900">
                      {s.raw_score.toFixed(1)}
                    </td>
                    <td className="px-4 py-3">
                      {s.is_partial_score ? (
                        <span className="text-yellow-700 text-xs" title="Some factors could not be evaluated due to insufficient history">
                          Partial *
                        </span>
                      ) : (
                        <span className="text-green-700 text-xs">Full</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">
                      {s.missing_factors?.join(', ') || '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400 font-mono">
                      {s.algorithm_version}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/students/${s.student_id}/profile`}
                        className="text-primary-600 hover:underline text-xs focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
                      >
                        View Profile
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
