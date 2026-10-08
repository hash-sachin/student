/**
 * LoginPage — JWT authentication form.
 * WCAG 2.1 AA: labelled fields, error announced via role="alert", focus management.
 */
import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import type { AxiosError } from 'axios'

export default function LoginPage() {
  const { login, loading, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const emailRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard', { replace: true })
    emailRef.current?.focus()
  }, [isAuthenticated, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await login(email, password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      const ax = err as AxiosError<{ error?: { message?: string } }>
      const msg =
        ax.response?.data?.error?.message ||
        (ax.response?.status === 423 ? 'Account is locked. Please try later.' : 'Invalid email or password.')
      setError(msg)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-primary-700">AcademicIQ</h1>
          <p className="text-gray-500 text-sm mt-1">
            Evidence-Driven Academic Intelligence Platform
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Sign in</h2>

          {error && (
            <div
              role="alert"
              className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm"
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Email address
              </label>
              <input
                id="email"
                ref={emailRef}
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                aria-describedby={error ? 'login-error' : undefined}
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !email || !password}
              className="w-full py-2.5 px-4 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          AcademicIQ is decision support only. It never makes irreversible academic decisions.
        </p>
      </div>
    </div>
  )
}
