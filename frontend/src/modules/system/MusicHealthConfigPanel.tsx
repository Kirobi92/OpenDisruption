import { useState, useEffect } from 'react'

/**
 * Panel: /api/music-health-config — Refresh-Interval anzeigen und live editieren.
 * Zeigt aktuellem Wert (refresh_s), Quelle (env/default/runtime) und erlaubt PUT-Update.
 */
export function MusicHealthConfigPanel({
  base,
  musicHealthRefreshMs,
  onRefreshMsChange,
}: {
  base: string
  musicHealthRefreshMs: number
  onRefreshMsChange: (ms: number) => void
}) {
  const [config, setConfig] = useState<{ refresh_s: number; source: string } | null>(null)
  const [editMode, setEditMode] = useState(false)
  const [inputVal, setInputVal] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')

  useEffect(() => {
    fetch(`${base}/api/music-health-config`, { cache: 'no-store' })
      .then((r) => r.ok ? r.json() : null)
      .then((cfg) => { if (cfg) setConfig(cfg) })
      .catch(() => {})
  }, [base, musicHealthRefreshMs])

  const handleSave = async () => {
    const val = parseInt(inputVal, 10)
    if (isNaN(val) || val < 10) { setSaveMsg('❌ Mindestwert 10 Sekunden'); return }
    setSaving(true); setSaveMsg('')
    try {
      const res = await fetch(`${base}/api/music-health-config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_s: val }),
      })
      if (!res.ok) { const d = await res.json(); setSaveMsg(`❌ ${d.detail ?? `HTTP ${res.status}`}`); setSaving(false); return }
      const updated = await res.json()
      setConfig(updated)
      onRefreshMsChange(val * 1000)
      setSaveMsg(`✅ Interval auf ${val}s gesetzt (Runtime)`)
      setEditMode(false)
    } catch (e) { setSaveMsg(`❌ ${e instanceof Error ? e.message : String(e)}`) }
    setSaving(false)
  }

  if (!config) return null
  const sourceLabel = config.source === 'env' ? '📌 ENV' : config.source === 'runtime' ? '⚡ Runtime' : '⚙️ Default'

  return (
    <div className="gpuPanel" style={{ marginBottom: 14 }} data-testid="music-health-config-panel">
      <strong>⏱️ Music-Health Refresh-Config</strong>
      <div style={{ fontSize: 11, color: '#aaa', marginTop: 6 }}>
        <span style={{ marginRight: 12 }}>Interval: <strong style={{ color: '#e0e0e0' }} data-testid="refresh-s">{config.refresh_s}s</strong></span>
        <span style={{ marginRight: 12 }}>Quelle: <strong style={{ color: '#7986cb' }} data-testid="source-label">{sourceLabel}</strong></span>
        <span>ENV: <code style={{ fontSize: 10, color: '#888' }}>KIROBI_MUSIC_HEALTH_REFRESH_S</code></span>
      </div>
      {!editMode ? (
        <button
          onClick={() => { setInputVal(String(config.refresh_s)); setEditMode(true); setSaveMsg('') }}
          style={{ marginTop: 8, padding: '3px 10px', fontSize: 11, background: '#2a2a3a', color: '#90caf9', border: '1px solid #444', borderRadius: 4, cursor: 'pointer' }}
          data-testid="edit-button"
        >
          ✏️ Interval ändern
        </button>
      ) : (
        <div style={{ marginTop: 8, display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="number"
            value={inputVal}
            min={10}
            onChange={(e) => setInputVal(e.target.value)}
            style={{ width: 70, padding: '2px 6px', fontSize: 12, background: '#1a1a2a', color: '#e0e0e0', border: '1px solid #555', borderRadius: 4 }}
            data-testid="interval-input"
          />
          <span style={{ fontSize: 11, color: '#aaa' }}>Sekunden (min. 10)</span>
          <button
            onClick={handleSave}
            disabled={saving}
            style={{ padding: '3px 10px', fontSize: 11, background: '#1b3a1f', color: '#4caf50', border: '1px solid #4caf50', borderRadius: 4, cursor: 'pointer' }}
            data-testid="save-button"
          >
            {saving ? '…' : '💾 Speichern'}
          </button>
          <button
            onClick={() => { setEditMode(false); setSaveMsg('') }}
            style={{ padding: '3px 8px', fontSize: 11, background: '#2a2a3a', color: '#aaa', border: '1px solid #444', borderRadius: 4, cursor: 'pointer' }}
            data-testid="cancel-button"
          >
            ✕
          </button>
        </div>
      )}
      {saveMsg && <div style={{ fontSize: 11, marginTop: 6 }} data-testid="save-msg">{saveMsg}</div>}
    </div>
  )
}

export default MusicHealthConfigPanel
