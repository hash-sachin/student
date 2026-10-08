/**
 * UploadDetailPage — validation preview, admin fix/skip/commit workflow.
 * Shows: total, valid, warning, error, unmatched counts.
 * Admin can fix records, skip with reason, or commit valid ones.
 */
import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { resultsApi } from '@/api/endpoints'
import { PageHeader } from '@/components/PageHeader'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { MetricBadge } from '@/components/MetricBadge'

const VALIDATION_BADGE: Record<string, string> = {
  VALID:     'bg-green-100 text-green-700',
  WARNING:   'bg-yellow-100 text-yellow-700',
  ERROR:     'bg-red-100 text-red-700',
  UNMATCHED: 'bg-orange-100 text-orange-700',
  DUPLICATE: 'bg-purple-100 text-purple-700',
  SKIPPED:   'bg-gray-100 text-gray-500',
}

export default function UploadDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [committing, setCommitting] = useState(false)
  const [commitResult, setCommitResult] = useState<{ committed_count: number; skipped_count: number } | null>(null)

  const { data: upload, isLoading: uploadLoading } = useQuery({
    queryKey: ['upload', id],
    queryFn: () => resultsApi.getUpload(id!).then(r => r.data),
    refetchInterval: (data: any) =>
      data?.processing_status === 'READY_FOR_REVIEW' || data?.processing_status === 'COMMITTED'
        ? false
        : 3000,
  })

  const { data: validation, isLoading: valLoading } = useQuery({
    queryKey: ['upload-validation', id],
    queryFn: () => resultsApi.getValidation(id!).then(r => r.data),
    enabled: upload?.processing_status === 'READY_FOR_REVIEW',
  })

  const handleCommit = async () => {
    if (!id) return
    setCommitting(true)
    try {
      const { data } = await resultsApi.commit(id)
      setCommitResult(data)
      qc.invalidateQueries({ queryKey: ['upload', id] })
    } catch (err: any) {
      alert(err?.response?.data?.error?.message ?? 'Commit failed.')
    } finally {
      setCommitting(false)
    }
  }

  if (uploadLoading) return <LoadingSpinner label="Loading upload…" />
  if (!upload) return <ErrorMessage />

  return (
    <div className="space-y-6">
      <PageHeader
        title={upload.file_name}
        subtitle={`Upload ID: ${upload.id}`}
      />

      {/* Status card */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-sm font-medium text-gray-600">Processing Status:</span>
          <span className="font-semibold text-gray-900">{upload.processing_status}</span>
          {upload.parser_name && (
            <span className="text-xs text-gray-400">
              Parser: {upload.parser_name} v{upload.parser_version}
              {upload.parser_confidence != null && ` (${(upload.parser_confidence * 100).toFixed(0)}% confidence)`}
            </span>
          )}
        </div>

        {/* Processing states */}
        {['QUEUED', 'PROCESSING', 'VALIDATION'].includes(upload.processing_status) && (
          <div className="mt-3 flex items-center gap-2 text-sm text-blue-600">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Processing in background… page will refresh automatically.
          </div>
        )}
      </div>

      {/* Commit success */}
      {commitResult && (
        <div role="alert" className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-green-800">
          <p className="font-semibold">✓ Committed successfully</p>
          <p>Records committed: <strong>{commitResult.committed_count}</strong></p>
          <p>Records skipped: <strong>{commitResult.skipped_count}</strong></p>
        </div>
      )}

      {/* Validation preview */}
      {validation && (
        <div className="space-y-4">
          {/* Summary counts */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            {[
              { label: 'Total', value: validation.total, cls: 'text-gray-900' },
              { label: 'Valid', value: validation.valid, cls: 'text-green-700' },
              { label: 'Warnings', value: validation.warning, cls: 'text-yellow-700' },
              { label: 'Errors', value: validation.error, cls: 'text-red-700' },
              { label: 'Unmatched', value: validation.unmatched, cls: 'text-orange-700' },
              { label: 'Duplicates', value: validation.duplicate, cls: 'text-purple-700' },
            ].map(item => (
              <div key={item.label} className="bg-white rounded-lg border border-gray-200 p-3 text-center shadow-sm">
                <p className={`text-xl font-bold tabular-nums ${item.cls}`}>{item.value}</p>
                <p className="text-xs text-gray-500 mt-0.5">{item.label}</p>
              </div>
            ))}
          </div>

          {/* Records table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
              <h3 className="text-sm font-semibold text-gray-700">Extracted Records</h3>
              <MetricBadge label="OFFICIAL" />
              <span className="text-xs text-gray-400">(marks are OFFICIAL — from source document)</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs" aria-label="Validation records">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    {['Register No.', 'Subject Code', 'Internal', 'External', 'Total', 'Grade', 'Status', 'Confidence', 'Validation', 'Notes'].map(h => (
                      <th key={h} scope="col" className="px-3 py-2 text-left font-semibold text-gray-500 uppercase tracking-wide">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {validation.records.map((rec: any) => (
                    <tr key={rec.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-mono">{rec.raw_register_number ?? '—'}</td>
                      <td className="px-3 py-2 font-mono">{rec.raw_subject_code ?? '—'}</td>
                      <td className="px-3 py-2 tabular-nums">{rec.raw_internal_marks ?? '—'}</td>
                      <td className="px-3 py-2 tabular-nums">{rec.raw_external_marks ?? '—'}</td>
                      <td className="px-3 py-2 tabular-nums font-medium">{rec.raw_total_marks ?? '—'}</td>
                      <td className="px-3 py-2">{rec.raw_grade ?? '—'}</td>
                      <td className="px-3 py-2">{rec.raw_result_status ?? '—'}</td>
                      <td className="px-3 py-2 tabular-nums text-gray-400">
                        {rec.confidence_score != null ? `${(rec.confidence_score * 100).toFixed(0)}%` : '—'}
                      </td>
                      <td className="px-3 py-2">
                        <span className={`inline-flex px-1.5 py-0.5 rounded text-xs font-medium ${VALIDATION_BADGE[rec.validation_status] ?? 'bg-gray-100 text-gray-600'}`}>
                          {rec.validation_status}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-gray-400 max-w-xs truncate" title={rec.validation_notes ?? ''}>
                        {rec.validation_notes ?? ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Commit / Reject actions */}
          {upload.processing_status === 'READY_FOR_REVIEW' && !commitResult && (
            <div className="flex gap-3 items-center">
              <button
                onClick={handleCommit}
                disabled={committing || validation.valid === 0}
                className="px-5 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {committing ? 'Committing…' : `Commit ${validation.valid} valid records`}
              </button>
              <button
                onClick={() => resultsApi.reject(id!).then(() => qc.invalidateQueries({ queryKey: ['upload', id] }))}
                className="px-5 py-2 border border-red-300 text-red-600 text-sm rounded-lg hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                Reject upload
              </button>
              <p className="text-xs text-gray-400">
                Skipped/rejected records are stored with reason — no data is lost.
              </p>
            </div>
          )}
        </div>
      )}

      {valLoading && <LoadingSpinner label="Loading validation data…" />}
    </div>
  )
}
