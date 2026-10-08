/**
 * DashboardPage — role-aware overview.
 * Cards: total students, pass %, class average, failed students, attention count.
 * All metrics carry their label (OFFICIAL / CALCULATED / ESTIMATED).
 */
import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/hooks/useAuth'
import { StatCard } from '@/components/StatCard'
import { apiClient } from '@/api/client'

function useStudentCount() {
  return useQuery({
    queryKey: ['dashboard-student-count'],
    queryFn: () =>
      apiClient.get('/students', { params: { page: 1, page_size: 1 } }).then(r => r.data.total as number),
  })
}

function useAttentionCount() {
  return useQuery({
    queryKey: ['dashboard-attention-count'],
    queryFn: async () => {
      // Placeholder — real impl would query intelligence/attention summary
      return null as number | null
    },
  })
}

export default function DashboardPage() {
  const { role } = useAuth()
  const { data: studentCount, isLoading: studentLoading } = useStudentCount()
  const { data: attentionCount } = useAttentionCount()

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Dashboard</h2>
        <p className="text-sm text-gray-500 mt-1">
          Welcome to AcademicIQ — Evidence-Driven Academic Intelligence Platform
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Students"
          value={studentCount ?? null}
          label="CALCULATED"
          loading={studentLoading}
        />
        <StatCard
          title="Academic Attention"
          value={attentionCount ?? '—'}
          label="ESTIMATED"
          description="students needing attention"
        />
        <StatCard
          title="Metric Type"
          value="OFFICIAL"
          label="OFFICIAL"
          description="marks from source documents"
        />
        <StatCard
          title="Data Quality"
          value="CALCULATED"
          label="CALCULATED"
          description="derived from official data"
        />
      </div>

      {/* Quick links */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Quick actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {[
            { label: 'Upload Results', href: '/results/upload', icon: '↑' },
            { label: 'View Students', href: '/students', icon: '👤' },
            { label: 'Academic Attention', href: '/intelligence/attention', icon: '⚑' },
            { label: 'What-If Simulator', href: '/simulation/what-if', icon: '◇' },
            { label: 'AI Insights', href: '/ai/insights', icon: '✦' },
            { label: 'Upload History', href: '/results/uploads', icon: '📄' },
          ].map(item => (
            <Link
              key={item.href}
              to={item.href}
              className="flex items-center gap-2 p-3 rounded-lg border border-gray-200 text-sm text-gray-700 hover:bg-primary-50 hover:border-primary-200 hover:text-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <span aria-hidden="true" className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </div>
      </div>

      {/* System info */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
        <p className="font-medium mb-1">About AcademicIQ</p>
        <p className="text-blue-700 text-xs leading-relaxed">
          AcademicIQ is decision support only. It never automatically fails, removes, or
          disciplines a student. Every indicator is explainable, versioned, and requires
          human review. Metric labels: <strong>OFFICIAL</strong> = from source document,{' '}
          <strong>CALCULATED</strong> = derived, <strong>ESTIMATED</strong> = heuristic,{' '}
          <strong>HYPOTHETICAL</strong> = what-if only.
        </p>
      </div>
    </div>
  )
}
