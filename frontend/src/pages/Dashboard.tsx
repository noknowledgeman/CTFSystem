import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { challenges as challengesApi, leaderboard as leaderboardApi } from '../api/client'
import type { Challenge, LeaderboardEntry } from '../types'

export default function Dashboard() {
  const { user } = useAuth()
  const [challenges, setChallenges] = useState<Challenge[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [progress, setProgress] = useState<{ total_points: number; solved_count: number } | null>(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [c, lb] = await Promise.all([
          challengesApi.list(),
          leaderboardApi.get('user'),
        ])
        if (!cancelled) {
          setChallenges(c)
          setLeaderboard(lb)
        }
        if (user) {
          const p = await leaderboardApi.myProgress()
          if (!cancelled) setProgress(p)
        }
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : 'Failed to load')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [user])

  if (loading) return <div className="app"><p>Loading…</p></div>
  if (err) return <div className="app"><p className="error">{err}</p></div>

  return (
    <div className="app">
      <h1>CTF Dashboard</h1>
      {user && progress !== null && (
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Your progress</h2>
          <p><strong>{progress.total_points}</strong> points · <strong>{progress.solved_count}</strong> solved</p>
        </div>
      )}

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Leaderboard</h2>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Player</th>
              <th>Points</th>
              <th>Solved</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map((e) => (
              <tr key={e.user_id ?? e.team_id ?? e.rank}>
                <td>{e.rank}</td>
                <td>{e.username_or_team}</td>
                <td>{e.total_points}</td>
                <td>{e.solved_count}</td>
              </tr>
            ))}
            {leaderboard.length === 0 && (
              <tr><td colSpan={4}>No entries yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Challenges</h2>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Difficulty</th>
              <th>Points</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {challenges.map((c) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td><span className="badge">{c.category}</span></td>
                <td><span className={`badge ${c.difficulty}`}>{c.difficulty}</span></td>
                <td>{c.points}</td>
                <td>
                  {c.solved && <span className="badge solved">Solved</span>}
                  <Link to={`/challenge/${c.id}`} className="btn" style={{ marginLeft: 8 }}>Open</Link>
                </td>
              </tr>
            ))}
            {challenges.length === 0 && (
              <tr><td colSpan={5}>No challenges yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
