/**
 * Unit-Tests: MusicHealthConfigPanel
 * Vitest + @testing-library/react
 *
 * Testszenarien:
 *   1. GET /api/music-health-config — Panel zeigt refresh_s + source korrekt an
 *   2. Edit-Button → Eingabe → PUT-Call wird ausgelöst
 *   3. PUT-Response → saveMsg "✅ Interval auf Xs gesetzt (Runtime)"
 *   4. Validierung: Wert < 10 zeigt Fehler, kein PUT
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { MusicHealthConfigPanel } from '../modules/system/MusicHealthConfigPanel'

// ─── Fetch-Mock ────────────────────────────────────────────────────────────────
const mockFetch = vi.fn()
beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch)
})
afterEach(() => {
  vi.restoreAllMocks()
  mockFetch.mockReset()
})

// Hilfsfunktion: Response-Mock
function mockResponse(body: object, ok = true) {
  return Promise.resolve({
    ok,
    json: () => Promise.resolve(body),
  } as Response)
}

// ─── Tests ─────────────────────────────────────────────────────────────────────

describe('MusicHealthConfigPanel', () => {
  it('zeigt refresh_s und Quelle nach GET-Response an', async () => {
    mockFetch.mockReturnValueOnce(mockResponse({ refresh_s: 30, source: 'default' }))

    render(
      <MusicHealthConfigPanel
        base="http://localhost:8765"
        musicHealthRefreshMs={30000}
        onRefreshMsChange={vi.fn()}
      />
    )

    // Erst null → Panel nicht sichtbar; nach fetch-Antwort erscheint es
    await waitFor(() => {
      expect(screen.getByTestId('music-health-config-panel')).toBeTruthy()
    })

    expect(screen.getByTestId('refresh-s').textContent).toBe('30s')
    expect(screen.getByTestId('source-label').textContent).toBe('⚙️ Default')

    // GET wurde exakt 1x mit korrekter URL aufgerufen
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8765/api/music-health-config',
      { cache: 'no-store' }
    )
  })

  it('zeigt "📌 ENV" als Quelle wenn source=env', async () => {
    mockFetch.mockReturnValueOnce(mockResponse({ refresh_s: 60, source: 'env' }))

    render(
      <MusicHealthConfigPanel
        base="http://localhost:8765"
        musicHealthRefreshMs={60000}
        onRefreshMsChange={vi.fn()}
      />
    )

    await waitFor(() => screen.getByTestId('source-label'))
    expect(screen.getByTestId('source-label').textContent).toBe('📌 ENV')
  })

  it('zeigt "⚡ Runtime" als Quelle wenn source=runtime', async () => {
    mockFetch.mockReturnValueOnce(mockResponse({ refresh_s: 20, source: 'runtime' }))

    render(
      <MusicHealthConfigPanel
        base="http://localhost:8765"
        musicHealthRefreshMs={20000}
        onRefreshMsChange={vi.fn()}
      />
    )

    await waitFor(() => screen.getByTestId('source-label'))
    expect(screen.getByTestId('source-label').textContent).toBe('⚡ Runtime')
  })

  it('Edit-Button öffnet Eingabe, PUT-Call wird korrekt ausgelöst', async () => {
    // GET
    mockFetch.mockReturnValueOnce(mockResponse({ refresh_s: 30, source: 'default' }))
    // PUT
    mockFetch.mockReturnValueOnce(mockResponse({ refresh_s: 45, source: 'runtime' }))

    const onChangeMock = vi.fn()

    render(
      <MusicHealthConfigPanel
        base="http://localhost:8765"
        musicHealthRefreshMs={30000}
        onRefreshMsChange={onChangeMock}
      />
    )

    // Warten bis Panel erscheint
    await waitFor(() => screen.getByTestId('edit-button'))

    // Edit-Button klicken
    fireEvent.click(screen.getByTestId('edit-button'))

    // Input prüfen und Wert setzen
    const input = screen.getByTestId('interval-input') as HTMLInputElement
    expect(input.value).toBe('30')

    fireEvent.change(input, { target: { value: '45' } })
    expect(input.value).toBe('45')

    // Speichern
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-button'))
    })

    // PUT wurde aufgerufen
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8765/api/music-health-config',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ refresh_s: 45 }),
      })
    )

    // onRefreshMsChange mit korrektem Wert aufgerufen
    expect(onChangeMock).toHaveBeenCalledWith(45000)

    // Erfolgsmeldung angezeigt
    await waitFor(() => {
      expect(screen.getByTestId('save-msg').textContent).toContain('✅ Interval auf 45s gesetzt')
    })
  })

  it('Validierungsfehler bei Wert < 10 — kein PUT', async () => {
    mockFetch.mockReturnValueOnce(mockResponse({ refresh_s: 30, source: 'default' }))

    render(
      <MusicHealthConfigPanel
        base="http://localhost:8765"
        musicHealthRefreshMs={30000}
        onRefreshMsChange={vi.fn()}
      />
    )

    await waitFor(() => screen.getByTestId('edit-button'))
    fireEvent.click(screen.getByTestId('edit-button'))

    const input = screen.getByTestId('interval-input') as HTMLInputElement
    fireEvent.change(input, { target: { value: '5' } })

    fireEvent.click(screen.getByTestId('save-button'))

    // Fehlermeldung erscheint, kein zweiter fetch-Aufruf
    await waitFor(() => {
      expect(screen.getByTestId('save-msg').textContent).toContain('❌ Mindestwert 10 Sekunden')
    })

    // mockFetch wurde nur 1x (GET) aufgerufen — kein PUT
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('Cancel-Button schließt Edit-Mode ohne Mutation', async () => {
    mockFetch.mockReturnValueOnce(mockResponse({ refresh_s: 30, source: 'default' }))

    render(
      <MusicHealthConfigPanel
        base="http://localhost:8765"
        musicHealthRefreshMs={30000}
        onRefreshMsChange={vi.fn()}
      />
    )

    await waitFor(() => screen.getByTestId('edit-button'))
    fireEvent.click(screen.getByTestId('edit-button'))

    expect(screen.queryByTestId('interval-input')).toBeTruthy()

    fireEvent.click(screen.getByTestId('cancel-button'))

    // Edit-Mode geschlossen → Edit-Button wieder sichtbar
    await waitFor(() => {
      expect(screen.getByTestId('edit-button')).toBeTruthy()
    })

    // Kein PUT wurde ausgeführt
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })
})
