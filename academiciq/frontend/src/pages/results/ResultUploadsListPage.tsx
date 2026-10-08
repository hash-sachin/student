/**
 * ResultUploadsListPage — history of all result PDF uploads with status.
 */
import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { resultsApi } from '@/api/endpoints'
import { PageHeader } from '@/components/PageHeader'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { EmptyState } from '@/components/EmptyState'
import type { ResultUpload, UploadStatus } from '@/types'

const STATUS_STYLE: Record<UploadStatus, string> = {
  QUEUED:           'bg-gray-100 text-gray-600',
  PROCESSING:       'bg-blue-100 text-blue-700',
  VALIDATION:       'bg-yellow-100 text-yellow-700',
  READY_FOR_REVIEW: 'bg-purple-100 text-purple-700',
  COMMITTED:        'bg-green-100 text-green-700',
  REJECTED:         'bg-red-100 text-red-700',
  FAILED:           'bg-red-200 text-red-800',
}

export default function ResultUploadsListPage() {
  const { data: uploads, isLoading, isError, refetch } = useQuery({
    queryKey: ['uploads'],
    queryFn: () => resultsApi.listUploads().then(r => r.data),
    refetchInterval: 5000, // Poll every 5 s while processing
  })

  return (
    <div>
      <PageHeader
        title="Upload History"
        subtitle="All result PDF uploads and their processing status"
        actions={
          <Link
            to="/results/upload"
            className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            + New Upload
          </Link>
        }
      />

      {isLoading && <LoadingSpinner label="Loading uploads…" />}
      {isError && <ErrorMessage retry={refetch} />}

      {uploads && uploads.length === 0 && (
        <EmptyState
          title="No uploads yet"
          description="Upload a result PDF to get started."
          action={
            <Link to="/results/upload" className="text-primary-600 underline text-sm">
              Upload now
            </Link>
          }
        />
      )}

      {uploads && uploads.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm" aria-label="Upload history table">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {['File', 'Status', 'Records', 'Valid', 'Warnings', 'Errors', 'Parser', 'Uploaded', 'Actions'].map(h => (
                    <th key={h} scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {uploads.map((u: ResultUpload) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 max-w-xs truncate text-gray-700" title={u.file_name}>
                      {u.file_name}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLE[u.processing_status]}`}>
                        {u.processing_status}
                      </span>
                    </td>
                    <td className="px-4 py-3 tabular-nums text-gray-600">{u.record_count ?? '—'}</td>
                    <td className="px-4 py-3 tabular-nums text-green-700">{u.valid_count ?? '—'}</td>
                    <td className="px-4 py-3 tabular-nums text-yellow-700">{u.warning_count ?? '—'}</td>
                    <td className="px-4 py-3 tabular-nums text-red-700">{u.error_count ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {u.parser_name ?? '—'}
                      {u.parser_confidence != null && (
                        <span className="ml-1 text-gray-400">
                          ({(u.parser_confidence * 100).toFixed(0)}%)
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/results/uploads/${u.id}`}
                        className="text-primary-600 hover:underline text-xs focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
                      >
                        Details
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
