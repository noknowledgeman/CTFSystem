import { useEffect, useState } from 'react'
import { admin } from '../../api/client'
import type { EventStats } from '../../types'

export default function AdminStats() {
  const [stats, setStats] = useState<EventStats | null>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    admin.stats()
      .then(setStats)
      .catch((e) => setErr(e instanceof Error ? e.message : 'Failed'))
  }, [])

  if (err) return <p className="error">{err}</p>
  if (!stats) return <p>Loading…</p>

  return (
    <div className="card">
      <h1 style={{ marginTop: 0 }}>Event stats</h1>
      <table style={{ maxWidth: 400 }}>
        <tbody>
          <tr><td>Total submissions</td><td><strong>{stats.total_submissions}</strong></td></tr>
          <tr><td>Correct submissions</td><td><strong>{stats.correct_submissions}</strong></td></tr>
          <tr><td>Unique solvers</td><td><strong>{stats.unique_solvers}</strong></td></tr>
          <tr><td>Challenges</td><td><strong>{stats.challenges_count}</strong></td></tr>
        </tbody>
      </table>
    </div>
  )
}
