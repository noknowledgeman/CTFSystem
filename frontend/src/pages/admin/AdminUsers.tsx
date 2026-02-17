import { useEffect, useState } from 'react'
import { admin } from '../../api/client'
import type { User } from '../../types'

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState<number | null>(null)

  function load() {
    admin.users().then(setUsers).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function toggleActive(u: User) {
    const next = !(u.is_active !== false)
    setToggling(u.id)
    try {
      await admin.updateUser(u.id, { is_active: next })
      setUsers((prev) => prev.map((x) => (x.id === u.id ? { ...x, is_active: next } : x)))
    } finally {
      setToggling(null)
    }
  }

  if (loading) return <p>Loading…</p>

  return (
    <div className="card">
      <h1 style={{ marginTop: 0 }}>Users</h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        Disabled users cannot log in. They are excluded from the leaderboard.
      </p>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.id}</td>
              <td>{u.username}</td>
              <td>{u.email}</td>
              <td>{u.role}</td>
              <td>
                <span className={u.is_active !== false ? 'badge solved' : 'badge'}>
                  {u.is_active !== false ? 'Active' : 'Disabled'}
                </span>
              </td>
              <td>
                <button
                  type="button"
                  className={u.is_active !== false ? 'btn danger' : 'btn primary'}
                  disabled={toggling !== null}
                  onClick={() => toggleActive(u)}
                >
                  {toggling === u.id ? '…' : u.is_active !== false ? 'Disable' : 'Enable'}
                </button>
              </td>
            </tr>
          ))}
          {users.length === 0 && <tr><td colSpan={6}>No users.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
