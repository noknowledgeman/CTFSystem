import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { leaderboard as leaderboardApi } from '../api/client'
import type { ProgressDetailed } from '../types'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts'

export default function Progress() {
  const { user } = useAuth()
  const [data, setData] = useState<ProgressDetailed | null>(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }
    leaderboardApi.myProgressDetailed()
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : 'Failed'))
      .finally(() => setLoading(false))
  }, [user])

  if (!user) {
    return <div className="app"><p>Log in to see your progress.</p></div>
  }

  if (loading) return <div className="app"><p>Loading…</p></div>
  if (err) return <div className="app"><p className="error">{err}</p></div>
  if (!data) return <div className="app"><p>No data.</p></div>

  const barData = data.by_category.map((c) => ({ name: c.category, points: c.points, solved: c.solved_count }))
  const lineData = data.points_over_time.length ? data.points_over_time : [{ date: '–', cumulative_points: 0 }]

  return (
    <div className="app">
      <h1>Your progress</h1>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Summary</h2>
        <p><strong>{data.username}</strong>{data.team_name && <> · Team: <strong>{data.team_name}</strong></>}</p>
        <p><strong>{data.total_points}</strong> points · <strong>{data.solved_count}</strong> challenges solved</p>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Points over time</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Cumulative score as you solve challenges.</p>
        <div style={{ width: '100%', height: 240 }}>
          <ResponsiveContainer>
            <LineChart data={lineData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }}
                labelStyle={{ color: 'var(--text)' }}
              />
              <Line type="monotone" dataKey="cumulative_points" stroke="var(--accent)" strokeWidth={2} dot={{ fill: 'var(--accent)' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Points by category</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Score breakdown by challenge category.</p>
        <div style={{ width: '100%', height: 260 }}>
          <ResponsiveContainer>
            <BarChart data={barData} layout="vertical" margin={{ top: 8, right: 24, left: 60, bottom: 8 }}>
              <XAxis type="number" stroke="var(--text-muted)" fontSize={12} />
              <YAxis type="category" dataKey="name" stroke="var(--text-muted)" fontSize={12} width={56} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }}
              />
              <Bar dataKey="points" fill="var(--accent)" name="Points" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        {barData.length === 0 && <p>Solve challenges to see breakdown by category.</p>}
      </div>
    </div>
  )
}
