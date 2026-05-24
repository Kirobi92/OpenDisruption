import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { getBackendHttpBase } from '../../stores/agentStore'
import { ModuleCard } from '../placeholder/ModuleCard'

type Person = 'sven' | 'samira' | 'sineo'
type Note = { id: string; text: string; person: Person; created_at: number }
type Task = { id: string; title: string; person: Person; status: string; created_at: number }
type Expense = { id: string; amount: number; category: string; person: Person; note?: string }
type PersonaContext = { name: Person; voice: string; style: string; prompt: string; greeting: string; color: string }
type FileEntry = { name: string; size: number; modified_at: number; mime: string }
type ApkProfile = {
  theme: string; agent_name: string; child_mode: boolean
  child_safe_topics: string[]; blocked_topics: string[]
  notifications_enabled: boolean; language: string; avatar_style: string
  updated_at?: number
}

type Tab = 'hub' | 'files' | 'profile'

const labels: Record<Person, string> = { sven: 'Sven', samira: 'Samira', sineo: 'Sineo' }
const avatarEmoji: Record<Person, string> = { sven: '👨‍💻', samira: '👩‍🌸', sineo: '🧒' }
const personaColors: Record<Person, string> = { sven: '#3b82f6', samira: '#f4b8d8', sineo: '#22c55e' }

// ─── Login Screen ─────────────────────────────────────────────────────────────
function LoginScreen({ onLogin }: { onLogin: (p: Person) => void }) {
  const base = useMemo(getBackendHttpBase, [])
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleLogin(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${base}/api/family/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim().toLowerCase(), password }),
      })
      const data = await res.json()
      if (res.ok && data.ok) {
        onLogin(data.persona as Person)
      } else {
        setError(data.detail || 'Login fehlgeschlagen')
      }
    } catch {
      setError('Verbindungsfehler')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 48, gap: 24 }}>
      <div style={{ fontSize: 48 }}>🏠</div>
      <h2 style={{ margin: 0 }}>Familien-Hub</h2>
      <p style={{ opacity: 0.6, margin: 0, fontSize: 14 }}>Wer bist du?</p>

      {/* Schnell-Login per Avatar */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 8 }}>
        {(['sven', 'samira', 'sineo'] as Person[]).map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => setUsername(p)}
            style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
              padding: '12px 18px', borderRadius: 12,
              border: `2px solid ${username === p ? personaColors[p] : 'transparent'}`,
              background: username === p ? `${personaColors[p]}22` : undefined,
              cursor: 'pointer', fontSize: 14,
            }}
          >
            <span style={{ fontSize: 32 }}>{avatarEmoji[p]}</span>
            {labels[p]}
          </button>
        ))}
      </div>

      <form onSubmit={handleLogin} style={{ display: 'grid', gap: 12, width: '100%', maxWidth: 300 }}>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Benutzername"
          autoComplete="username"
          required
          style={{ padding: '10px 14px', borderRadius: 8, fontSize: 15 }}
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Passwort"
          autoComplete="current-password"
          required
          style={{ padding: '10px 14px', borderRadius: 8, fontSize: 15 }}
        />
        {error && <p style={{ color: '#f87171', margin: 0, fontSize: 13 }}>⚠️ {error}</p>}
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '11px 0', borderRadius: 8, fontSize: 15, fontWeight: 600,
            background: '#3b82f6', color: '#fff', border: 'none', cursor: 'pointer', opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? 'Laden…' : 'Einloggen'}
        </button>
      </form>
    </div>
  )
}

