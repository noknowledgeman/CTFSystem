import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const user = await login(username, password)
      if (user.role === 'admin') navigate('/admin')
      else navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <div className="card" style={{ maxWidth: 400, margin: '2rem auto' }}>
        <h1 style={{ marginTop: 0 }}>CTF Login</h1>
        <form onSubmit={handleSubmit}>
          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoComplete="username"
          />
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
          {error && <p className="error">{error}</p>}
          <div className="form-actions">
            <button type="submit" className="btn primary" disabled={loading}>
              {loading ? 'Logging in…' : 'Log in'}
            </button>
            <Link to="/register" className="btn">Register</Link>
          </div>
        </form>
      </div>
    </div>
  )
}
