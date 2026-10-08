/**
 * Axios API client with JWT interceptor and error handling.
 */
import axios, { type AxiosError } from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---------------------------------------------------------------------------
// Request interceptor — attach access token
// ---------------------------------------------------------------------------
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ---------------------------------------------------------------------------
// Response interceptor — auto-refresh on 401
// ---------------------------------------------------------------------------
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as any
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          localStorage.setItem('access_token', data.access_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return apiClient(original)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  },
)
