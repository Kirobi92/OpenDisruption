/**
 * Unit-Tests: SystemModule — Download-History Panel
 * Vitest + @testing-library/react (Snapshot-Tests)
 *
 * Testszenarien:
 *   1. Leere History — Panel nicht sichtbar (tags leer)
 *   2. 1 Eintrag — Panel sichtbar, Tag-Label + total + trend korrekt
 *   3. Volle History (>8 Snapshots) — Pagination-Dots + Ältere/Neuere Buttons sichtbar
 *
 * Alle Fetch-Calls werden gemockt:
 *   - /api/status → minimal
 *   - /api/alerts → leer
 *   - /api/download-history → gemockt (je Szenario)
 *   - /api/download-history-config → minimal
 *   - /api/milestone-config → minimal
 *   - /api/music-health → minimal
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import SystemModule from '../modules/system/SystemModule'

// ─── Mock: agentStore ─────────────────────────────────────────────────────────
vi.mock('../stores/agentStore', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../stores/agentStore')>()
  return {
    ...actual,
    getBackendHttpBase: () => 'http://localhost:8765',
    // useAgentStore falls verwendet — stubs
    useAgentStore: (selector: (s: object) => unknown) => {
      const stub = {
        state: 'idle',
        connectionState: 'disconnected',
        inputMode: 'auto',
        backendMode: 'lan',
        customHost: '',
        setBackendMode: vi.fn(),
        setCustomHost: vi.fn(),
      }
      return selector ? selector(stub) : stub
    },
  }
})

// ─── Fetch-Mock Infrastruktur ─────────────────────────────────────────────────
const mockFetch = vi.fn()

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch)
})

afterEach(() => {
  vi.restoreAllMocks()
  mockFetch.mockReset()
})

// Helper: gültige JSON-Response
function jsonResponse(body: object, ok = true) {
  return Promise.resolve({
    ok,
    json: () => Promise.resolve(body),
  } as Response)
}

// ─── Basis-Mock-Antworten ─────────────────────────────────────────────────────
// /api/system/status — SystemData (sysRes)
const systemStatusOk = {
  running: true,
  mode: 'idle',
  audio_idle_limit_s: 30,
  idle_limit_mode: 'day',
  gpu_memory_mb: 0,
  queue_size: 0,
  uptime_s: 0,
}
// /api/status — AudioStatus (audioRes)
const audioStatusOk = {
  active_connections: 0,
  idle_s: 0,
  last_connection_ts: null,
  status: 'ok',
  idle_limit_mode: 'day',
}
const alertsEmpty = { alerts: [] }
const dashboardEmpty = {
  trend: 'stable',
  latest_assessment: '',
  avg_marked_rate: 0,
  min_marked_rate: 0,
  max_marked_rate: 0,
  snapshots_total: 0,
  snapshots: [],
}
const dashboardConfig = {}
const milestoneFired = { fired: {} }
const downloadHistoryConfig = { refresh_s: 15 }
const milestoneConfig = { config: { global: {}, tag_overrides: {}, global_milestones: [] }, tags: {} }
const downloadCompareEmpty = { status: 'ok', tags: [], weeks: [], matrix: {}, tag_totals: {}, ts: Date.now() }
const musicHealth = { status: 'ok', service: 'music-generation', port: 8790, database: { ok: true }, ollama: { reachable: true }, audiocraft: { available: true }, heartmula: { available: true, model_exists: true } }
const musicHealthConfig = { refresh_s: 30, source: 'default' }

// Download-History Fixtures
function makeSnapshot(week: string, total: number, debug: number, release: number) {
  return { week, total, debug_downloads: debug, release_downloads: release }
}

const emptyHistory = { status: 'ok', schema_version: '1', tags: {}, ts: Date.now() }

const oneEntryHistory = {
  status: 'ok',
  schema_version: '1',
  tags: {
    'v14-debug': {
      snapshots: [makeSnapshot('2026-W20', 42, 30, 12)],
      total_downloads: 42,
      sparkline: '',
      trend: '↗',
      latest_week: '2026-W20',
      latest_debug: 30,
      latest_release: 12,
    },
  },
  ts: Date.now(),
}

// Volle History: 10 Snapshots (>8 → Pagination)
function buildFullHistory() {
  const snapshots = Array.from({ length: 10 }, (_, i) =>
    makeSnapshot(`2026-W${10 + i}`, 100 + i * 5, 60 + i * 3, 40 + i * 2)
  )
  return {
    status: 'ok',
    schema_version: '1',
    tags: {
      'v16-debug': {
        snapshots,
        total_downloads: 1000,
        sparkline: '',
        trend: '↗↗',
        latest_week: '2026-W19',
        latest_debug: 87,
        latest_release: 53,
      },
    },
    ts: Date.now(),
  }
}

// Fetch-Dispatcher: gibt je nach URL die passende Response zurück
function setupFetchMock(downloadHistoryData: object) {
  mockFetch.mockImplementation((url: string) => {
    if (url.includes('/api/system/status')) return jsonResponse(systemStatusOk)
    if (url.includes('/api/status')) return jsonResponse(audioStatusOk)
    if (url.includes('/api/alerts/')) return jsonResponse({}) // DELETE single alert
    if (url.includes('/api/alerts')) return jsonResponse(alertsEmpty)
    if (url.includes('/api/dashboard-config')) return jsonResponse(dashboardConfig)
    if (url.includes('/api/dashboard')) return jsonResponse(dashboardEmpty)
    if (url.includes('/api/milestone-fired')) return jsonResponse(milestoneFired)
    if (url.includes('/api/download-history-config')) return jsonResponse(downloadHistoryConfig)
    if (url.includes('/api/download-compare')) return jsonResponse(downloadCompareEmpty)
    if (url.includes('/api/download-history')) return jsonResponse(downloadHistoryData)
    if (url.includes('/api/milestone-config')) return jsonResponse(milestoneConfig)
    if (url.includes('/api/music-health-config')) return jsonResponse(musicHealthConfig)
    if (url.includes('/api/music-health')) return jsonResponse(musicHealth)
    if (url.includes('/health')) return jsonResponse(musicHealth)  // http://127.0.0.1:8013/health
    // Fallback: leere 200-Antwort
    return jsonResponse({})
  })
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('SystemModule — Download-History Panel', () => {
  it('1. Leere History — Panel "📥 APK Download-History" nicht sichtbar', async () => {
    setupFetchMock(emptyHistory)

    await act(async () => {
      render(<SystemModule />)
    })

    // Panel-Überschrift darf NICHT sichtbar sein bei leeren tags
    expect(screen.queryByText('📥 APK Download-History')).toBeNull()
  })

  it('2. 1 Eintrag — Panel sichtbar, Tag + Gesamtzahl + Trend korrekt', async () => {
    setupFetchMock(oneEntryHistory)

    await act(async () => {
      render(<SystemModule />)
    })

    await waitFor(() => {
      expect(screen.getByText('📥 APK Download-History')).toBeTruthy()
    })

    // Tag-Label
    expect(screen.getByText('v14-debug')).toBeTruthy()
    // Gesamtanzahl + Trend (kombinierter Text)
    expect(screen.getByText(/42 total ↗/)).toBeTruthy()
    // Debug / Release Stats
    expect(screen.getByText(/Debug: 30/)).toBeTruthy()
    expect(screen.getByText(/Release: 12/)).toBeTruthy()
  })

  it('2b. Snapshot-Test: 1 Eintrag — gerenderter Container stimmt mit Snapshot überein', async () => {
    setupFetchMock(oneEntryHistory)

    let container: HTMLElement | undefined

    await act(async () => {
      const result = render(<SystemModule />)
      container = result.container
    })

    await waitFor(() => {
      expect(screen.getByText('📥 APK Download-History')).toBeTruthy()
    })

    // Snapshot des Download-History-Panels
    const panel = container!.querySelector('.gpuPanel')
    expect(panel).toBeTruthy()
    expect(panel!.innerHTML).toMatchSnapshot()
  })

  it('3. Volle History (10 Snapshots) — Pagination-Buttons sichtbar', async () => {
    setupFetchMock(buildFullHistory())

    await act(async () => {
      render(<SystemModule />)
    })

    await waitFor(() => {
      expect(screen.getByText('📥 APK Download-History')).toBeTruthy()
    })

    // Tag v16-debug
    expect(screen.getByText('v16-debug')).toBeTruthy()
    // 10 Snapshots > PAGE_SIZE 8 → Pagination-Buttons müssen existieren
    expect(screen.getByLabelText('Ältere Einträge')).toBeTruthy()
    // Seite 0 (neueste) = kann nicht vorwärts
    // Bullet-Dots: tablist mit aria-label "Seite 1 von 2"
    expect(screen.getByRole('tablist', { name: /Seite 1 von 2/ })).toBeTruthy()
    // 2 Seiten = 2 Bullet-Dots
    const dots = screen.getAllByRole('tab')
    expect(dots.length).toBe(2)
    // Aktueller Dot (Seite 0) ist selected
    expect(dots[0].getAttribute('aria-selected')).toBe('true')
  })

  it('3b. Snapshot-Test: Volle History — gerenderter Container stimmt mit Snapshot überein', async () => {
    setupFetchMock(buildFullHistory())

    let container: HTMLElement | undefined

    await act(async () => {
      const result = render(<SystemModule />)
      container = result.container
    })

    await waitFor(() => {
      expect(screen.getByText('📥 APK Download-History')).toBeTruthy()
    })

    const panel = container!.querySelector('.gpuPanel')
    expect(panel).toBeTruthy()
    expect(panel!.innerHTML).toMatchSnapshot()
  })
})
