/**
 * Unit-Tests: ScAlertsPanel — Pagination (Vitest + @testing-library/react)
 *
 * Testszenarien:
 *   1. offset=0, hasMore=true  → Next enabled, Prev disabled
 *   2. offset=5, hasMore=false → Prev enabled, Next disabled
 *   3. Leer-State (0 Events, offset=0) → Leer-Meldung, keine Buttons
 *   4. Farbkodierung: sc_issue_count>0 = rot, =0 = grün
 *   5. GitHub-Link href korrekt
 *   6. Seitenanzeige "Seite X / N" bei totalPages > 1
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ScAlertsPanel } from '../modules/system/ScAlertsPanel'
import { type ScAlertEvent } from '../modules/system/types'

// ─── Test-Fixtures ─────────────────────────────────────────────────────────────

function makeAlert(overrides: Partial<ScAlertEvent> = {}): ScAlertEvent {
  return {
    timestamp: '2026-05-22T10:00:00Z',
    run_id: 12345,
    run_started_at: '2026-05-22T09:59:00Z',
    sc_issue_count: 1,
    threshold: 0,
    delta: 1,
    ...overrides,
  }
}

function makeAlerts(count: number): ScAlertEvent[] {
  return Array.from({ length: count }, (_, i) =>
    makeAlert({ run_id: 1000 + i, timestamp: `2026-05-22T${String(10 + i).padStart(2, '0')}:00:00Z` })
  )
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('ScAlertsPanel — Pagination', () => {
  it('offset=0 + hasMore=true → Prev disabled, Next enabled', () => {
    const onPrev = vi.fn()
    const onNext = vi.fn()
    const alerts = makeAlerts(5)

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={10}
        offset={0}
        hasMore={true}
        onPrev={onPrev}
        onNext={onNext}
      />
    )

    const prevBtn = screen.getByRole('button', { name: /vorherige seite/i })
    const nextBtn = screen.getByRole('button', { name: /nächste seite/i })

    expect(prevBtn).toHaveProperty('disabled', true)
    expect(nextBtn).toHaveProperty('disabled', false)

    // Next-Click → onNext aufgerufen
    fireEvent.click(nextBtn)
    expect(onNext).toHaveBeenCalledTimes(1)
    expect(onPrev).not.toHaveBeenCalled()
  })

  it('offset=5 + hasMore=false → Prev enabled, Next disabled', () => {
    const onPrev = vi.fn()
    const onNext = vi.fn()
    const alerts = makeAlerts(5)

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={10}
        offset={5}
        hasMore={false}
        onPrev={onPrev}
        onNext={onNext}
      />
    )

    const prevBtn = screen.getByRole('button', { name: /vorherige seite/i })
    const nextBtn = screen.getByRole('button', { name: /nächste seite/i })

    expect(prevBtn).toHaveProperty('disabled', false)
    expect(nextBtn).toHaveProperty('disabled', true)

    // Prev-Click → onPrev aufgerufen
    fireEvent.click(prevBtn)
    expect(onPrev).toHaveBeenCalledTimes(1)
    expect(onNext).not.toHaveBeenCalled()
  })

  it('Leer-State (0 Events, offset=0) → Leer-Meldung, keine Pagination-Buttons', () => {
    render(
      <ScAlertsPanel
        scAlerts={[]}
        total={0}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    expect(screen.getByText(/shellcheck sauber/i)).toBeTruthy()
    expect(screen.queryByRole('button')).toBeNull()
  })

  it('Delta-Spalte zeigt Trending-Pfeil ▲ bei positivem, ▼ bei negativem Delta, — bei 0', () => {
    const alerts = [
      makeAlert({ run_id: 2001, delta: 3 }),
      makeAlert({ run_id: 2002, delta: -2 }),
      makeAlert({ run_id: 2003, delta: 0 }),
    ]

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={3}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    const cells = document.querySelectorAll('td')
    const allTexts = Array.from(cells).map((td) => td.textContent)
    expect(allTexts.some((t) => t?.includes('▲'))).toBe(true)
    expect(allTexts.some((t) => t?.includes('▼'))).toBe(true)
    expect(allTexts.some((t) => t?.includes('—'))).toBe(true)
  })

  it('sc_issue_count > 0 zeigt rote Farbe; =0 zeigt grüne Farbe', () => {
    const alerts = [
      makeAlert({ run_id: 1001, sc_issue_count: 2, delta: 2 }),
      makeAlert({ run_id: 1002, sc_issue_count: 0, delta: 0 }),
    ]

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={2}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    const cells = document.querySelectorAll('td')
    // Suche die SC-Count-Zellen (3. Spalte = Index 2 pro Zeile → td[2] und td[7])
    // Einfacher: alle td-Texts prüfen
    const allTexts = Array.from(cells).map((td) => td.textContent)
    expect(allTexts).toContain('2')
    expect(allTexts).toContain('0')

    // Farbkodierung: sc_count-Zelle für Alert 1001 soll rot sein
    const redCells = Array.from(cells).filter(
      (td) => (td as HTMLElement).style.color === 'rgb(255, 82, 82)' ||
               (td as HTMLElement).style.color === '#ff5252'
    )
    const greenCells = Array.from(cells).filter(
      (td) => (td as HTMLElement).style.color === 'rgb(76, 175, 80)' ||
               (td as HTMLElement).style.color === '#4caf50'
    )

    expect(redCells.length).toBeGreaterThanOrEqual(1)
    expect(greenCells.length).toBeGreaterThanOrEqual(1)
  })

  it('GitHub-Link href korrekt für run_id', () => {
    const alert = makeAlert({ run_id: 98765 })

    render(
      <ScAlertsPanel
        scAlerts={[alert]}
        total={1}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    const link = screen.getByRole('link') as HTMLAnchorElement
    expect(link.href).toContain('98765')
    expect(link.href).toContain('github.com/Kirobi92/OpenDisruption/actions/runs/')
  })

  it('Seitenanzeige "Seite X / N" sichtbar wenn totalPages > 1', () => {
    // total=10, PAGE_LIMIT=5 → totalPages=2 → Seite 1/2
    const alerts = makeAlerts(5)

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={10}
        offset={0}
        hasMore={true}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    expect(screen.getByText(/seite 1 \/ 2/i)).toBeTruthy()
  })

  it('Seitenanzeige NICHT sichtbar wenn totalPages = 1', () => {
    const alerts = makeAlerts(3)

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={3}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    expect(screen.queryByText(/seite/i)).toBeNull()
  })

  it('Keyboard ArrowRight → onNext aufgerufen wenn hasMore=true', () => {
    const onNext = vi.fn()
    const onPrev = vi.fn()
    const alerts = makeAlerts(5)

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={10}
        offset={0}
        hasMore={true}
        onPrev={onPrev}
        onNext={onNext}
      />
    )

    const region = screen.getByRole('region', { name: /sc-alert-history/i })
    fireEvent.keyDown(region, { key: 'ArrowRight' })
    expect(onNext).toHaveBeenCalledTimes(1)
    expect(onPrev).not.toHaveBeenCalled()
  })

  it('Keyboard ArrowLeft → onPrev aufgerufen wenn offset>0', () => {
    const onNext = vi.fn()
    const onPrev = vi.fn()
    const alerts = makeAlerts(5)

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={10}
        offset={5}
        hasMore={false}
        onPrev={onPrev}
        onNext={onNext}
      />
    )

    const region = screen.getByRole('region', { name: /sc-alert-history/i })
    fireEvent.keyDown(region, { key: 'ArrowLeft' })
    expect(onPrev).toHaveBeenCalledTimes(1)
    expect(onNext).not.toHaveBeenCalled()
  })

  it('Keyboard ArrowRight → onNext NICHT aufgerufen wenn hasMore=false', () => {
    const onNext = vi.fn()
    const alerts = makeAlerts(3)

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={3}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={onNext}
      />
    )

    const region = screen.getByRole('region', { name: /sc-alert-history/i })
    fireEvent.keyDown(region, { key: 'ArrowRight' })
    expect(onNext).not.toHaveBeenCalled()
  })

  // ── Explizite Zeilen-Tests (0/2/5 Events) per Task OPE-290 ──

  it('Render mit 0 Events → Leer-Meldung, keine Tabellenzeilen (tbody)', () => {
    render(
      <ScAlertsPanel
        scAlerts={[]}
        total={0}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    expect(screen.getByText(/shellcheck sauber/i)).toBeTruthy()
    // Es gibt keine Tabelle — also auch keine tr im tbody
    const tbody = document.querySelector('tbody')
    expect(tbody).toBeNull()
  })

  it('Render mit 2 Events → genau 2 Tabellenzeilen (tr) im tbody', () => {
    const alerts = makeAlerts(2)

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={2}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    const tbody = document.querySelector('tbody')!
    expect(tbody).not.toBeNull()
    const rows = tbody.querySelectorAll('tr')
    expect(rows).toHaveLength(2)

    // Farb-Check: erste Zeile sc_count > 0 → rot
    const firstRowCountCell = rows[0].querySelectorAll('td')[2]
    expect(firstRowCountCell?.textContent).toBe('1')
    expect((firstRowCountCell as HTMLElement).style.color).toBe('rgb(255, 82, 82)')
  })

  it('Render mit 5 Events → genau 5 Tabellenzeilen (tr) im tbody', () => {
    const alerts = makeAlerts(5)

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={5}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    const tbody = document.querySelector('tbody')!
    expect(tbody).not.toBeNull()
    const rows = tbody.querySelectorAll('tr')
    expect(rows).toHaveLength(5)
  })

  it('Render mit 5 Events, sc_count=0 → grüne Farbklasse', () => {
    const alerts = [
      makeAlert({ run_id: 9001, sc_issue_count: 0, delta: 0 }),
      makeAlert({ run_id: 9002, sc_issue_count: 0, delta: 0 }),
      makeAlert({ run_id: 9003, sc_issue_count: 0, delta: 0 }),
      makeAlert({ run_id: 9004, sc_issue_count: 0, delta: 0 }),
      makeAlert({ run_id: 9005, sc_issue_count: 0, delta: 0 }),
    ]

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={5}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    const tbody = document.querySelector('tbody')!
    const rows = tbody.querySelectorAll('tr')
    expect(rows).toHaveLength(5)

    // Alle 5 SC-Count-Zellen (Spalte Index 2) müssen grün sein
    rows.forEach((row) => {
      const countCell = row.querySelectorAll('td')[2] as HTMLElement
      expect(countCell.style.color).toBe('rgb(76, 175, 80)')
      expect(countCell.textContent).toBe('0')
    })
  })

  it('Render mit 5 Events, sc_count > 0 → rote Farbklasse', () => {
    const alerts = [
      makeAlert({ run_id: 8001, sc_issue_count: 3, delta: 3 }),
      makeAlert({ run_id: 8002, sc_issue_count: 5, delta: 2 }),
      makeAlert({ run_id: 8003, sc_issue_count: 1, delta: -4 }),
      makeAlert({ run_id: 8004, sc_issue_count: 7, delta: 6 }),
      makeAlert({ run_id: 8005, sc_issue_count: 2, delta: -5 }),
    ]

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={5}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    const tbody = document.querySelector('tbody')!
    const rows = tbody.querySelectorAll('tr')
    expect(rows).toHaveLength(5)

    // Alle 5 SC-Count-Zellen müssen rot sein (sc_count > 0)
    rows.forEach((row) => {
      const countCell = row.querySelectorAll('td')[2] as HTMLElement
      expect(countCell.style.color).toBe('rgb(255, 82, 82)')
    })
  })

  it('GitHub-Link href: alle 5 Zeilen haben korrekten Actions-Runs-Link', () => {
    const alerts = makeAlerts(5)

    render(
      <ScAlertsPanel
        scAlerts={alerts}
        total={5}
        offset={0}
        hasMore={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      />
    )

    const links = document.querySelectorAll('a[href*="github.com/Kirobi92/OpenDisruption/actions/runs/"]')
    expect(links).toHaveLength(5)

    links.forEach((link, i) => {
      expect((link as HTMLAnchorElement).href).toContain(String(1000 + i))
    })
  })
})
// unit-test trigger Fr 22. Mai 05:38:23 CEST 2026
