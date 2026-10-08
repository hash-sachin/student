/**
 * MainLayout — sidebar navigation + content area.
 * WCAG 2.1 AA: skip-to-content link, landmark roles, keyboard navigation.
 */
import React, { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import clsx from 'clsx'

const NAV_SECTIONS = [
  {
    title: 'Overview',
    items: [
      { label: 'Dashboard', href: '/dashboard', icon: '⊞' },
    ],
  },
  {
    title: 'Students',
    items: [
      { label: 'All Students', href: '/students', icon: '👤' },
    ],
  },
  {
    title: 'Results',
    items: [
      { label: 'Upload Results', href: '/results/upload', icon: '↑' },
      { label: 'Upload History', href: '/results/uploads', icon: '📄' },
    ],
  },
  {
    title: 'Academic Intelligence',
    items: [
      { label: 'Academic Attention', href: '/intelligence/attention', icon: '⚑' },
    ],
  },
  {
    title: 'Simulation',
    items: [
      { label: 'What-If Simulator', href: '/simulation/what-if', icon: '◇' },
    ],
  },
  {
    title: 'AI',
    items: [
      { label: 'AI Insights', href: '/ai/insights', icon: '✦' },
    ],
  },
]

export function MainLayout() {
  const { role, logout } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Skip to content — WCAG 2.1 AA */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded"
      >
        Skip to main content
      </a>

      {/* Sidebar */}
      <nav
        aria-label="Main navigation"
        className={clsx(
          'bg-white border-r border-gray-200 flex flex-col transition-all duration-200',
          sidebarOpen ? 'w-60' : 'w-16',
        )}
      >
        {/* Logo */}
        <div className="h-14 flex items-center px-4 border-b border-gray-100 shrink-0">
          {sidebarOpen ? (
            <span className="font-bold text-primary-700 text-lg tracking-tight">
              AcademicIQ
            </span>
          ) : (
            <span className="font-bold text-primary-700 text-lg">A</span>
          )}
          <button
            onClick={() => setSidebarOpen(o => !o)}
            className="ml-auto text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {sidebarOpen ? '←' : '→'}
          </button>
        </div>

        {/* Nav items */}
        <div className="flex-1 overflow-y-auto py-4 space-y-1">
          {NAV_SECTIONS.map(section => (
            <div key={section.title}>
              {sidebarOpen && (
                <p className="px-4 pt-3 pb-1 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  {section.title}
                </p>
              )}
              {section.items.map(item => (
                <NavLink
                  key={item.href}
                  to={item.href}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-3 px-4 py-2 text-sm rounded-md mx-2 transition-colors',
                      isActive
                        ? 'bg-primary-50 text-primary-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                    )
                  }
                  title={!sidebarOpen ? item.label : undefined}
                >
                  <span aria-hidden="true" className="text-base w-5 text-center shrink-0">
                    {item.icon}
                  </span>
                  {sidebarOpen && <span>{item.label}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-100 shrink-0">
          {sidebarOpen && (
            <p className="text-xs text-gray-400 mb-2 truncate">Role: {role}</p>
          )}
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <span aria-hidden="true">⎋</span>
            {sidebarOpen && 'Sign out'}
          </button>
        </div>
      </nav>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-14 bg-white border-b border-gray-200 flex items-center px-6 shrink-0">
          <h1 className="text-sm font-medium text-gray-500">
            AcademicIQ — Evidence-Driven Academic Intelligence Platform
          </h1>
        </header>

        {/* Page content */}
        <main id="main-content" className="flex-1 overflow-auto p-6" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