// ─── Main Module ──────────────────────────────────────────────────────────────
export default function FamilyModule() {
  const base = useMemo(getBackendHttpBase, [])
  const [loggedIn, setLoggedIn] = useState<Person | null>(null)
  const [persona, setPersona] = useState<Person>('sven')
  const [personaContext, setPersonaContext] = useState<PersonaContext | null>(null)
  const [notes, setNotes] = useState<Note[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [noteText, setNoteText] = useState('')
  const [taskTitle, setTaskTitle] = useState('')
  const [expenseAmount, setExpenseAmount] = useState('')
  const [expenseCategory, setExpenseCategory] = useState('Haushalt')

  // Dateibereich & APK-Profil
  const [activeTab, setActiveTab] = useState<Tab>('hub')
  const [files, setFiles] = useState<FileEntry[]>([])
  const [filesLoading, setFilesLoading] = useState(false)
  const [fileUploadStatus, setFileUploadStatus] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [apkProfile, setApkProfile] = useState<ApkProfile | null>(null)
  const [profileSaving, setProfileSaving] = useState(false)

  async function refresh() {
    const [personaRes, notesRes, tasksRes, expensesRes] = await Promise.all([
      fetch(`${base}/api/family/persona`),
      fetch(`${base}/api/family/notes`),
      fetch(`${base}/api/family/tasks`),
      fetch(`${base}/api/family/expenses`),
    ])
    if (personaRes.ok) {
      const p = await personaRes.json()
      setPersona(p.active || 'sven')
      setPersonaContext(p.runtime_context || p.active_profile || null)
    }
    if (notesRes.ok) setNotes((await notesRes.json()).notes || [])
    if (tasksRes.ok) setTasks((await tasksRes.json()).tasks || [])
    if (expensesRes.ok) setExpenses((await expensesRes.json()).expenses || [])
  }

  useEffect(() => { if (loggedIn) void refresh() }, [loggedIn])   

  function handleLogin(p: Person) {
    setLoggedIn(p)
    setPersona(p)
  }

  function handleLogout() {
    setLoggedIn(null)
    setPersona('sven')
    setPersonaContext(null)
    setFiles([])
    setApkProfile(null)
    setActiveTab('hub')
  }

  async function loadFiles(p: Person) {
    setFilesLoading(true)
    try {
      const res = await fetch(`${base}/api/family/files/${p}`)
      if (res.ok) setFiles((await res.json()).files || [])
    } finally {
      setFilesLoading(false)
    }
  }

  async function loadApkProfile(p: Person) {
    const res = await fetch(`${base}/api/family/profile/${p}`)
    if (res.ok) setApkProfile(await res.json())
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (!f || !loggedIn) return
    setFileUploadStatus('Hochladen…')
    const fd = new FormData()
    fd.append('file', f)
    try {
      const res = await fetch(`${base}/api/family/files/${loggedIn}/upload`, { method: 'POST', body: fd })
      const data = await res.json()
      if (res.ok) {
        setFileUploadStatus(`✅ ${data.name} hochgeladen`)
        await loadFiles(loggedIn)
      } else {
        setFileUploadStatus(`⚠️ ${data.detail || 'Fehler'}`)
      }
    } catch {
      setFileUploadStatus('⚠️ Verbindungsfehler')
    }
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  async function handleDeleteFile(name: string) {
    if (!loggedIn) return
    await fetch(`${base}/api/family/files/${loggedIn}/${encodeURIComponent(name)}`, { method: 'DELETE' })
    await loadFiles(loggedIn)
  }

  async function saveApkProfile(updates: Partial<ApkProfile>) {
    if (!loggedIn) return
    setProfileSaving(true)
    try {
      const res = await fetch(`${base}/api/family/profile/${loggedIn}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      })
      if (res.ok) setApkProfile(await res.json())
    } finally {
      setProfileSaving(false)
    }
  }

  useEffect(() => {
    if (loggedIn) {
      void refresh()
      void loadFiles(loggedIn)
      void loadApkProfile(loggedIn)
    }
  }, [loggedIn])

  async function switchPersona(p: Person) {
    setPersona(p)
    const res = await fetch(`${base}/api/family/persona`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ persona: p }) })
    if (res.ok) await refresh()
  }

  async function addNote(e: FormEvent) {
    e.preventDefault()
    if (!noteText.trim()) return
    await fetch(`${base}/api/family/notes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: noteText, person: persona }) })
    setNoteText('')
    await refresh()
  }

  async function addTask(e: FormEvent) {
    e.preventDefault()
    if (!taskTitle.trim()) return
    await fetch(`${base}/api/family/tasks`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: taskTitle, person: persona }) })
    setTaskTitle('')
    await refresh()
  }

  async function addExpense(e: FormEvent) {
    e.preventDefault()
    const amount = Number(expenseAmount.replace(',', '.'))
    if (!Number.isFinite(amount)) return
    await fetch(`${base}/api/family/expenses`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ amount, category: expenseCategory, person: persona }) })
    setExpenseAmount('')
    await refresh()
  }

  // ── Nicht eingeloggt → Login-Screen ──
  if (!loggedIn) return <LoginScreen onLogin={handleLogin} />

  // ── Eingeloggt ──
  const accentColor = personaContext?.color || personaColors[persona]

  return (
    <div>
      {/* Header mit Logout */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 28 }}>{avatarEmoji[loggedIn]}</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>Hallo, {labels[loggedIn]}!</div>
            <div style={{ fontSize: 12, opacity: 0.6 }}>
              {apkProfile?.agent_name || 'Kirobi'} · Familien-Hub
              {apkProfile?.child_mode && <span style={{ color: '#22c55e', marginLeft: 6 }}>🔒 Kinderschutz</span>}
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          style={{ fontSize: 12, padding: '6px 12px', borderRadius: 8, opacity: 0.7 }}
        >
          Abmelden
        </button>
      </div>

      {/* Tab-Navigation */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
        {(['hub', 'files', 'profile'] as Tab[]).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '6px 14px', borderRadius: 20, fontSize: 13,
              background: activeTab === tab ? accentColor : undefined,
              color: activeTab === tab ? '#fff' : undefined,
              fontWeight: activeTab === tab ? 700 : 400,
              opacity: activeTab === tab ? 1 : 0.6,
            }}
          >
            {tab === 'hub' && '🏠 Hub'}
            {tab === 'files' && '📁 Dateien'}
            {tab === 'profile' && '⚙️ Profil'}
          </button>
        ))}
      </div>

      {/* ── Tab: Hub ── */}
      {activeTab === 'hub' && <>
        <ModuleCard
          title="Familien-Hub"
          subtitle="Schnellnotizen, Aufgaben, Ausgaben und familienfreundliche Kirobi-Modi."
          items={[
            `Aktive Persona: ${labels[persona]}`,
            `Live Voice: ${personaContext?.voice || 'lädt...'}`,
            'Persona-Wechsel wirkt ab der nächsten Voice-Session auf Systemprompt + Edge-TTS-Stimme',
            'Sineo-Modus erzwingt kindgerechte Schutzgrenzen',
          ]}
        />

        <section className="moduleCard" style={{ marginTop: 12, borderColor: accentColor }}>
          <h2>Persona</h2>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {(['sven', 'samira', 'sineo'] as Person[]).map((p) => (
              <button key={p} type="button" onClick={() => void switchPersona(p)} style={{ opacity: persona === p ? 1 : 0.55 }}>
                {avatarEmoji[p]} {labels[p]}
              </button>
            ))}
          </div>
          {personaContext && (
            <div style={{ marginTop: 10 }}>
              <p><strong>Stil:</strong> {personaContext.style}</p>
              <p><strong>Greeting:</strong> {personaContext.greeting}</p>
              <p style={{ fontSize: 12, opacity: 0.78 }}><strong>Prompt-Hook:</strong> aktiv fuer neue Pipecat-Sessions.</p>
            </div>
          )}
        </section>

        <section className="moduleCard" style={{ marginTop: 12 }}>
          <h2>Schnellnotiz</h2>
          <form onSubmit={addNote} style={{ display: 'grid', gap: 8 }}>
            <textarea value={noteText} onChange={(e) => setNoteText(e.target.value)} placeholder="Was soll Kirobi merken?" />
            <button type="submit">Notiz speichern</button>
          </form>
          {notes.slice(0, 5).map((n) => <p key={n.id}><strong>{labels[n.person]}</strong>: {n.text}</p>)}
        </section>

        <section className="moduleCard" style={{ marginTop: 12 }}>
          <h2>Aufgaben</h2>
          <form onSubmit={addTask} style={{ display: 'flex', gap: 8 }}>
            <input value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} placeholder="Neue Aufgabe" />
            <button type="submit">+</button>
          </form>
          {tasks.slice(0, 8).map((t) => <p key={t.id}><strong>{labels[t.person]}</strong>: {t.title} · {t.status}</p>)}
        </section>

        <section className="moduleCard" style={{ marginTop: 12 }}>
          <h2>Ausgaben</h2>
          <form onSubmit={addExpense} style={{ display: 'flex', gap: 8 }}>
            <input value={expenseAmount} onChange={(e) => setExpenseAmount(e.target.value)} placeholder="Betrag" />
            <input value={expenseCategory} onChange={(e) => setExpenseCategory(e.target.value)} placeholder="Kategorie" />
            <button type="submit">Speichern</button>
          </form>
          {expenses.slice(0, 5).map((x) => <p key={x.id}><strong>{labels[x.person]}</strong>: {x.amount.toFixed(2)} € · {x.category}</p>)}
        </section>
      </>}

      {/* ── Tab: Dateibereich ── */}
      {activeTab === 'files' && (
        <section className="moduleCard">
          <h2>📁 Persönlicher Dateibereich — {labels[loggedIn]}</h2>
          <p style={{ fontSize: 12, opacity: 0.6 }}>
            Nur du siehst diese Dateien. Max. 50 MB pro Datei.
            {apkProfile?.child_mode && ' Ausführbare Dateien werden blockiert.'}
          </p>

          {/* Upload */}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
            <input
              ref={fileInputRef}
              type="file"
              onChange={(e) => void handleFileUpload(e)}
              style={{ fontSize: 13 }}
            />
            <button type="button" onClick={() => void loadFiles(loggedIn)} style={{ fontSize: 12 }}>
              🔄
            </button>
          </div>
          {fileUploadStatus && <p style={{ fontSize: 13, margin: '4px 0 8px' }}>{fileUploadStatus}</p>}

          {/* Dateiliste */}
          {filesLoading
            ? <p style={{ opacity: 0.5, fontSize: 13 }}>Lädt…</p>
            : files.length === 0
              ? <p style={{ opacity: 0.5, fontSize: 13 }}>Noch keine Dateien.</p>
              : (
                <div style={{ display: 'grid', gap: 6 }}>
                  {files.map((f) => (
                    <div key={f.name} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</span>
                      <span style={{ opacity: 0.5, whiteSpace: 'nowrap' }}>{(f.size / 1024).toFixed(1)} KB</span>
                      <a
                        href={`${base}/api/family/files/${loggedIn}/${encodeURIComponent(f.name)}`}
                        download={f.name}
                        style={{ fontSize: 12, opacity: 0.7 }}
                      >⬇️</a>
                      <button
                        type="button"
                        onClick={() => void handleDeleteFile(f.name)}
                        style={{ fontSize: 11, padding: '2px 6px', opacity: 0.6 }}
                      >🗑️</button>
                    </div>
                  ))}
                </div>
              )
          }
        </section>
      )}

      {/* ── Tab: APK-Profil ── */}
      {activeTab === 'profile' && apkProfile && (
        <section className="moduleCard">
          <h2>⚙️ APK-Profil — {labels[loggedIn]}</h2>
          <p style={{ fontSize: 12, opacity: 0.6 }}>Persönliche App-Einstellungen. Wirken ab dem nächsten Start.</p>

          <div style={{ display: 'grid', gap: 12, marginTop: 10 }}>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 14 }}>
              Agent-Name
              <input
                value={apkProfile.agent_name}
                onChange={(e) => setApkProfile({ ...apkProfile, agent_name: e.target.value })}
                style={{ padding: '6px 10px', borderRadius: 8 }}
              />
            </label>

            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 14 }}>
              Theme
              <select
                value={apkProfile.theme}
                onChange={(e) => setApkProfile({ ...apkProfile, theme: e.target.value })}
                style={{ padding: '6px 10px', borderRadius: 8 }}
              >
                <option value="dark">Dark</option>
                <option value="light">Light</option>
                <option value="auto">Auto (System)</option>
              </select>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>
              <input
                type="checkbox"
                checked={apkProfile.child_mode}
                onChange={(e) => setApkProfile({ ...apkProfile, child_mode: e.target.checked })}
              />
              Kinderschutz-Modus aktiv
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>
              <input
                type="checkbox"
                checked={apkProfile.notifications_enabled}
                onChange={(e) => setApkProfile({ ...apkProfile, notifications_enabled: e.target.checked })}
              />
              Benachrichtigungen aktiviert
            </label>

            {apkProfile.child_mode && (
              <div style={{ background: '#22c55e18', borderRadius: 8, padding: 10, fontSize: 13 }}>
                <strong>🔒 Kinderschutz aktiv</strong>
                <p style={{ margin: '4px 0 0', opacity: 0.8 }}>
                  Erlaubte Themen: {apkProfile.child_safe_topics.join(', ')}<br />
                  Blockierte Themen: {apkProfile.blocked_topics.join(', ')}
                </p>
              </div>
            )}

            <button
              type="button"
              onClick={() => void saveApkProfile(apkProfile)}
              disabled={profileSaving}
              style={{ padding: '10px 0', borderRadius: 8, background: accentColor, color: '#fff', fontWeight: 600, opacity: profileSaving ? 0.6 : 1 }}
            >
              {profileSaving ? 'Speichern…' : '💾 Profil speichern'}
            </button>
          </div>
        </section>
      )}
    </div>
  )
}

