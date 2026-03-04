import { useState } from 'react'
import { admin } from '../../api/client'
import type { ValidationResult } from '../../types'

export default function AdminVm() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<{ filename?: string; size?: number; message?: string } | null>(null)
  const [err, setErr] = useState('')
  const [uploading, setUploading] = useState(false)
  const [validating, setValidating] = useState(false)
  const [validationResults, setValidationResults] = useState<ValidationResult[] | null>(null)

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return
    setErr('')
    setResult(null)
    setUploading(true)
    try {
      const res = await admin.uploadVmConfig(file)
      setResult(res)
      setFile(null)
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  async function handleValidate() {
    setErr('')
    setValidating(true)
    try {
      const res = await admin.validateChallenges()
      setValidationResults(res)
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Validation failed')
    } finally {
      setValidating(false)
    }
  }

  return (
    <div className="card">
      <h1 style={{ marginTop: 0 }}>VM config & validation</h1>
      <p style={{ color: 'var(--text-muted)' }}>
        This admin VM runs inside the same virtualised environment as the team VMs. You can upload VM descriptors
        and trigger automated checks to see whether each Docker-based challenge is reachable on its designated VM.
      </p>
      <form onSubmit={handleUpload}>
        <h2>Upload VM config</h2>
        <input
          type="file"
          accept=".json,.yaml,.yml"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        {err && <p className="error">{err}</p>}
        {result && <p style={{ color: 'var(--success)' }}>Uploaded: {result.filename} ({result.size} bytes)</p>}
        <button type="submit" className="btn primary" disabled={!file || uploading}>
          {uploading ? 'Uploading…' : 'Upload'}
        </button>
      </form>

      <hr style={{ margin: '2rem 0' }} />

      <h2>Validate deployed challenges</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        This triggers HTTP healthchecks against each challenge using its VM identifier and metadata
        (exposed port and optional healthcheck path) from the Brightspace submission.
      </p>
      <button type="button" className="btn primary" onClick={handleValidate} disabled={validating}>
        {validating ? 'Running validation…' : 'Run validation'}
      </button>

      {validationResults && (
        <table style={{ marginTop: '1rem' }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>VM</th>
              <th>Status</th>
              <th>Error</th>
              <th>Checked at</th>
            </tr>
          </thead>
          <tbody>
            {validationResults.map((r) => (
              <tr key={r.challenge_id}>
                <td>{r.challenge_id}</td>
                <td>{r.name}</td>
                <td>{r.vm_identifier ?? '–'}</td>
                <td>{r.status}</td>
                <td>{r.error ?? '–'}</td>
                <td>{r.checked_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
