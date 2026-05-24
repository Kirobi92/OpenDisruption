/**
 * Unit-Tests: SystemModule Sub-Komponenten (GpuPanel, ServicesGridPanel, LiveLogsPanel)
 * 
 * Testszenarien GpuPanel:
 *   1. GPU verfügbar → VRAM, Temperatur, Last werden angezeigt
 *   2. GPU nicht verfügbar → Fehlermeldung wird angezeigt
 *   3. GPU verfügbar mit fehlenden optionalen Feldern → keine Crash
 *
 * Testszenarien ServicesGridPanel:
 *   4. Leere Service-Liste → kein Crash, Grid leer
 *   5. Einzelner Service ONLINE → korrekte Anzeige
 *   6. Einzelner Service DOWN → DOWN-Pill, rote Klasse
 *   7. Mehrere Services gemischt → alle gerendert
 *   8. Service mit Port → Port angezeigt
 *   9. Service ohne Port → "systemd" angezeigt
 *  10. Service mit Latenz → Latenz in ms angezeigt
 *  11. Service mit detail → detail angezeigt
 *
 * Testszenarien LiveLogsPanel:
 *  12. Initial-Render: Service-Selector + Button + Platzhalter
 *  13. Service-Selector hat 4 Optionen
 *  14. Button togglet "Stream starten" ↔ "Stop"
 *  15. Log-Bereich initial mit Platzhalter-Text
 *  16. Stop schließt EventSource
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { GpuPanel } from '../modules/system/GpuPanel'
import { ServicesGridPanel } from '../modules/system/ServicesGridPanel'
import { LiveLogsPanel } from '../modules/system/LiveLogsPanel'
import { GpuStatus, ServiceStatus } from '../modules/system/types'

// ─── EventSource Mock für LiveLogsPanel ────────────────────────────────────────
// vitest 4.x: vi.fn() mit arrow ist nicht constructable → function nutzen

const mockEventSourceCtor = vi.fn(function (this: any, _url: string) {
  return mockEventSourceInstance
})
let mockEventSourceInstance: { close: ReturnType<typeof vi.fn>; onmessage: Function | null; onerror: Function | null }

beforeEach(() => {
  mockEventSourceInstance = {
    close: vi.fn(),
    onmessage: null,
    onerror: null,
  }
  vi.stubGlobal('EventSource', mockEventSourceCtor)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

// ─── Fixtures ──────────────────────────────────────────────────────────────────

function makeGpuAvailable(overrides: Partial<GpuStatus> = {}): GpuStatus {
  return {
    available: true,
    memory_used_mb: 8192,
    memory_total_mb: 24576,
    temperature_c: 62,
    utilization_pct: 45,
    ...overrides,
  }
}

function makeGpuUnavailable(error?: string): GpuStatus {
  return {
    available: false,
    error: error || 'nvidia-smi nicht gefunden',
  }
}

function makeService(overrides: Partial<ServiceStatus> = {}): ServiceStatus {
  return {
    name: 'paperclip',
    port: 3100,
    status: 'ok',
    url: 'http://localhost:3100',
    detail: 'Paperclip API v2026.517.0',
    latency_ms: 12,
    ...overrides,
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// GPU PANEL
// ═══════════════════════════════════════════════════════════════════════════════

describe('GpuPanel', () => {
  it('GPU verfügbar → VRAM, Temperatur, Last werden angezeigt', () => {
    const gpu = makeGpuAvailable()
    render(<GpuPanel gpu={gpu} />)

    expect(screen.getByText('RTX 3090 / GPU')).toBeTruthy()
    expect(screen.getByText(/8192 \/ 24576 MB/)).toBeTruthy()
    expect(screen.getByText(/62 °C/)).toBeTruthy()
    expect(screen.getByText(/45 %/)).toBeTruthy()
  })

  it('GPU nicht verfügbar → Fehlermeldung mit error-Text', () => {
    const gpu = makeGpuUnavailable('nvidia-smi nicht gefunden')
    render(<GpuPanel gpu={gpu} />)

    expect(screen.getByText('RTX 3090 / GPU')).toBeTruthy()
    expect(screen.getByText(/GPU-Daten nicht verfügbar/)).toBeTruthy()
    expect(screen.getByText(/nvidia-smi nicht gefunden/)).toBeTruthy()
    // Keine GPU-Detail-Zeilen
    expect(screen.queryByText(/MB/)).toBeNull()
  })

  it('GPU verfügbar mit fehlenden optionalen Feldern → kein Crash', () => {
    const gpu: GpuStatus = { available: true }
    render(<GpuPanel gpu={gpu} />)

    // GPU-Header immer sichtbar
    expect(screen.getByText('RTX 3090 / GPU')).toBeTruthy()
    // VRAM-Zeile zeigt undefined/undefined — aber kein Crash
    expect(screen.getByText(/\/ MB$/)).toBeTruthy()
  })

  it('GPU verfügbar mit 0-Werten → zeigt korrekt 0', () => {
    const gpu = makeGpuAvailable({
      memory_used_mb: 0,
      temperature_c: 0,
      utilization_pct: 0,
    })
    render(<GpuPanel gpu={gpu} />)

    expect(screen.getByText(/0 \/ 24576 MB/)).toBeTruthy()
    expect(screen.getByText(/0 °C/)).toBeTruthy()
    expect(screen.getByText(/0 %/)).toBeTruthy()
  })

  it('GPU nicht verfügbar ohne error-Text → zeigt leere Fehlermeldung', () => {
    const gpu: GpuStatus = { available: false }
    render(<GpuPanel gpu={gpu} />)

    expect(screen.getByText(/GPU-Daten nicht verfügbar/)).toBeTruthy()
    // Kein Crash bei undefined error
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// SERVICES GRID PANEL
// ═══════════════════════════════════════════════════════════════════════════════

describe('ServicesGridPanel', () => {
  it('Leere Service-Liste → kein Crash, Grid-Container vorhanden', () => {
    render(<ServicesGridPanel services={[]} />)

    const grid = document.querySelector('.systemGrid')
    expect(grid).not.toBeNull()
    const cards = document.querySelectorAll('.systemCard')
    expect(cards).toHaveLength(0)
  })

  it('Einzelner Service ONLINE → korrekte Anzeige', () => {
    const svc = makeService({ name: 'paperclip', status: 'ok', port: 3100 })
    render(<ServicesGridPanel services={[svc]} />)

    expect(screen.getByText('paperclip')).toBeTruthy()
    expect(screen.getByText(':3100')).toBeTruthy()
    expect(screen.getByText('ONLINE')).toBeTruthy()
    expect(screen.getByText('Paperclip API v2026.517.0')).toBeTruthy()
    expect(screen.getByText('12 ms')).toBeTruthy()
  })

  it('Einzelner Service DOWN → DOWN-Pill', () => {
    const svc = makeService({ name: 'comfyui', status: 'down', port: 8188 })
    render(<ServicesGridPanel services={[svc]} />)

    expect(screen.getByText('comfyui')).toBeTruthy()
    expect(screen.getByText(':8188')).toBeTruthy()
    expect(screen.getByText('DOWN')).toBeTruthy()
    // systemCard soll die CSS-Klasse 'down' haben
    const card = document.querySelector('.systemCard')
    expect(card?.classList.contains('down')).toBe(true)
  })

  it('Mehrere Services gemischt (ok+down) → alle gerendert', () => {
    const services: ServiceStatus[] = [
      makeService({ name: 'paperclip', status: 'ok', port: 3100 }),
      makeService({ name: 'comfyui', status: 'down', port: 8188 }),
      makeService({ name: 'hermes', status: 'ok', port: null }),
    ]
    render(<ServicesGridPanel services={services} />)

    const cards = document.querySelectorAll('.systemCard')
    expect(cards).toHaveLength(3)
    expect(screen.getByText('paperclip')).toBeTruthy()
    expect(screen.getByText('comfyui')).toBeTruthy()
    expect(screen.getByText('hermes')).toBeTruthy()

    // Status-Pills
    const onlinePills = screen.getAllByText('ONLINE')
    const downPills = screen.getAllByText('DOWN')
    expect(onlinePills).toHaveLength(2)
    expect(downPills).toHaveLength(1)
  })

  it('Service ohne Port → zeigt "systemd"', () => {
    const svc = makeService({ name: 'kirobi-backend', port: null })
    render(<ServicesGridPanel services={[svc]} />)

    expect(screen.getByText('systemd')).toBeTruthy()
    expect(screen.queryByText(/^:\d/)).toBeNull()
  })

  it('Service mit Latenz → Latenz in ms angezeigt', () => {
    const svc = makeService({ latency_ms: 42 })
    render(<ServicesGridPanel services={[svc]} />)

    expect(screen.getByText('42 ms')).toBeTruthy()
  })

  it('Service ohne Latenz → keine ms-Anzeige', () => {
    const svc = makeService({ latency_ms: null })
    render(<ServicesGridPanel services={[svc]} />)

    expect(screen.queryByText(/ms/)).toBeNull()
  })

  it('Service mit detail → detail wird angezeigt', () => {
    const svc = makeService({ detail: 'Running v2.1.0' })
    render(<ServicesGridPanel services={[svc]} />)

    expect(screen.getByText('Running v2.1.0')).toBeTruthy()
  })

  it('Service ohne detail und ohne url → zeigt "bereit"', () => {
    const svc: ServiceStatus = {
      name: 'minimal-svc',
      port: null,
      status: 'ok',
    }
    render(<ServicesGridPanel services={[svc]} />)

    expect(screen.getByText('bereit')).toBeTruthy()
  })

  it('Service mit url aber ohne detail → zeigt url', () => {
    const svc: ServiceStatus = {
      name: 'api-svc',
      port: 9000,
      status: 'ok',
      url: 'http://localhost:9000',
    }
    render(<ServicesGridPanel services={[svc]} />)

    expect(screen.getByText('http://localhost:9000')).toBeTruthy()
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// LIVE LOGS PANEL
// ═══════════════════════════════════════════════════════════════════════════════

describe('LiveLogsPanel', () => {
  const base = 'http://localhost:8765'

  it('Initial-Render: Service-Selector, Button, Platzhalter-Text', () => {
    render(<LiveLogsPanel base={base} />)

    expect(screen.getByText('Live Logs')).toBeTruthy()
    expect(screen.getByRole('combobox')).toBeTruthy()
    expect(screen.getByRole('button', { name: /stream starten/i })).toBeTruthy()
    expect(screen.getByText(/noch kein logstream aktiv/i)).toBeTruthy()
  })

  it('Service-Selector hat alle 4 Optionen', () => {
    render(<LiveLogsPanel base={base} />)

    const select = screen.getByRole('combobox') as HTMLSelectElement
    const options = Array.from(select.options).map((o) => o.value)
    expect(options).toEqual(['kirobi-backend', 'kirobi-frontend', 'comfyui', 'hermes'])
  })

  it('Button-Text togglet bei Klick: "Stream starten" → "Stop"', () => {
    render(<LiveLogsPanel base={base} />)

    const btn = screen.getByRole('button', { name: /stream starten/i })
    fireEvent.click(btn)

    // EventSource sollte erstellt worden sein
    expect(mockEventSourceCtor).toHaveBeenCalledWith(
      `${base}/api/system/logs/kirobi-backend`
    )
    // Button-Text wechselt
    expect(screen.getByRole('button', { name: /stop/i })).toBeTruthy()
  })

  it('Stop schließt EventSource und Button wechselt zurück', () => {
    render(<LiveLogsPanel base={base} />)

    // Starten
    fireEvent.click(screen.getByRole('button', { name: /stream starten/i }))
    expect(mockEventSourceCtor).toHaveBeenCalledTimes(1)

    // Stoppen
    fireEvent.click(screen.getByRole('button', { name: /stop/i }))
    // close wird 2x aufgerufen: stopStream() + useEffect-Cleanup (source.close())
    expect(mockEventSourceInstance.close).toHaveBeenCalled()
    // Button zurück
    expect(screen.getByRole('button', { name: /stream starten/i })).toBeTruthy()
  })

  it('Service-Wechsel während Stream läuft → schließt alten Stream, öffnet neuen', () => {
    render(<LiveLogsPanel base={base} />)

    // Stream starten
    fireEvent.click(screen.getByRole('button', { name: /stream starten/i }))
    expect(mockEventSourceCtor).toHaveBeenCalledWith(
      `${base}/api/system/logs/kirobi-backend`
    )

    // Service wechseln
    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'comfyui' } })

    // Alter Stream geschlossen
    expect(mockEventSourceInstance.close).toHaveBeenCalled()

    // Neuer Stream (EventSource wird durch Effect neu erstellt)
    // Da der erste Mock bereits konsumiert wurde, prüfen wir den zweiten Call
    expect(mockEventSourceCtor).toHaveBeenCalledTimes(2)
    expect(mockEventSourceCtor).toHaveBeenLastCalledWith(
      `${base}/api/system/logs/comfyui`
    )
  })

  it('EventSource onmessage → Log-Lines werden gerendert', () => {
    render(<LiveLogsPanel base={base} />)

    fireEvent.click(screen.getByRole('button', { name: /stream starten/i }))

    // Simuliere eingehende Nachrichten
    const handler = mockEventSourceInstance.onmessage
    expect(handler).not.toBeNull()

    act(() => {
      handler!({ data: JSON.stringify({ line: '[INFO] Server started' }) } as MessageEvent)
    })
    expect(screen.getByText(/\[INFO\] Server started/)).toBeTruthy()

    // Sende weitere Nachricht
    act(() => {
      handler!({ data: JSON.stringify({ line: '[WARN] High memory usage' }) } as MessageEvent)
    })
    expect(screen.getByText(/\[WARN\] High memory usage/)).toBeTruthy()
  })

  it('EventSource onmessage mit nicht-JSON → raw data als Log-Zeile', () => {
    render(<LiveLogsPanel base={base} />)

    fireEvent.click(screen.getByRole('button', { name: /stream starten/i }))

    const handler = mockEventSourceInstance.onmessage
    act(() => {
      handler!({ data: 'Plain text log line' } as MessageEvent)
    })
    expect(screen.getByText('Plain text log line')).toBeTruthy()
  })

  it('EventSource onerror → zeigt Trennungs-Meldung', () => {
    render(<LiveLogsPanel base={base} />)

    fireEvent.click(screen.getByRole('button', { name: /stream starten/i }))

    const handler = mockEventSourceInstance.onerror
    expect(handler).not.toBeNull()
    act(() => {
      handler!(new Event('error'))
    })

    expect(screen.getByText(/SSE getrennt oder Service nicht erlaubt/)).toBeTruthy()
  })

  it('Log-Bereich initial mit Platzhalter-Text', () => {
    render(<LiveLogsPanel base={base} />)

    const pre = document.querySelector('pre')
    expect(pre?.textContent).toContain('Noch kein Logstream aktiv.')
  })

  it('base-Prop wird korrekt für EventSource-URL verwendet', () => {
    const customBase = 'https://remote.example.com'

    render(<LiveLogsPanel base={customBase} />)
    fireEvent.click(screen.getByRole('button', { name: /stream starten/i }))

    expect(mockEventSourceCtor).toHaveBeenCalledWith(
      `${customBase}/api/system/logs/kirobi-backend`
    )
  })
})
