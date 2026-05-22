/**
 * Vitest Snapshot-Test: StoryMusicHealthConfig
 * DOM-Snapshots für alle 3 Szenarien (Default / ENV / Runtime)
 *
 * Ziel: Storybook-ähnlicher Regression-Schutz ohne Storybook-Overhead.
 * Jedes Szenario rendert MusicHealthConfigPanel mit Mock-Fetch und
 * sichert den resultierenden DOM als Snapshot.
 *
 * Szenarien:
 *   1. Default  — source=default, refresh_s=30  → ⚙️ Default
 *   2. ENV      — source=env,     refresh_s=60  → 📌 ENV
 *   3. Runtime  — source=runtime, refresh_s=15  → ⚡ Runtime
 *
 * Snapshots werden in __snapshots__/StoryMusicHealthConfig.snapshot.test.tsx.snap
 * gespeichert. Bei absichtlichen Änderungen: `vitest run --update-snapshots`
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'
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

function mockGETResponse(body: { refresh_s: number; source: string }) {
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve(body),
  } as Response)
}

// ─── Szenarien ─────────────────────────────────────────────────────────────────
const SCENARIOS = [
  {
    name: 'Default (source=default, refresh_s=30)',
    mockResponse: { refresh_s: 30, source: 'default' },
    refreshMs: 30000,
    expectedSourceLabel: '⚙️ Default',
    expectedRefreshS: '30s',
  },
  {
    name: 'ENV (source=env, refresh_s=60)',
    mockResponse: { refresh_s: 60, source: 'env' },
    refreshMs: 60000,
    expectedSourceLabel: '📌 ENV',
    expectedRefreshS: '60s',
  },
  {
    name: 'Runtime (source=runtime, refresh_s=15)',
    mockResponse: { refresh_s: 15, source: 'runtime' },
    refreshMs: 15000,
    expectedSourceLabel: '⚡ Runtime',
    expectedRefreshS: '15s',
  },
]

// ─── Snapshot-Tests ────────────────────────────────────────────────────────────
describe('StoryMusicHealthConfig — DOM-Snapshot-Regression', () => {
  for (const scenario of SCENARIOS) {
    it(`Snapshot: ${scenario.name}`, async () => {
      mockFetch.mockReturnValueOnce(mockGETResponse(scenario.mockResponse))

      const { getByTestId, container } = render(
        <MusicHealthConfigPanel
          base="http://localhost:8765"
          musicHealthRefreshMs={scenario.refreshMs}
          onRefreshMsChange={vi.fn()}
        />
      )

      // Warten bis Panel gerendert ist (fetch abgeschlossen)
      await waitFor(() => getByTestId('music-health-config-panel'))

      // Werte-Validierung (guard assertions vor Snapshot)
      expect(getByTestId('refresh-s').textContent).toBe(scenario.expectedRefreshS)
      expect(getByTestId('source-label').textContent).toBe(scenario.expectedSourceLabel)

      // DOM-Snapshot für Regression-Schutz
      expect(container.firstChild).toMatchSnapshot()
    })
  }
})

// ─── Edit-Mode Snapshot ────────────────────────────────────────────────────────
describe('StoryMusicHealthConfig — Edit-Mode Snapshot', () => {
  it('Snapshot: Edit-Mode offen (Default-Szenario)', async () => {
    mockFetch.mockReturnValueOnce(mockGETResponse({ refresh_s: 30, source: 'default' }))

    const { getByTestId, container } = render(
      <MusicHealthConfigPanel
        base="http://localhost:8765"
        musicHealthRefreshMs={30000}
        onRefreshMsChange={vi.fn()}
      />
    )

    await waitFor(() => getByTestId('edit-button'))

    // Edit-Mode aktivieren
    getByTestId('edit-button').click()

    // Input erscheint
    await waitFor(() => getByTestId('interval-input'))

    // Snapshot mit geöffnetem Edit-Mode
    expect(container.firstChild).toMatchSnapshot()
  })
})
