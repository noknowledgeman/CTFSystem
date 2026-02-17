import { useState } from 'react'
import { admin } from '../../api/client'

export default function AdminVm() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<{ filename?: string; size?: number; message?: string } | null>(null)
  const [err, setErr] = useState('')
  const [uploading, setUploading] = useState(false)

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

  return (
    <div className="card">
      <h1 style={{ marginTop: 0 }}>Upload VM config</h1>
      <p style={{ color: 'var(--text-muted)' }}>Upload a JSON or YAML descriptor for a flag VM. It will be stored and can be linked to challenges.</p>
      <form onSubmit={handleUpload}>
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
    </div>
  )
}
