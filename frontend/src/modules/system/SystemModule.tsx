import { useCallback, useEffect, useMemo, useState } from 'react'
import { getBackendHttpBase } from '../../stores/agentStore'
import { MusicHealthConfigPanel } from './MusicHealthConfigPanel'
import { AudioStatusPanel } from './AudioStatusPanel'
import { AlertHistoryPanel } from './AlertHistoryPanel'
import { DashboardPanel } from './DashboardPanel'
import { MilestoneFiredPanel } from './MilestoneFiredPanel'
import { MilestoneConfigPanel } from './MilestoneConfigPanel'
import { DownloadHistoryPanel } from './DownloadHistoryPanel'
import { DownloadComparePanel } from './DownloadComparePanel'
import { MusicHealthBadgePanel } from './MusicHealthBadgePanel'
import { ScAlertsPanel } from './ScAlertsPanel'
import { ScTrendPanel } from './ScTrendPanel'
import { GpuPanel } from './GpuPanel'
import { ServicesGridPanel } from './ServicesGridPanel'
import { LiveLogsPanel } from './LiveLogsPanel'
import { BUILD_TIME_GREEN, BUILD_TIME_YELLOW } from './Sparkline'
import {
  SystemStatus,
  AudioStatus,
  AlertEntry,
  DashboardData,
  DashboardConfig,
  MilestoneFiredData,
  MilestoneConfig,
  DownloadHistoryData,
  DownloadCompareData,
  MusicHealthData,
  ScAlertsData,
  GpuStatus,
} from './types'
import './SystemModule.css'

