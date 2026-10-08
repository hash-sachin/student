/**
 * AcademicIQ — Main application router.
 */
import React, { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from '@/layouts/MainLayout'
import { useAuth } from '@/hooks/useAuth'

// Lazy-loaded pages
const LoginPage = lazy(() => import('@/pages/LoginPage'))
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const StudentsListPage = lazy(() => import('@/pages/students/StudentsListPage'))
const StudentProfilePage = lazy(() => import('@/pages/students/StudentProfilePage'))
const LongitudinalProfilePage = lazy(() => import('@/pages/students/LongitudinalProfilePage'))
const ResultUploadPage = lazy(() => import('@/pages/results/ResultUploadPage'))
const ResultUploadsListPage = lazy(() => import('@/pages/results/ResultUploadsListPage'))
const UploadDetailPage = lazy(() => import('@/pages/results/UploadDetailPage'))
const AttentionListPage = lazy(() => import('@/pages/intelligence/AttentionListPage'))
const WhatIfPage = lazy(() => import('@/pages/simulation/WhatIfPage'))
const AIInsightsPage = lazy(() => import('@/pages/ai/AIInsightsPage'))

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function LoadingFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center" aria-label="Loading">
      <div className="animate-pulse text-gray-500">Loading AcademicIQ…</div>
    </div>
  )
}

export default function App() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />

          {/* Students */}
          <Route path="students" element={<StudentsListPage />} />
          <Route path="students/:id" element={<StudentProfilePage />} />
          <Route path="students/:id/profile" element={<LongitudinalProfilePage />} />

          {/* Results */}
          <Route path="results/upload" element={<ResultUploadPage />} />
          <Route path="results/uploads" element={<ResultUploadsListPage />} />
          <Route path="results/uploads/:id" element={<UploadDetailPage />} />

          {/* Intelligence */}
          <Route path="intelligence/attention" element={<AttentionListPage />} />

          {/* Simulation */}
          <Route path="simulation/what-if" element={<WhatIfPage />} />

          {/* AI */}
          <Route path="ai/insights" element={<AIInsightsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  )
}
