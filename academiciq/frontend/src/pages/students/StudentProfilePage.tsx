/**
 * StudentProfilePage — basic student info + navigation to longitudinal profile.
 */
import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { useStudent } from '@/hooks/useStudents'
import { PageHeader } from '@/components/PageHeader'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { MetricBadge } from '@/components/MetricBadge'

export default function StudentProfilePage() {
  const { id } = useParams<{ id: string }>()
  const { data: student, isLoading, isError, refetch } = useStudent(id!)

  if (isLoading) return <LoadingSpinner label="Loading student…" />
  if (isError || !student) return <ErrorMessage retry={refetch} />

  return (
    <div className="space-y-6">
      <PageHeader
        title={student.name}
        subtitle={`Register No. ${student.register_number}`}
        actions={
          <Link
            to={`/students/${id}/profile`}
            className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            View Longitudinal Profile
          </Link>
        }
      />

      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-sm font-semibold text-gray-700">Student Details</h3>
          <MetricBadge label="OFFICIAL" />
        </div>
        <dl className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          {[
            ['Register Number', student.register_number],
            ['University Reg. No.', student.university_register_number ?? '—'],
            ['Admission Year', String(student.admission_year)],
            ['Status', student.status],
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-gray-500">{label}</dt>
              <dd className="font-medium text-gray-900 mt-0.5">{value}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
        <p className="font-medium mb-1">About the Longitudinal Academic Profile</p>
        <p className="text-xs text-blue-700">
          The Longitudinal Academic Profile is a structured representation of this
          student's academic history over time. It includes semester results, subject
          performance, detected patterns (decline/improvement), and academic attention
          indicators. "Academic Digital Twin" is a secondary alias (ADR-003).
        </p>
      </div>
    </div>
  )
}