export default function SystemModule() {
  const [data, setData] = useState<SystemStatus | null>(null)
  const [audioStatus, setAudioStatus] = useState<AudioStatus | null>(null)
  const [alerts, setAlerts] = useState<AlertEntry[]>([])
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [dashConfig, setDashConfig] = useState<DashboardConfig>({ marked_rate_green: BUILD_TIME_GREEN, marked_rate_yellow: BUILD_TIME_YELLOW })
  const [milestoneFired, setMilestoneFired] = useState<MilestoneFiredData | null>(null)
  const [milestoneConfig, setMilestoneConfig] = useState<MilestoneConfig | null>(null)
  // Edit-UI State für Milestone-Config
  const [mcEditMode, setMcEditMode] = useState(false)
  const [mcGlobalInput, setMcGlobalInput] = useState('')
  const [mcTagInput, setMcTagInput] = useState('')
  const [mcTagThresholdsInput, setMcTagThresholdsInput] = useState('')
  const [mcSaving, setMcSaving] = useState(false)
  const [mcError, setMcError] = useState('')
  const [mcSuccess, setMcSuccess] = useState('')
  const [downloadHistory, setDownloadHistory] = useState<DownloadHistoryData | null>(null)
  const [downloadCompare, setDownloadCompare] = useState<DownloadCompareData | null>(null)
  const [musicHealth, setMusicHealth] = useState<MusicHealthData | null>(null)
  const [scAlerts, setScAlerts] = useState<ScAlertsData | null>(null)
  const [scAlertsOffset, setScAlertsOffset] = useState(0)
  const [dlHistPage, setDlHistPage] = useState<Record<string, number>>({})
  const [focusedTag, setFocusedTag] = useState<string | null>(null)
  // aria-live Announcement für Screenreader (Tab-Fokus auf Tag-Sektion)
  const [dlAriaAnnouncement, setDlAriaAnnouncement] = useState<string>('')
  // Swipe-Touch-State für Download-History Tag-Navigation (pro Tag)
  const [dlSwipeStart, setDlSwipeStart] = useState<Record<string, { x: number; y: number } | null>>({})
  // Swipe-Feedback-Indikator: kurzer Opacity-Pulse nach erfolgreicher Navigation (150ms)
  const [dlSwipePulse, setDlSwipePulse] = useState<Record<string, boolean>>({})
  // Desktop-User-Agent Detection für Keyboard-Shortcut Hint im Pagination-Bereich
  const isDesktopUA = useMemo(() => !/Android|iPhone|iPad|iPod|Mobile|Tablet/i.test(navigator.userAgent), [])
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [swipeState, setSwipeState] = useState<Record<number, number>>({})
  const [dismissing, setDismissing] = useState<Set<number>>(new Set())
  // KIROBI_DL_HISTORY_REFRESH_S — dynamisch vom Backend (Standard: 15s)
  const [dlHistRefreshMs, setDlHistRefreshMs] = useState<number>(15000)
  // KIROBI_MUSIC_HEALTH_REFRESH_S — separater langsamerer Intervall für Music-Health (Standard: 30s)
  const [musicHealthRefreshMs, setMusicHealthRefreshMs] = useState<number>(30000)
  const base = useMemo(getBackendHttpBase, [])

  const refresh = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [sysRes, audioRes, alertsRes, dashRes, dashConfigRes, milestoneRes, dlHistRes, dlCompareRes, milestoneConfigRes, scAlertsRes] = await Promise.all([
        fetch(`${base}/api/system/status`, { cache: 'no-store' }),
        fetch(`${base}/api/status`, { cache: 'no-store' }),
        fetch(`${base}/api/alerts`, { cache: 'no-store' }),
        fetch(`${base}/api/dashboard`, { cache: 'no-store' }),
        fetch(`${base}/api/dashboard-config`, { cache: 'no-store' }),
        fetch(`${base}/api/milestone-fired`, { cache: 'no-store' }),
        fetch(`${base}/api/download-history`, { cache: 'no-store' }),
        fetch(`${base}/api/download-compare`, { cache: 'no-store' }),
        fetch(`${base}/api/milestone-config`, { cache: 'no-store' }),
        fetch(`${base}/api/sc-alerts?limit=5&offset=${scAlertsOffset}`, { cache: 'no-store' }),
      ])
      if (!sysRes.ok) throw new Error(`HTTP ${sysRes.status}`)
      setData(await sysRes.json())
      if (audioRes.ok) setAudioStatus(await audioRes.json())
      if (alertsRes.ok) {
        const alertData = await alertsRes.json()
        setAlerts((alertData.alerts ?? []).slice(0, 5))
      }
      if (dashRes.ok) setDashboard(await dashRes.json())
      if (dashConfigRes.ok) setDashConfig(await dashConfigRes.json())
      if (milestoneRes.ok) setMilestoneFired(await milestoneRes.json())
      if (milestoneConfigRes.ok) setMilestoneConfig(await milestoneConfigRes.json())
      if (dlHistRes.ok) setDownloadHistory(await dlHistRes.json())
      if (dlCompareRes.ok) setDownloadCompare(await dlCompareRes.json())
      if (scAlertsRes.ok) setScAlerts(await scAlertsRes.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [base, scAlertsOffset])

  const dismissAlert = useCallback(async (ts: number) => {
    setDismissing((prev) => new Set(prev).add(ts))
    try {
      await fetch(`${base}/api/alerts/${ts}`, { method: 'DELETE' })
      setAlerts((prev) => prev.filter((a) => a.ts !== ts))
    } catch {
      // ignore — nächster Refresh synchronisiert
    } finally {
      setDismissing((prev) => { const next = new Set(prev); next.delete(ts); return next })
      setSwipeState((prev) => { const next = { ...prev }; delete next[ts]; return next })
    }
  }, [base])

  // Milestone-Config: globale Thresholds speichern
  const saveMcGlobal = useCallback(async () => {
    setMcSaving(true); setMcError(''); setMcSuccess('')
    try {
      const milestones = mcGlobalInput.split(',').map((s) => parseInt(s.trim(), 10)).filter((n) => !isNaN(n) && n > 0)
      if (milestones.length === 0) { setMcError('Bitte gültige Komma-separierte Zahlen eingeben.'); setMcSaving(false); return }
      const res = await fetch(`${base}/api/milestone-config/global`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ milestones }),
      })
      if (!res.ok) { const d = await res.json(); setMcError(d.detail ?? `HTTP ${res.status}`); setMcSaving(false); return }
      setMcSuccess('✅ Globale Thresholds gespeichert')
      void refresh()
    } catch (e) { setMcError(e instanceof Error ? e.message : String(e)) }
    setMcSaving(false)
  }, [base, mcGlobalInput, refresh])

  // Milestone-Config: Tag-Override setzen
  const saveMcTag = useCallback(async () => {
    setMcSaving(true); setMcError(''); setMcSuccess('')
    try {
      const tag = mcTagInput.trim()
      if (!tag) { setMcError('Bitte Release-Tag eingeben.'); setMcSaving(false); return }
      const milestones = mcTagThresholdsInput.split(',').map((s) => parseInt(s.trim(), 10)).filter((n) => !isNaN(n) && n > 0)
      if (milestones.length === 0) { setMcError('Bitte gültige Thresholds eingeben.'); setMcSaving(false); return }
      const res = await fetch(`${base}/api/milestone-config/tags/${encodeURIComponent(tag)}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ milestones }),
      })
      if (!res.ok) { const d = await res.json(); setMcError(d.detail ?? `HTTP ${res.status}`); setMcSaving(false); return }
      setMcSuccess(`✅ Tag-Override für "${tag}" gespeichert`)
      setMcTagInput(''); setMcTagThresholdsInput('')
      void refresh()
    } catch (e) { setMcError(e instanceof Error ? e.message : String(e)) }
    setMcSaving(false)
  }, [base, mcTagInput, mcTagThresholdsInput, refresh])

  // Milestone-Config: Tag-Override löschen
  const deleteMcTag = useCallback(async (tag: string) => {
    setMcSaving(true); setMcError(''); setMcSuccess('')
    try {
      const res = await fetch(`${base}/api/milestone-config/tags/${encodeURIComponent(tag)}`, { method: 'DELETE' })
      if (!res.ok) { const d = await res.json(); setMcError(d.detail ?? `HTTP ${res.status}`); setMcSaving(false); return }
      setMcSuccess(`🗑️ Override für "${tag}" entfernt`)
      void refresh()
    } catch (e) { setMcError(e instanceof Error ? e.message : String(e)) }
    setMcSaving(false)
  }, [base, refresh])

  // Swipe-Geste: translateX tracking per Alert-ts
  const handleTouchStart = useCallback((ts: number, e: React.TouchEvent) => {
    setSwipeState((prev) => ({ ...prev, [ts]: e.touches[0].clientX }))
  }, [])

  const handleTouchMove = useCallback((ts: number, e: React.TouchEvent) => {
    const startX = swipeState[ts]
    if (startX == null) return
    const delta = e.touches[0].clientX - startX
    if (delta < -60) {
      void dismissAlert(ts)
    }
  }, [swipeState, dismissAlert])

  // Lade Refresh-Interval-Config einmalig vom Backend (KIROBI_DL_HISTORY_REFRESH_S ENV).
  // Separater Effect damit dlHistRefreshMs-Änderung den Interval neu startet.
  useEffect(() => {
    fetch(`${base}/api/download-history-config`, { cache: 'no-store' })
      .then((r) => r.ok ? r.json() : null)
      .then((cfg) => { if (cfg?.refresh_s) setDlHistRefreshMs(Math.max(5000, cfg.refresh_s * 1000)) })
      .catch(() => { /* Fallback: 15000 bleibt */ })
  }, [base])

  // Music-Health Refresh-Config laden (KIROBI_MUSIC_HEALTH_REFRESH_S ENV, Standard: 30s).
  useEffect(() => {
    fetch(`${base}/api/music-health-config`, { cache: 'no-store' })
      .then((r) => r.ok ? r.json() : null)
      .then((cfg) => { if (cfg?.refresh_s) setMusicHealthRefreshMs(Math.max(10000, cfg.refresh_s * 1000)) })
      .catch(() => { /* Fallback: 30000 bleibt */ })
  }, [base])

  // Separater Callback für Music-Health-Polling (langsamerer Intervall).
  const refreshMusicHealth = useCallback(async () => {
    try {
      const res = await fetch('http://127.0.0.1:8013/health', { cache: 'no-store' })
      if (res.ok) setMusicHealth(await res.json())
    } catch {
      // Service nicht verfügbar — kein Update
    }
  }, [])

  // Music-Health Polling-Interval: separater, langsamerer Intervall (Standard: 30s).
  useEffect(() => {
    void refreshMusicHealth()
    const timer = window.setInterval(refreshMusicHealth, musicHealthRefreshMs)
    return () => window.clearInterval(timer)
  }, [refreshMusicHealth, musicHealthRefreshMs])

  // Polling-Interval: reagiert auf dlHistRefreshMs-Änderungen (z.B. nach Config-Load)
  useEffect(() => {
    void refresh()
    const timer = window.setInterval(refresh, dlHistRefreshMs)
    return () => window.clearInterval(timer)
  }, [refresh, base, dlHistRefreshMs])

  // Keyboard-Support: ArrowLeft/ArrowRight navigiert Download-History Pages (Desktop-Browsertest)
  // Pro-Tag-Modus: nur der per Tab fokussierte Tag wird navigiert; wenn kein Tag fokussiert → globale Navigation
  useEffect(() => {
    if (!downloadHistory) return
    const tags = Object.keys(downloadHistory.tags)
    if (tags.length === 0) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
      // Nur wenn kein Input/Textarea fokussiert
      const active = document.activeElement
      if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT')) return

      e.preventDefault()
      // Pro-Tag: fokussierten Tag navigieren; sonst alle Tags global
      const targetTags = focusedTag ? [focusedTag] : tags
      setDlHistPage((prev) => {
        const next = { ...prev }
        targetTags.forEach((tag) => {
          const snaps = downloadHistory.tags[tag].snapshots
          const PAGE_SIZE = 8
          const totalPages = Math.max(1, Math.ceil(snaps.length / PAGE_SIZE))
          const current = Math.min(prev[tag] ?? 0, totalPages - 1)
          if (e.key === 'ArrowLeft') {
            next[tag] = current < totalPages - 1 ? current + 1 : current
          } else {
            next[tag] = current > 0 ? current - 1 : current
          }
        })
        return next
      })
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [downloadHistory, focusedTag])

  // Swipe-Touch-Handler für Download-History Tag-Navigation
  // SWIPE_MIN_DISTANCE=50px | vertikaler Scroll-Schutz (SWIPE_MAX_VERTICAL=80px) | Pro-Tag
  const SWIPE_MIN_DISTANCE = 50
  const SWIPE_MAX_VERTICAL = 80

  const handleDlTouchStart = useCallback((tag: string, e: React.TouchEvent) => {
    const t = e.touches[0]
    setDlSwipeStart((prev) => ({ ...prev, [tag]: { x: t.clientX, y: t.clientY } }))
  }, [])

  const handleDlTouchEnd = useCallback((tag: string, e: React.TouchEvent) => {
    const start = dlSwipeStart[tag]
    if (!start) return
    const t = e.changedTouches[0]
    const dx = t.clientX - start.x
    const dy = Math.abs(t.clientY - start.y)
    // Scroll-Schutz: vertikale Gesten ignorieren
    if (dy > SWIPE_MAX_VERTICAL) {
      setDlSwipeStart((prev) => ({ ...prev, [tag]: null }))
      return
    }
    if (Math.abs(dx) < SWIPE_MIN_DISTANCE) {
      setDlSwipeStart((prev) => ({ ...prev, [tag]: null }))
      return
    }
    setDlHistPage((prev) => {
      if (!downloadHistory) return prev
      const snaps = downloadHistory.tags[tag]?.snapshots ?? []
      const PAGE_SIZE = 8
      const totalPages = Math.max(1, Math.ceil(snaps.length / PAGE_SIZE))
      const current = Math.min(prev[tag] ?? 0, totalPages - 1)
      let next = current
      if (dx < 0) {
        // Swipe links → ältere Seite (pageIdx++)
        next = current < totalPages - 1 ? current + 1 : current
      } else {
        // Swipe rechts → neuere Seite (pageIdx--)
        next = current > 0 ? current - 1 : current
      }
      // Pulse-Feedback auslösen wenn Navigation erfolgte
      if (next !== current) {
        setDlSwipePulse((p) => ({ ...p, [tag]: true }))
        setTimeout(() => {
          setDlSwipePulse((p) => ({ ...p, [tag]: false }))
        }, 150)
      }
      return { ...prev, [tag]: next }
    })
    setDlSwipeStart((prev) => ({ ...prev, [tag]: null }))
  }, [dlSwipeStart, downloadHistory])

  const gpu = data?.gpu

  return (
    <section className="systemModule">
      <div className="systemHeader">
        <div>
          <div className="systemEyebrow">Live Ops</div>
          <h1 className="systemTitle">System Monitor</h1>
        </div>
        <button className="systemRefresh" type="button" onClick={refresh} disabled={loading}>
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {error && <div className="systemError">Backend nicht erreichbar: {error}</div>}

      {audioStatus && <AudioStatusPanel audioStatus={audioStatus} />}

      {alerts.length > 0 && (
        <AlertHistoryPanel
          alerts={alerts}
          dismissing={dismissing}
          onDismiss={(ts) => void dismissAlert(ts)}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
        />
      )}

      {dashboard && <DashboardPanel dashboard={dashboard} dashConfig={dashConfig} />}

      {dashboard?.sc_trend && <ScTrendPanel scTrend={dashboard.sc_trend} />}

      {(milestoneFired || milestoneConfig) && (
        <MilestoneFiredPanel milestoneFired={milestoneFired} milestoneConfig={milestoneConfig} />
      )}

      {/* Milestone-Config Edit-UI */}
      {milestoneConfig && (
        <MilestoneConfigPanel
          milestoneConfig={milestoneConfig}
          mcEditMode={mcEditMode}
          mcGlobalInput={mcGlobalInput}
          mcTagInput={mcTagInput}
          mcTagThresholdsInput={mcTagThresholdsInput}
          mcSaving={mcSaving}
          mcError={mcError}
          mcSuccess={mcSuccess}
          onToggleEdit={() => { setMcEditMode((v) => !v); setMcError(''); setMcSuccess('') }}
          onGlobalInputChange={setMcGlobalInput}
          onTagInputChange={setMcTagInput}
          onTagThresholdsInputChange={setMcTagThresholdsInput}
          onSaveGlobal={() => void saveMcGlobal()}
          onSaveTag={() => void saveMcTag()}
          onDeleteTag={(tag) => void deleteMcTag(tag)}
        />
      )}

      {downloadHistory && Object.keys(downloadHistory.tags).length > 0 && (
        <DownloadHistoryPanel
          downloadHistory={downloadHistory}
          dlHistPage={dlHistPage}
          focusedTag={focusedTag}
          dlAriaAnnouncement={dlAriaAnnouncement}
          dlSwipePulse={dlSwipePulse}
          isDesktopUA={isDesktopUA}
          onPageChange={(tag, page) => setDlHistPage((p) => ({ ...p, [tag]: page }))}
          onFocus={(tag) => {
            setFocusedTag(tag)
            const totalPages = Math.max(1, Math.ceil((downloadHistory?.tags[tag]?.snapshots?.length ?? 0) / 8))
            const currentPage = Math.min(dlHistPage[tag] ?? 0, totalPages - 1)
            setDlAriaAnnouncement(`Download-Verlauf für ${tag}, Seite ${currentPage + 1} von ${totalPages}`)
          }}
          onBlur={() => { setFocusedTag(null); setDlAriaAnnouncement('') }}
          onTouchStart={handleDlTouchStart}
          onTouchEnd={handleDlTouchEnd}
        />
      )}

      {downloadCompare && downloadCompare.tags.length > 0 && downloadCompare.weeks.length > 0 && (
        <DownloadComparePanel downloadCompare={downloadCompare} />
      )}

      {musicHealth && <MusicHealthBadgePanel musicHealth={musicHealth} />}

      {/* SC-Alert-History Panel — /api/sc-alerts */}
      <ScAlertsPanel
        scAlerts={scAlerts?.alerts ?? []}
        total={scAlerts?.total ?? 0}
        offset={scAlertsOffset}
        hasMore={scAlerts?.has_more ?? false}
        onPrev={() => setScAlertsOffset((prev) => Math.max(0, prev - 5))}
        onNext={() => setScAlertsOffset((prev) => prev + 5)}
      />

      {/* Music-Health Config Panel — /api/music-health-config Refresh-Interval anzeigen + live editieren */}
      <MusicHealthConfigPanel base={base} musicHealthRefreshMs={musicHealthRefreshMs} onRefreshMsChange={(_ms) => {}} />

      {gpu && <GpuPanel gpu={gpu} />}

      <ServicesGridPanel services={data?.services ?? []} />

      <LiveLogsPanel base={base} />
    </section>
  )
}
