import { Fragment, useEffect, useState } from 'react'
import { challenges as challengesApi, hints as hintsApi, admin as adminApi } from '../../api/client'
import type { Challenge, Hint } from '../../types'

export default function AdminChallenges() {
  const [list, setList] = useState<Challenge[]>([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')
  const [form, setForm] = useState<{ name: string; description: string; category: string; difficulty: string; points: string; flag: string }>({ name: '', description: '', category: 'web', difficulty: 'easy', points: '100', flag: '' })
  const [creating, setCreating] = useState(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [hintsByChallenge, setHintsByChallenge] = useState<Record<number, Hint[]>>({})
  const [hintForm, setHintForm] = useState<{ order: string; content: string; cost: string }>({ order: '1', content: '', cost: '0' })
  const [addingHint, setAddingHint] = useState(false)

  function load() {
    challengesApi.list().then(setList).catch((e) => setErr(e instanceof Error ? e.message : 'Failed')).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function loadHints(challengeId: number) {
    try {
      const h = await adminApi.getChallengeHints(challengeId)
      setHintsByChallenge((prev) => ({ ...prev, [challengeId]: h }))
    } catch {
      setHintsByChallenge((prev) => ({ ...prev, [challengeId]: [] }))
    }
  }

  function toggleHints(c: Challenge) {
    if (expandedId === c.id) {
      setExpandedId(null)
    } else {
      setExpandedId(c.id)
      loadHints(c.id)
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setErr('')
    setCreating(true)
    try {
      await challengesApi.create({
        name: form.name,
        description: form.description || undefined,
        category: form.category,
        difficulty: form.difficulty,
        points: Number(form.points),
        flag: form.flag,
      })
      setForm({ name: '', description: '', category: 'web', difficulty: 'easy', points: '100', flag: '' })
      load()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Create failed')
    } finally {
      setCreating(false)
    }
  }

  async function handleAddHint(challengeId: number) {
    setAddingHint(true)
    setErr('')
    try {
      await hintsApi.create({
        challenge_id: challengeId,
        order: Number(hintForm.order),
        content: hintForm.content,
        cost: Number(hintForm.cost) || 0,
      })
      setHintForm({ order: String(Number(hintForm.order) + 1), content: '', cost: hintForm.cost })
      loadHints(challengeId)
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Add hint failed')
    } finally {
      setAddingHint(false)
    }
  }

  async function handleDeleteHint(hintId: number, challengeId: number) {
    if (!confirm('Delete this hint?')) return
    try {
      await hintsApi.delete(hintId)
      loadHints(challengeId)
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this challenge?')) return
    try {
      await challengesApi.delete(id)
      load()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  if (loading) return <p>Loading…</p>

  return (
    <>
      <div className="card">
        <h2>Create challenge</h2>
        <form onSubmit={handleCreate}>
          <label>Name</label>
          <input type="text" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
          <label>Description</label>
          <textarea value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} rows={3} />
          <label>Category</label>
          <input type="text" value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))} />
          <label>Difficulty</label>
          <select value={form.difficulty} onChange={(e) => setForm((f) => ({ ...f, difficulty: e.target.value }))}>
            <option value="easy">easy</option>
            <option value="medium">medium</option>
            <option value="hard">hard</option>
          </select>
          <label>Points</label>
          <input type="number" value={form.points} onChange={(e) => setForm((f) => ({ ...f, points: e.target.value }))} />
          <label>Flag (stored hashed)</label>
          <input type="text" value={form.flag} onChange={(e) => setForm((f) => ({ ...f, flag: e.target.value }))} required />
          {err && <p className="error">{err}</p>}
          <button type="submit" className="btn primary" disabled={creating}>{creating ? 'Creating…' : 'Create'}</button>
        </form>
      </div>
      <div className="card">
        <h2>Challenges</h2>
        <table>
          <thead>
            <tr><th>ID</th><th>Name</th><th>Category</th><th>Points</th><th></th></tr>
          </thead>
          <tbody>
            {list.map((c) => (
              <Fragment key={c.id}>
                <tr>
                  <td>{c.id}</td>
                  <td>{c.name}</td>
                  <td>{c.category}</td>
                  <td>{c.points}</td>
                  <td>
                    <button type="button" className="btn" onClick={() => toggleHints(c)}>
                      {expandedId === c.id ? 'Hide hints' : 'Manage hints'}
                    </button>
                    <button type="button" className="btn danger" onClick={() => handleDelete(c.id)} style={{ marginLeft: 8 }}>Delete</button>
                  </td>
                </tr>
                {expandedId === c.id && (
                  <tr key={`hints-${c.id}`}>
                    <td colSpan={5} style={{ padding: '1rem', background: 'var(--bg-input)', borderBottom: '1px solid var(--border)' }}>
                      <h3 style={{ marginTop: 0 }}>Hints for {c.name}</h3>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Cost is the number of points deducted when the player reveals this hint (and then solves the challenge).</p>
                      <table style={{ marginBottom: '1rem' }}>
                        <thead>
                          <tr><th>Order</th><th>Content</th><th>Cost (pts)</th><th></th></tr>
                        </thead>
                        <tbody>
                          {(hintsByChallenge[c.id] || []).map((h) => (
                            <tr key={h.id}>
                              <td>{h.order}</td>
                              <td>{h.content}</td>
                              <td>{h.cost}</td>
                              <td><button type="button" className="btn danger" onClick={() => handleDeleteHint(h.id, c.id)}>Delete</button></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <form onSubmit={(e) => { e.preventDefault(); handleAddHint(c.id); }}>
                        <label>Order</label>
                        <input type="number" value={hintForm.order} onChange={(e) => setHintForm((f) => ({ ...f, order: e.target.value }))} style={{ width: 80 }} />
                        <label>Content</label>
                        <input type="text" value={hintForm.content} onChange={(e) => setHintForm((f) => ({ ...f, content: e.target.value }))} required placeholder="Hint text" />
                        <label>Cost (points deducted when revealed)</label>
                        <input type="number" min={0} value={hintForm.cost} onChange={(e) => setHintForm((f) => ({ ...f, cost: e.target.value }))} style={{ width: 80 }} />
                        <button type="submit" className="btn primary" disabled={addingHint}>{addingHint ? 'Adding…' : 'Add hint'}</button>
                      </form>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
            {list.length === 0 && <tr><td colSpan={5}>No challenges.</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  )
}
