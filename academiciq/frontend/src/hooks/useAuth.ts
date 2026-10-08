/**
 * useAuth — authentication state and actions.
 * Stores tokens in localStorage; attaches to axios interceptor via api/client.ts.
 */
import { useState, useCallback, useEffect } from 'react'
import { authApi } from '@/api/endpoints'
import type { TokenResponse } from '@/types'

interface AuthState {
  isAuthenticated: boolean
  userId: string | null
  role: string | null
  loading: boolean
}

function decodePayload(token: string): Record<string, unknown> {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64))
  } catch {
    return {}
  }
}

function getInitialState(): AuthState {
  const token = localStorage.getItem('access_token')
  if (!token) return { isAuthenticated: false, userId: null, role: null, loading: false }
  const payload = decodePayload(token)
  const exp = payload.exp as number | undefined
  if (exp && exp * 1000 < Date.now()) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    return { isAuthenticated: false, userId: null, role: null, loading: false }
  }
  return {
    isAuthenticated: true,
    userId: payload.sub as string,
    role: payload.role as string,
    loading: false,
  }
}

export function useAuth() {
  const [state, setState] = useState<AuthState>(getInitialState)

  const login = useCallback(async (email: string, password: string) => {
    setState(s => ({ ...s, loading: true }))
    try {
      const { data } = await authApi.login({ email, password })
      localStorage.setItem('access_token', data.access_token)
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token)
      }
      const payload = decodePayload(data.access_token)
      setState({
        isAuthenticated: true,
        userId: payload.sub as string,
        role: payload.role as string,
        loading: false,
      })
    } catch (err) {
      setState(s => ({ ...s, loading: false }))
      throw err
    }
  }, [])

  const logout = useCallback(async () => {
    try { await authApi.logout() } catch { /* ignore */ }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setState({ isAuthenticated: false, userId: null, role: null, loading: false })
  }, [])

  return { ...state, login, logout }
}
