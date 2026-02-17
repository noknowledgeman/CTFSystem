import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { challenges as challengesApi, hints as hintsApi, submissions as submissionsApi } from '../api/client'
import type { Challenge, Hint } from '../types'

export default function ChallengeDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [challenge, setChallenge] = useState<Challenge | null>(null)
  const [hints, setHints] = useState<Hint[]>([])
  const [flag, setFlag] = useState('')
  const [message, setMessage] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [unlocking, setUnlocking] = useState(false)
  const [hintError, setHintError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    async function load() {
      try {
        const [c, h] = await Promise.all([
          challengesApi.get(Number(id)),
          hintsApi.list(Number(id)),
        ])
        if (!cancelled) {
          setChallenge(c)
          setHints(Array.isArray(h) ? h : [])
        }
      } catch {
        if (!cancelled) setChallenge(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [id])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!user || !challenge) return
    setMessage(null)
    setSubmitting(true)
    try {
      const sub = await submissionsApi.submit(challenge.id, flag)
      if (sub.correct) {
        setMessage({ type: 'ok', text: 'Correct! Points awarded.' })
        setChallenge((prev) => prev ? { ...prev, solved: true } : null)
      } else {
        setMessage({ type: 'err', text: sub.feedback || 'Incorrect flag.' })
      }
    } catch (err) {
      setMessage({ type: 'err', text: err instanceof Error ? err.message : 'Submit failed' })
    } finally {
      setSubmitting(false)
    }
  }

  if (loading || !challenge) {
    return <div className="app"><p>{loading ? 'Loading…' : 'Challenge not found.'}</p></div>
  }

  return (
    <div className="app">
      <p><button type="button" className="btn" onClick={() => navigate(-1)}>← Back</button></p>
      <div className="card">
        <h1 style={{ marginTop: 0 }}>{challenge.name}</h1>
        <p><span className="badge">{challenge.category}</span> <span className={`badge ${challenge.difficulty}`}>{challenge.difficulty}</span> {challenge.points} pts</p>
        {challenge.solved && <span className="badge solved">Solved</span>}
        {challenge.description && (
          <div style={{ marginTop: '1rem', whiteSpace: 'pre-wrap' }}>{challenge.description}</div>
        )}
      </div>

      {user && !challenge.solved && (
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Submit flag</h2>
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Flag"
              value={flag}
              onChange={(e) => setFlag(e.target.value)}
              required
            />
            {message && <p className={message.type === 'ok' ? '' : 'error'}>{message.text}</p>}
            <button type="submit" className="btn primary" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit'}
            </button>
          </form>
        </div>
      )}

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Hints</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Revealing a hint deducts its cost from your score when you solve this challenge.
        </p>
        {user && !challenge.solved && (
          <p>
            <button
              type="button"
              className="btn"
              disabled={unlocking}
              onClick={async () => {
                setHintError(null)
                setUnlocking(true)
                try {
                  const next = await hintsApi.unlockNext(challenge.id)
                  setHints((prev) => [...prev, next])
                } catch (e) {
                  setHintError(e instanceof Error ? e.message : 'No more hints or error')
                } finally {
                  setUnlocking(false)
                }
              }}
            >
              {unlocking ? 'Revealing…' : 'Reveal next hint'}
            </button>
          </p>
        )}
        {hintError && <p className="error">{hintError}</p>}
        {hints.length === 0 && !user && <p>Log in to unlock hints.</p>}
        {hints.length === 0 && user && !hintError && <p>No hints revealed yet. Click the button above to reveal the first hint.</p>}
        {hints.length > 0 && (
          <ul style={{ paddingLeft: '1.25rem' }}>
            {hints.map((h) => (
              <li key={h.id} style={{ marginBottom: '0.5rem' }}>
                <strong>Hint {h.order}</strong>{h.cost > 0 && ` (−${h.cost} pts when you solve)`}: {h.content}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
