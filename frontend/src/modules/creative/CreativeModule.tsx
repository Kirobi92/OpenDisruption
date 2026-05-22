import { FormEvent, useEffect, useMemo, useState } from 'react'
import { getBackendHttpBase } from '../../stores/agentStore'
import { ModuleCard } from '../placeholder/ModuleCard'

type SearchResult = { score: number; filename: string; text: string }
type ComfyJob = { prompt_id: string; prompt: string; status: string; checkpoint?: string; images?: Array<{ url: string; filename: string }> }

export default function CreativeModule() {
  const base = useMemo(getBackendHttpBase, [])
  const [file, setFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState('')
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [prompt, setPrompt] = useState('Schwarz-goldenes 3D-Druck-Bar Produktfoto, hochwertig, dramatische Beleuchtung')
  const [generateStatus, setGenerateStatus] = useState('')
  const [jobs, setJobs] = useState<ComfyJob[]>([])
  const [checkpoints, setCheckpoints] = useState<string[]>([])
  const [checkpoint, setCheckpoint] = useState('')

  async function refreshComfy() {
    const [statusRes, jobsRes] = await Promise.all([
      fetch(`${base}/api/creative/comfyui/status`),
      fetch(`${base}/api/creative/comfyui/jobs`),
    ])
    if (statusRes.ok) {
      const data = await statusRes.json()
      setCheckpoints(data.checkpoints || [])
      setCheckpoint((current) => current || data.checkpoints?.[0] || '')
    }
    if (jobsRes.ok) {
      const data = await jobsRes.json()
      setJobs(data.jobs || [])
    }
  }

  useEffect(() => {
    void refreshComfy()
    const id = window.setInterval(() => void refreshComfy(), 10000)
    return () => window.clearInterval(id)
  }, [])

  async function upload() {
    if (!file) return
    setUploadStatus('Indexiere lokal...')
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${base}/api/knowledge/upload`, { method: 'POST', body: form })
    if (!res.ok) throw new Error(await res.text())
    const data = await res.json()
    setUploadStatus(`OK: ${data.filename} · ${data.chunks} Chunk(s)`)
  }

  async function search(e: FormEvent) {
    e.preventDefault()
    if (!query.trim()) return
    const res = await fetch(`${base}/api/knowledge/search?q=${encodeURIComponent(query)}&limit=5`)
    if (!res.ok) throw new Error(await res.text())
    const data = await res.json()
    setResults(data.results || [])
  }

  async function generateImage(e: FormEvent) {
    e.preventDefault()
    if (!prompt.trim()) return
    setGenerateStatus('ComfyUI Job wird gestartet...')
    const res = await fetch(`${base}/api/creative/comfyui/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, checkpoint: checkpoint || undefined }),
    })
    if (!res.ok) {
      setGenerateStatus(await res.text())
      return
    }
    const data = await res.json()
    setGenerateStatus(`Job gestartet: ${data.prompt_id}`)
    await refreshComfy()
  }

  return (
    <div>
      <ModuleCard
        title="Kreativ-Zentrale"
        subtitle="ComfyUI, Produktbilder, Marketing-Visuals und Wissens-Upload."
        primaryAction={{ label: 'ComfyUI öffnen', href: 'http://192.168.178.10:8188' }}
        items={[
          'ComfyUI Prompt-Submit läuft jetzt direkt über Kirobi Backend',
          'Wissens-Upload: TXT/MD/PDF → Ollama Embeddings → Qdrant',
          'Galerie zeigt letzte ComfyUI Jobs und fertige Bilder',
        ]}
      />

      <section className="moduleCard" style={{ marginTop: 12 }}>
        <h2>Bildgenerator</h2>
        <p>Lokaler ComfyUI-Job für Produktbilder, Marketing und 3D-Druck-Bar Visuals.</p>
        <form onSubmit={generateImage} style={{ display: 'grid', gap: 10 }}>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={4} />
          <select value={checkpoint} onChange={(e) => setCheckpoint(e.target.value)}>
            {checkpoints.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <button type="submit">Bild generieren</button>
        </form>
        {generateStatus && <p>{generateStatus}</p>}
        <div style={{ display: 'grid', gap: 12, marginTop: 12 }}>
          {jobs.slice(0, 10).map((job) => (
            <div key={job.prompt_id} style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 10 }}>
              <strong>{job.status}</strong> <span>{job.prompt.slice(0, 100)}</span>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                {(job.images || []).map((img) => <img key={img.url} src={img.url.startsWith('http') ? img.url : `${base}${img.url}`} alt={img.filename} style={{ width: 120, borderRadius: 12 }} />)}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="moduleCard" style={{ marginTop: 12 }}>
        <h2>Wissens-Upload</h2>
        <p>Local-first MVP: Datei bleibt lokal, Index landet in Qdrant collection opendisruption_workspace.</p>
        <input type="file" accept=".txt,.md,.pdf" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <button type="button" onClick={() => void upload()} disabled={!file}>Upload & Index</button>
        {uploadStatus && <p>{uploadStatus}</p>}

        <form onSubmit={search} style={{ marginTop: 14 }}>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Wissenssuche..." />
          <button type="submit">Suchen</button>
        </form>
        {results.map((r, idx) => (
          <div key={`${r.filename}-${idx}`} style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
            <strong>{r.filename}</strong> <span>({Math.round(r.score * 100)}%)</span>
            <p>{r.text}</p>
          </div>
        ))}
      </section>
    </div>
  )
}
