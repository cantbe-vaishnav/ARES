import React, { useState } from 'react'
import { api, setToken } from '../api'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await api('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
      setToken(data.access_token)
      onLogin(data.user)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return <div className="login-shell">
    <form className="login-card" onSubmit={submit}>
      <div className="brand-mark">A</div>
      <h1>ARES</h1>
      <p>AI Retrieval Engine System</p>
      <input autoFocus placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
      <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      {error && <div className="error">{error}</div>}
      <button disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
    </form>
  </div>
}
