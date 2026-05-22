import { FormEvent, useEffect, useMemo, useState } from 'react'
import { ModuleCard } from '../placeholder/ModuleCard'

type Product = { id: string; title: string; thumbnail?: string; handle?: string; variants?: Array<{ calculated_price?: { calculated_amount?: number } }> }
type PrintJob = { id: string; title: string; customer: string; status: string; material: string; color: string; notes?: string }
type Filament = { material: string; color: string; grams_remaining: number; spool_id?: string }

function backendBase(): string {
  const host = window.location.hostname === 'localhost' && !window.location.port ? '192.168.178.10' : window.location.hostname
  const proto = window.location.protocol === 'https:' ? 'https' : 'http'
  return `${proto}://${host}:8765`
}

export default function InventoryModule() {
  const base = useMemo(backendBase, [])
  const [products, setProducts] = useState<Product[]>([])
  const [jobs, setJobs] = useState<PrintJob[]>([])
  const [filament, setFilament] = useState<Filament[]>([])
  const [status, setStatus] = useState<Record<string, string>>({})
  const [title, setTitle] = useState('Neuer 3D-Druck Job')
  const [material, setMaterial] = useState('PLA')
  const [color, setColor] = useState('Schwarz')

  async function refresh() {
    const [statusRes, productsRes, jobsRes, filamentRes] = await Promise.all([
      fetch(`${base}/api/commerce/status`),
      fetch(`${base}/api/commerce/products?limit=8`),
      fetch(`${base}/api/commerce/print/jobs`),
      fetch(`${base}/api/commerce/filament`),
    ])
    if (statusRes.ok) setStatus(await statusRes.json())
    if (productsRes.ok) setProducts((await productsRes.json()).products || [])
    if (jobsRes.ok) setJobs((await jobsRes.json()).jobs || [])
    if (filamentRes.ok) setFilament((await filamentRes.json()).filament || [])
  }

  useEffect(() => {
    void refresh()
  }, [])

  async function addJob(e: FormEvent) {
    e.preventDefault()
    const res = await fetch(`${base}/api/commerce/print/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, material, color, status: 'queued', customer: 'intern' }),
    })
    if (res.ok) {
      setTitle('Neuer 3D-Druck Job')
      await refresh()
    }
  }

  return (
    <div>
      <ModuleCard
        title="Inventar & 3D-Druck"
        subtitle="Live-Webshop-Produkte, lokale Druckjob-Liste und Filament-Bestand."
        primaryAction={{ label: 'InvenTree öffnen', href: 'http://192.168.178.10:4999' }}
        items={[
          `Medusa: ${status.medusa || 'prüfe...'}`,
          `InvenTree: ${status.inventree || 'prüfe...'}`,
          'Bambu Direktstatus wartet weiter auf IP/Serial/Access-Code; Fallback ist aktiv.',
        ]}
      />

      <section className="moduleCard" style={{ marginTop: 12 }}>
        <h2>Webshop Produkte</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12 }}>
          {products.map((p) => (
            <div key={p.id} style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: 10 }}>
              {p.thumbnail && <img src={p.thumbnail} alt={p.title} style={{ width: '100%', borderRadius: 10 }} />}
              <strong>{p.title}</strong>
              <p style={{ opacity: 0.7 }}>{p.handle}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="moduleCard" style={{ marginTop: 12 }}>
        <h2>Druckjobs</h2>
        <form onSubmit={addJob} style={{ display: 'grid', gap: 8 }}>
          <input value={title} onChange={(e) => setTitle(e.target.value)} />
          <div style={{ display: 'flex', gap: 8 }}>
            <input value={material} onChange={(e) => setMaterial(e.target.value)} />
            <input value={color} onChange={(e) => setColor(e.target.value)} />
          </div>
          <button type="submit">Druckjob anlegen</button>
        </form>
        {jobs.map((job) => (
          <div key={job.id} style={{ marginTop: 10, borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 10 }}>
            <strong>{job.title}</strong> · {job.status} · {job.material} {job.color}
          </div>
        ))}
      </section>

      <section className="moduleCard" style={{ marginTop: 12 }}>
        <h2>Filament</h2>
        {filament.map((f) => (
          <div key={f.spool_id || `${f.material}-${f.color}`} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
            <span>{f.material} · {f.color}</span><strong>{f.grams_remaining}g</strong>
          </div>
        ))}
      </section>
    </div>
  )
}
