import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { teams as teamsApi, leaderboard as leaderboardApi } from '../api/client'
import type { TeamRead } from '../api/client'
import type { LeaderboardEntry } from '../types'

export default function Teams() {
  const { user, updateUser } = useAuth()
  const [teamList, setTeamList] = useState<TeamRead[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [joining, setJoining] = useState<number | null>(null)
  const [leaving, setLeaving] = useState(false)
  const [err, setErr] = useState('')

  function load() {
    if (!user) return
    Promise.all([teamsApi.list(), leaderboardApi.get('team')])
      .then(([teams, lb]) => {
        setTeamList(teams)
        setLeaderboard(lb)
      })
      .catch((e) => setErr(e instanceof Error ? e.message : 'Failed'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [user])

  async function handleJoin(teamId: number) {
    setErr('')
    setJoining(teamId)
    try {
      const res = await teamsApi.join(teamId)
      updateUser(res.user)
      load()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Join failed')
    } finally {
      setJoining(null)
    }
  }

  async function handleLeave() {
    setErr('')
    setLeaving(true)
    try {
      const res = await teamsApi.leave()
      updateUser(res.user)
      load()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Leave failed')
    } finally {
      setLeaving(false)
    }
  }

  if (!user) {
    return <div className="app"><p>Log in to view and join teams.</p></div>
  }

  const myTeamRank = user.team_id ? leaderboard.find((e) => e.team_id === user.team_id) : null
  const myTeam = user.team_id ? teamList.find((t) => t.id === user.team_id) : null

  if (loading) return <div className="app"><p>Loading…</p></div>

  return (
    <div className="app">
      <h1>Teams</h1>
      {err && <p className="error">{err}</p>}
      {myTeam && (
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Your team</h2>
          <p><strong>{myTeam.name}</strong></p>
          {myTeamRank && (
            <p>Rank: {myTeamRank.rank} · {myTeamRank.total_points} pts · {myTeamRank.solved_count} solved</p>
          )}
          <button type="button" className="btn danger" onClick={handleLeave} disabled={leaving}>
            {leaving ? 'Leaving…' : 'Leave team'}
          </button>
        </div>
      )}
      <div className="card">
        <h2 style={{ marginTop: 0 }}>All teams</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Join a team to compete together. Your submissions will count toward the team score.
        </p>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Rank</th>
              <th>Points</th>
              <th>Solved</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {teamList.map((t) => {
              const entry = leaderboard.find((e) => e.team_id === t.id)
              const isMyTeam = user.team_id === t.id
              return (
                <tr key={t.id}>
                  <td>{t.name}</td>
                  <td>{entry ? entry.rank : '–'}</td>
                  <td>{entry ? entry.total_points : 0}</td>
                  <td>{entry ? entry.solved_count : 0}</td>
                  <td>
                    {isMyTeam ? (
                      <span className="badge solved">Your team</span>
                    ) : (
                      <button
                        type="button"
                        className="btn primary"
                        disabled={joining !== null}
                        onClick={() => handleJoin(t.id)}
                      >
                        {joining === t.id ? 'Joining…' : 'Join'}
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
            {teamList.length === 0 && <tr><td colSpan={5}>No teams yet. Admins can create teams.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
