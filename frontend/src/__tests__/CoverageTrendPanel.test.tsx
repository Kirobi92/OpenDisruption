/**
 * Unit-Tests: CoverageTrendPanel (Vitest + @testing-library/react)
 *
 * Testszenarien:
 *   1. Rendering mit 0 entries → keine Sparklines, Badges sichtbar
 *   2. Rendering mit 5 entries → Sparklines, Badges, Tabelle
 *   3. Rendering mit 10 entries → alle Features mit mehr Daten
 *   4. Leere Daten (available=false) → Fehler/Leer-Meldung
 *   5. summary=null → „Keine Summary-Daten"
 *   6. Trend-Pfeile validieren (▲ verbessernd, ▼ fallend)
 *   7. Sparklines prüfen (SVG-Elemente vorhanden wenn entries >= 2)
 *   8. Tabelle mit Min/Max/Ø — Werte korrekt
 *   9. Sync-Button: onSync wird aufgerufen, disabled bei syncing
 *  10. syncResult: ok/ok_zero/no_data/error States
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CoverageTrendPanel } from '../modules/system/CoverageTrendPanel'
import { CoverageTrendData, CoverageTrendEntry, CoverageTrendMetric } from '../modules/system/types'

// ─── Test-Fixtures ─────────────────────────────────────────────────────────────

function makeMetric(overrides: Partial<CoverageTrendMetric> = {}): CoverageTrendMetric {
  return {
    direction: '►',
    delta: 0,
    interpretation: 'stabil',
    latest: 65,
    min: 60,
    max: 70,
    avg_last_5: 64.5,
    ...overrides,
  }
}

function makeEntry(overrides: Partial<CoverageTrendEntry> = {}): CoverageTrendEntry {
  return {
    run_id: 1000,
    started_at: '2026-05-25T10:00:00Z',
    conclusion: 'success',
    head_sha: 'abc123def456',
    statements_pct: 65,
    branches_pct: 45,
    functions_pct: 70,
    lines_pct: 68,
    synced_at: '2026-05-25T10:05:00Z',
    ...overrides,
  }
}

function makeCoverageData(overrides: Partial<CoverageTrendData> = {}): CoverageTrendData {
  return {
    available: true,
    entries: [],
    summary: {
      total_runs: 0,
      latest: null,
      statements_trend: makeMetric({ direction: '►', delta: 0, latest: 65, interpretation: 'stabil' }),
      branches_trend: makeMetric({ direction: '►', delta: 0, latest: 45, interpretation: 'stabil' }),
      functions_trend: makeMetric({ direction: '►', delta: 0, latest: 70, interpretation: 'stabil' }),
      lines_trend: makeMetric({ direction: '►', delta: 0, latest: 68, interpretation: 'stabil' }),
    },
    ...overrides,
  }
}

function makeEntries(count: number): CoverageTrendEntry[] {
  return Array.from({ length: count }, (_, i) =>
    makeEntry({
      run_id: 2000 + i,
      statements_pct: 60 + i * 1.5,
      branches_pct: 40 + i * 1.2,
      functions_pct: 65 + i * 1.3,
      lines_pct: 63 + i * 1.4,
    })
  )
}

function makeImprovingCoverageData(entriesCount: number = 5): CoverageTrendData {
  const entries = makeEntries(entriesCount)
  return {
    available: true,
    entries,
    summary: {
      total_runs: entriesCount,
      latest: entries[entries.length - 1],
      statements_trend: makeMetric({
        direction: '▲',
        delta: 6,
        latest: 67,
        min: 60,
        max: 67,
        avg_last_5: 64.5,
        interpretation: 'steigend',
      }),
      branches_trend: makeMetric({
        direction: '▲',
        delta: 4.8,
        latest: 44.8,
        min: 40,
        max: 44.8,
        avg_last_5: 42.5,
        interpretation: 'steigend',
      }),
      functions_trend: makeMetric({
        direction: '▲',
        delta: 5.2,
        latest: 70.2,
        min: 65,
        max: 70.2,
        avg_last_5: 68,
        interpretation: 'steigend',
      }),
      lines_trend: makeMetric({
        direction: '▲',
        delta: 5.6,
        latest: 68.6,
        min: 63,
        max: 68.6,
        avg_last_5: 66,
        interpretation: 'steigend',
      }),
    },
  }
}

function makeDecliningCoverageData(): CoverageTrendData {
  const entries = [makeEntry({ statements_pct: 70, branches_pct: 50, functions_pct: 75, lines_pct: 72 }),
    makeEntry({ statements_pct: 68, branches_pct: 48, functions_pct: 73, lines_pct: 70 }),
    makeEntry({ statements_pct: 65, branches_pct: 45, functions_pct: 70, lines_pct: 68 }),
    makeEntry({ statements_pct: 62, branches_pct: 42, functions_pct: 68, lines_pct: 65 }),
    makeEntry({ statements_pct: 60, branches_pct: 40, functions_pct: 65, lines_pct: 63 }),
  ]
  return {
    available: true,
    entries,
    summary: {
      total_runs: 5,
      latest: entries[4],
      statements_trend: makeMetric({
        direction: '▼',
        delta: -10,
        latest: 60,
        min: 60,
        max: 70,
        avg_last_5: 65,
        interpretation: 'fallend',
      }),
      branches_trend: makeMetric({
        direction: '▼',
        delta: -10,
        latest: 40,
        min: 40,
        max: 50,
        avg_last_5: 45,
        interpretation: 'fallend',
      }),
      functions_trend: makeMetric({
        direction: '▼',
        delta: -10,
        latest: 65,
        min: 65,
        max: 75,
        avg_last_5: 70,
        interpretation: 'fallend',
      }),
      lines_trend: makeMetric({
        direction: '▼',
        delta: -9,
        latest: 63,
        min: 63,
        max: 72,
        avg_last_5: 67,
        interpretation: 'fallend',
      }),
    },
  }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('CoverageTrendPanel', () => {
  // ── Szenario 1: 0 entries ─────────────────────────────────────────────────

  it('Rendering mit 0 entries → Badges sichtbar, keine Sparklines, Tabelle vorhanden', () => {
    const data = makeCoverageData({ entries: [] })
    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    // Badges für Metriken vorhanden (erscheint doppelt: in Badge und Tabelle)
    expect(screen.getAllByText('Stmts').length).toBeGreaterThanOrEqual(2)
    expect(screen.getAllByText('Branch').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Funcs').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Lines').length).toBeGreaterThanOrEqual(1)

    // Keine Sparklines (entries < 2)
    expect(document.querySelectorAll('svg[aria-label*="Sparkline"]').length).toBe(0)

    // Tabelle existiert (Min/Max/Ø)
    expect(screen.getByText('Metrik')).toBeTruthy()
    expect(screen.getByText('Min')).toBeTruthy()
    expect(screen.getByText('Max')).toBeTruthy()
    expect(screen.getByText('Ø letzte 5')).toBeTruthy()
    expect(screen.getByText('Trend')).toBeTruthy()

    // Sync-Button vorhanden
    expect(screen.getByText('🔄 Jetzt synchronisieren')).toBeTruthy()

    // Meta-Row: total_runs=0 → kein „Total Runs" Text
    expect(screen.queryByText(/total runs/i)).toBeNull()
  })

  // ── Szenario 2: 5 entries ─────────────────────────────────────────────────

  it('Rendering mit 5 entries → Sparklines, Badges, Tabelle, Meta-Row', () => {
    const data = makeImprovingCoverageData(5)
    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    // Sparklines: 4 SVGs (eine pro Metrik) mit aria-label
    const sparklines = document.querySelectorAll('svg[aria-label*="Sparkline"]')
    expect(sparklines.length).toBe(4)

    // Badges zeigen Prozentwerte (in Badges UND Tabelle → getAllByText)
    expect(screen.getAllByText('67%').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('45%').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('70%').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('69%').length).toBeGreaterThanOrEqual(1)

    // Trend-Pfeile ▲
    const arrows = document.querySelectorAll('span')
    const arrowTexts = Array.from(arrows).filter(
      (el) => el.textContent?.startsWith('▲') || el.textContent?.startsWith('▼')
    )
    // Alle 4 Metriken haben ▲ (steigend)
    expect(arrowTexts.length).toBeGreaterThanOrEqual(4)

    // Meta-Row
    expect(screen.getByText(/total runs: 5/i)).toBeTruthy()
    expect(screen.getByText(/#2004/)).toBeTruthy() // letzte Run-ID

    // Tabelle hat 4 Metrik-Zeilen
    const tbody = document.querySelector('tbody')!
    const rows = tbody.querySelectorAll('tr')
    expect(rows).toHaveLength(4)
  })

  // ── Szenario 3: 10 entries ─────────────────────────────────────────────────

  it('Rendering mit 10 entries → Sparklines korrekt, alle Badges, vollständige Tabelle', () => {
    const data = makeImprovingCoverageData(10)
    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    // Sparklines vorhanden
    const sparklines = document.querySelectorAll('svg[aria-label*="Sparkline"]')
    expect(sparklines.length).toBe(4)

    // Alle Badges vorhanden (Label erscheint doppelt: in Badge und Tabelle)
    expect(screen.getAllByText('Stmts').length).toBeGreaterThanOrEqual(2)
    expect(screen.getAllByText('Branch').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Funcs').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Lines').length).toBeGreaterThanOrEqual(1)

    // Meta-Row zeigt total_runs=10
    expect(screen.getByText(/total runs: 10/i)).toBeTruthy()

    // Tabelle: 4 Zeilen
    const tbody = document.querySelector('tbody')!
    const rows = tbody.querySelectorAll('tr')
    expect(rows).toHaveLength(4)

    // Jede Zeile hat 5 Spalten (Metrik | Min | Max | Ø | Trend)
    rows.forEach((row) => {
      expect(row.querySelectorAll('td')).toHaveLength(5)
    })
  })

  // ── Szenario 4: available=false ────────────────────────────────────────────

  it('available=false → Fehler-Meldung oder Hinweis', () => {
    const data = makeCoverageData({
      available: false,
      entries: [],
      summary: null,
      error: 'coverage-trend.json nicht gefunden',
    })

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    // Leer-/Fehlermeldung
    expect(screen.getByText(/coverage-trend.json nicht gefunden/i)).toBeTruthy()

    // Titel trotzdem vorhanden
    expect(screen.getByText(/🧪 Coverage Trend/i)).toBeTruthy()

    // Keine Badges, keine Tabelle
    expect(screen.queryByText('Stmts')).toBeNull()
    expect(screen.queryByText('Metrik')).toBeNull()
  })

  it('available=false ohne error → generische Meldung', () => {
    const data = makeCoverageData({
      available: false,
      entries: [],
      summary: null,
    })

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    expect(screen.getByText(/noch keine daten/i)).toBeTruthy()
  })

  // ── Szenario 5: summary=null ───────────────────────────────────────────────

  it('available=true, summary=null → „Keine Summary-Daten"', () => {
    const data = makeCoverageData({
      available: true,
      entries: [],
      summary: null,
    })

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    expect(screen.getByText(/keine summary-daten/i)).toBeTruthy()
    // Keine Badges, keine Tabelle
    expect(screen.queryByText('Stmts')).toBeNull()
  })

  // ── Szenario 6: Trend-Pfeile validieren ────────────────────────────────────

  it('Steigender Trend → ▲ (grün) in Badges', () => {
    const data = makeImprovingCoverageData(5)

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    // Mindestens 4 ▲-Elemente
    const allText = document.body.textContent || ''
    const upArrows = (allText.match(/▲/g) || []).length
    expect(upArrows).toBeGreaterThanOrEqual(4)

    // Keine ▼-Pfeile
    const downArrows = (allText.match(/▼/g) || []).length
    expect(downArrows).toBe(0)
  })

  it('Fallender Trend → ▼ (rot) in Badges', () => {
    const data = makeDecliningCoverageData()

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    const allText = document.body.textContent || ''
    const downArrows = (allText.match(/▼/g) || []).length
    expect(downArrows).toBeGreaterThanOrEqual(4)

    // Keine ▲-Pfeile
    const upArrows = (allText.match(/▲/g) || []).length
    expect(upArrows).toBe(0)
  })

  it('Stabiler Trend → ► (grau) in Badges', () => {
    const data = makeCoverageData({
      available: true,
      entries: [],
      summary: {
        total_runs: 1,
        latest: null,
        statements_trend: makeMetric({ direction: '►', delta: 0, latest: 65, interpretation: 'stabil' }),
        branches_trend: makeMetric({ direction: '►', delta: 0, latest: 45, interpretation: 'stabil' }),
        functions_trend: makeMetric({ direction: '►', delta: 0, latest: 70, interpretation: 'stabil' }),
        lines_trend: makeMetric({ direction: '►', delta: 0, latest: 68, interpretation: 'stabil' }),
      },
    })

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    const allText = document.body.textContent || ''
    // ►-Pfeile vorhanden
    const flatArrows = (allText.match(/►/g) || []).length
    expect(flatArrows).toBeGreaterThanOrEqual(4)

    // Keine ▲/▼-Pfeile
    expect((allText.match(/▲/g) || []).length).toBe(0)
    expect((allText.match(/▼/g) || []).length).toBe(0)
  })

  // ── Szenario 7: Sparklines prüfen ─────────────────────────────────────────

  it('Sparklines rendern SVG polyline + circle für jeden Metrik-Typ', () => {
    const data = makeImprovingCoverageData(5)

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    const sparklines = document.querySelectorAll('svg[aria-label*="Sparkline"]')
    expect(sparklines).toHaveLength(4)

    sparklines.forEach((svg) => {
      // Jede Sparkline hat polyline
      const polyline = svg.querySelector('polyline')
      expect(polyline).not.toBeNull()
      expect(polyline!.getAttribute('points')).toBeTruthy()

      // Jede Sparkline hat einen Endpunkt-Kreis
      const circle = svg.querySelector('circle')
      expect(circle).not.toBeNull()

      // Verbessernd = grüne Linie
      expect(polyline!.getAttribute('stroke')).toBe('#4caf50')
    })
  })

  it('Fallender Trend → rote Sparkline-Linie', () => {
    const data = makeDecliningCoverageData()

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    const sparklines = document.querySelectorAll('svg[aria-label*="Sparkline"]')
    expect(sparklines).toHaveLength(4)

    sparklines.forEach((svg) => {
      const polyline = svg.querySelector('polyline')
      // Fallend = rot
      expect(polyline!.getAttribute('stroke')).toBe('#f44336')
    })
  })

  it('Nur 1 Entry → keine Sparklines', () => {
    const data = makeCoverageData({
      available: true,
      entries: [makeEntry()],
      summary: {
        total_runs: 1,
        latest: makeEntry(),
        statements_trend: makeMetric(),
        branches_trend: makeMetric(),
        functions_trend: makeMetric(),
        lines_trend: makeMetric(),
      },
    })

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    const sparklines = document.querySelectorAll('svg[aria-label*="Sparkline"]')
    expect(sparklines).toHaveLength(0)
  })

  // ── Szenario 8: Tabelle Min/Max/Ø ─────────────────────────────────────────

  it('Tabelle zeigt korrekte Min/Max/Ø-Werte für jede Metrik', () => {
    const data = makeImprovingCoverageData(5)

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    const tbody = document.querySelector('tbody')!
    const rows = tbody.querySelectorAll('tr')
    expect(rows).toHaveLength(4)

    // Erste Zeile: Statements → min=60, max=67, avg=65, trend=steigend
    const stmtsCells = rows[0].querySelectorAll('td')
    expect(stmtsCells[0].textContent).toBe('Stmts')
    expect(stmtsCells[1].textContent).toBe('60%')
    expect(stmtsCells[2].textContent).toBe('67%')
    expect(stmtsCells[3].textContent).toBe('65%')
    expect(stmtsCells[4].textContent).toBe('steigend')

    // Zweite Zeile: Branch → min=40, max=45, avg=43
    const branchCells = rows[1].querySelectorAll('td')
    expect(branchCells[0].textContent).toBe('Branch')
    expect(branchCells[1].textContent).toBe('40%')
    expect(branchCells[2].textContent).toBe('45%')
    expect(branchCells[3].textContent).toBe('43%')

    // Dritte Zeile: Funcs
    const funcsCells = rows[2].querySelectorAll('td')
    expect(funcsCells[0].textContent).toBe('Funcs')
    expect(funcsCells[3].textContent).toBe('68%')

    // Vierte Zeile: Lines
    const linesCells = rows[3].querySelectorAll('td')
    expect(linesCells[0].textContent).toBe('Lines')
    expect(linesCells[3].textContent).toBe('66%')
  })

  it('Tabelle zeigt „–" für null-Werte', () => {
    const data = makeCoverageData({
      available: true,
      entries: [],
      summary: {
        total_runs: 0,
        latest: null,
        statements_trend: makeMetric({ latest: null, min: null, max: null, avg_last_5: null }),
        branches_trend: makeMetric({ latest: null, min: null, max: null, avg_last_5: null }),
        functions_trend: makeMetric({ latest: null, min: null, max: null, avg_last_5: null }),
        lines_trend: makeMetric({ latest: null, min: null, max: null, avg_last_5: null }),
      },
    })

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    // Alle Zellen sollten „–" zeigen
    const allTDs = document.querySelectorAll('td')
    const dashCells = Array.from(allTDs).filter((td) => td.textContent === '–')
    // 4 Zeilen × 4 Daten-Spalten (Min, Max, Ø, Trend-interpretation) = 16 Zellen
    // Min + Max + Ø = 12 Zellen + Trend-Spalte kann auch interpretation enthalten
    expect(dashCells.length).toBeGreaterThanOrEqual(8)
  })

  // ── Szenario 9: Sync-Button-Verhalten ─────────────────────────────────────

  it('Sync-Button ruft onSync auf', () => {
    const onSync = vi.fn()
    const data = makeCoverageData()

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={onSync}
      />
    )

    const btn = screen.getByText('🔄 Jetzt synchronisieren')
    fireEvent.click(btn)
    expect(onSync).toHaveBeenCalledTimes(1)
  })

  it('Sync-Button disabled wenn syncing=true', () => {
    const onSync = vi.fn()
    const data = makeCoverageData()

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={true}
        syncResult={null}
        onSync={onSync}
      />
    )

    const btn = screen.getByText('⏳ Sync läuft…')
    expect(btn).toHaveProperty('disabled', true)

    fireEvent.click(btn)
    expect(onSync).not.toHaveBeenCalled()
  })

  // ── Szenario 10: syncResult States ────────────────────────────────────────

  it('syncResult: ok mit newEntries > 0 → grünes Feedback', () => {
    const data = makeCoverageData()

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={{ status: 'ok', message: '3 neue Einträge synchronisiert', newEntries: 3 }}
        onSync={vi.fn()}
      />
    )

    const feedback = screen.getByText(/3 neue einträge synchronisiert/i)
    expect(feedback).toBeTruthy()
    expect(feedback.textContent).toContain('✅')
  })

  it('syncResult: ok mit newEntries=0 → Info-Feedback', () => {
    const data = makeCoverageData()

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={{ status: 'ok', message: 'Bereits aktuell — keine neuen Daten', newEntries: 0 }}
        onSync={vi.fn()}
      />
    )

    const feedback = screen.getByText(/bereits aktuell/i)
    expect(feedback).toBeTruthy()
    expect(feedback.textContent).toContain('ℹ️')
  })

  it('syncResult: no_data → graues Feedback', () => {
    const data = makeCoverageData()

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={{ status: 'no_data', message: 'Kein CI-Run mit Coverage-Daten gefunden', newEntries: 0 }}
        onSync={vi.fn()}
      />
    )

    const feedback = screen.getByText(/kein ci-run mit coverage-daten gefunden/i)
    expect(feedback).toBeTruthy()
    expect(feedback.textContent).toContain('📭')
  })

  it('syncResult: error → rotes Feedback', () => {
    const data = makeCoverageData()

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={{ status: 'error', message: 'GitHub API nicht erreichbar', newEntries: 0 }}
        onSync={vi.fn()}
      />
    )

    const feedback = screen.getByText(/github api nicht erreichbar/i)
    expect(feedback).toBeTruthy()
    expect(feedback.textContent).toContain('❌')
  })

  // ── GitHub-Link ───────────────────────────────────────────────────────────

  it('Meta-Row enthält GitHub-Link zur neuesten Run-ID', () => {
    const data = makeImprovingCoverageData(5)
    // latest hat run_id=2004
    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    const link = screen.getByText('#2004')
    expect(link).toBeTruthy()
    expect((link as HTMLAnchorElement).href).toContain('github.com/Kirobi92/OpenDisruption/actions/runs/2004')
  })

  it('Meta-Row zeigt Datum des letzten Runs', () => {
    const data = makeImprovingCoverageData(5)

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    // latest.started_at: '2026-05-25T10:00:00Z' → slice(0,10) = '2026-05-25'
    expect(screen.getByText('2026-05-25')).toBeTruthy()
  })

  // ── total_runs=0 → keine Meta-Row ─────────────────────────────────────────

  it('total_runs=0 → keine Run-ID und kein Datum', () => {
    const data = makeCoverageData({ entries: [] })

    render(
      <CoverageTrendPanel
        coverageTrend={data}
        syncing={false}
        syncResult={null}
        onSync={vi.fn()}
      />
    )

    expect(screen.queryByRole('link')).toBeNull()
    expect(screen.queryByText(/2026-/)).toBeNull()
  })
})
