import { useEffect, useState } from 'react'
import { submissions as submissionsApi, challenges as challengesApi } from '../../api/client'
import type { Submission } from '../../types'
import type { Challenge } from '../../types'

export default function AdminSubmissions() {
  const [list, setList] = useState<Submission[]>([])
  const [challenges, setChallenges] = useState<Challenge[]>([])
  const [loading, setLoading] = useState(true)
  const [grading, setGrading] = useState<number | null>(null)
  const [feedback, setFeedback] = useState('')
  const [points, setPoints] = useState('')

  function load() {
    Promise.all([submissionsApi.all(), challengesApi.list()])
      .then(([subs, ch]) => {
        setList(subs)
        setChallenges(ch)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function handleGrade(sub: Submission, status: 'accepted' | 'rejected') {
    setGrading(sub.id)
    try {
      await submissionsApi.grade(sub.id, {
        status,
        assigned_points: status === 'accepted' ? (points ? Number(points) : undefined) : undefined,
        feedback: feedback || undefined,
      })
      setFeedback('')
      setPoints('')
      setGrading(null)
      load()
    } catch {
      setGrading(null)
    }
  }

  const challengeMap = Object.fromEntries(challenges.map((c) => [c.id, c]))

  if (loading) return <p>Loading…</p>

  return (
    <div className="card">
      <h1 style={{ marginTop: 0 }}>Submissions</h1>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Challenge</th>
            <th>User/Team</th>
            <th>Correct</th>
            <th>Status</th>
            <th>Points</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {list.map((sub) => (
            <tr key={sub.id}>
              <td>{sub.id}</td>
              <td>{challengeMap[sub.challenge_id]?.name ?? sub.challenge_id}</td>
              <td>{sub.user_id ?? `team ${sub.team_id}`}</td>
              <td>{sub.correct ? 'Yes' : 'No'}</td>
              <td>{sub.status}</td>
              <td>{sub.assigned_points ?? '–'}</td>
              <td>{new Date(sub.created_at).toLocaleString()}</td>
              <td>
                {sub.status === 'pending' && (
                  <>
                    <input type="number" placeholder="Points" value={grading === sub.id ? points : ''} onChange={(e) => setPoints(e.target.value)} style={{ width: 60, marginRight: 4 }} />
                    <input type="text" placeholder="Feedback" value={grading === sub.id ? feedback : ''} onChange={(e) => setFeedback(e.target.value)} style={{ width: 100, marginRight: 4 }} />
                    <button type="button" className="btn primary" onClick={() => handleGrade(sub, 'accepted')} disabled={grading !== null}>Accept</button>
                    <button type="button" className="btn danger" onClick={() => handleGrade(sub, 'rejected')} disabled={grading !== null}>Reject</button>
                  </>
                )}
              </td>
            </tr>
          ))}
          {list.length === 0 && <tr><td colSpan={8}>No submissions.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
