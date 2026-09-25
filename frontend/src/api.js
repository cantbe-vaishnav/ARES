const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function getToken() {
  return localStorage.getItem('ares_token') || ''
}

export function setToken(token) {
  if (token) localStorage.setItem('ares_token', token)
  else localStorage.removeItem('ares_token')
}

export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {})
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(`${API_URL}${path}`, { ...options, headers })
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new Error(data?.detail || `Request failed (${res.status})`)
  return data
}
