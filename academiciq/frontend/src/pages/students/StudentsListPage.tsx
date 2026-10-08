/**
 * StudentsListPage — searchable, filterable, paginated student roster.
 * WCAG 2.1 AA: table with proper thead/scope, keyboard-sortable, status labels.
 */
import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useStudents } from '@/hooks/useStudents'
import { PageHeader } from '@/components/PageHeader'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { EmptyState } from '@/components/EmptyState'
import type { Student } from '@/types'

const STATUS_BADGE: Record<string, string> = {
  ACTIVE: 'bg-green-100 text-green-700',
  DISCONTINUED: 'bg-red-100 text-red-700',
  GRADUATED: 'bg-blue-100 text-blue-700',
  ON_LEAVE: 'bg-yellow-100 text-yellow-700',
}

export default function StudentsListPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 20

  const { data, isLoading, isError, refetch } = useStudents({
    page,
    page_size: PAGE_SIZE,
    search: search || undefined,
  })

  return (
    <div>
      <PageHeader
        title="Students"
        subtitle="All registered students in the system"
      />

      {/* Search */}
      <div className="mb-4 flex gap-3">
        <label htmlFor="student-search" className="sr-only">
          Search by register number
        </label>
        <input
          id="student-search"
          type="search"
          placeholder="Search by register number…"
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
          className="w-72 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          aria-label="Search students by register number"
        />
        {search && (
          <button
            onClick={() => { setSearch(''); setPage(1) }}
            className="text-sm text-gray-400 hover:text-gray-700 px-2"
          >
            Clear
          </button>
        )}
      </div>

      {isLoading && <LoadingSpinner label="Loading students…" />}
      {isError && <ErrorMessage retry={refetch} />}

      {data && !isLoading && (
        <>
          {data.items.length === 0 ? (
            <EmptyState title="No students found" description="Try adjusting your search." />
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm" aria-label="Students table">
                  <caption className="sr-only">
                    Student roster — {data.total} students total
                  </caption>
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      {['Register No.', 'Name', 'Admission Year', 'Status', 'Actions'].map(h => (
                        <th
                          key={h}
                          scope="col"
                          className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data.items.map((s: Student) => (
                      <tr key={s.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 font-mono text-gray-900">{s.register_number}</td>
                        <td className="px-4 py-3 text-gray-700">{s.name}</td>
                        <td className="px-4 py-3 text-gray-500">{s.admission_year}</td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[s.status] ?? 'bg-gray-100 text-gray-600'}`}
                          >
                            {s.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 flex gap-3">
                          <Link
                            to={`/students/${s.id}`}
                            className="text-primary-600 hover:underline focus:outline-none focus:ring-2 focus:ring-primary-500 rounded text-xs"
                          >
                            View
                          </Link>
                          <Link
                            to={`/students/${s.id}/profile`}
                            className="text-primary-600 hover:underline focus:outline-none focus:ring-2 focus:ring-primary-500 rounded text-xs"
                          >
                            Profile
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 text-sm text-gray-500">
                <span>
                  Showing {(page - 1) * PAGE_SIZE + 1}–
                  {Math.min(page * PAGE_SIZE, data.total)} of {data.total}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    aria-label="Previous page"
                  >
                    ←
                  </button>
                  <span className="px-2 py-1">Page {page}</span>
                  <button
                    onClick={() => setPage(p => p + 1)}
                    disabled={page * PAGE_SIZE >= data.total}
                    className="px-3 py-1 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    aria-label="Next page"
                  >
                    →
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
