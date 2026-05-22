import { useState } from 'react'
import { MusicHealthConfigPanel } from '../modules/system/MusicHealthConfigPanel'

/**
 * Dev-Story: /story/music-health-config
 *
 * Isolierte Komponenten-Vorschau für MusicHealthConfigPanel.
 * Drei Szenarien mit Mock-Props — keine Backend-Abhängigkeit.
 *
 * Usage:
 *   http://localhost:5173/#/story/music-health-config
 *
 * Szenarien:
 *   1. Default (source=default, refresh_s=30) — grauer Source-Label
 *   2. ENV-gesteuert (source=env, refresh_s=60) — blauer Source-Label
 *   3. Runtime-Override (source=runtime, refresh_s=15) — gelber Source-Label
 */

const SCENARIOS: Array<{
  label: string
  refreshMs: number
  mockResponse: { refresh_s: number; source: string }
  description: string
}> = [
  {
    label: '⚙️ Default (30s)',
    refreshMs: 30000,
    mockResponse: { refresh_s: 30, source: 'default' },
    description: 'Standard-Wert, kein ENV gesetzt. Source-Label zeigt ⚙️ Default.',
  },
  {
    label: '📌 ENV (60s)',
    refreshMs: 60000,
    mockResponse: { refresh_s: 60, source: 'env' },
    description: 'KIROBI_MUSIC_HEALTH_REFRESH_S=60 im ENV gesetzt. Source-Label zeigt 📌 ENV.',
  },
  {
    label: '⚡ Runtime (15s)',
    refreshMs: 15000,
    mockResponse: { refresh_s: 15, source: 'runtime' },
    description: 'PUT /api/music-health-config wurde aufgerufen. Source-Label zeigt ⚡ Runtime.',
  },
]

/**
 * Mock-API-Base der Story: gibt via globalThis._storyMockResponse
 * beliebige GET-Responses zurück ohne echten Server.
 */
const STORY_BASE = '__story_mock__'

// Patch global fetch für Story-Modus
function installStoryFetch(mockResponse: { refresh_s: number; source: string }) {
  const origFetch = window._storyOrigFetch ?? window.fetch
  window._storyOrigFetch = origFetch

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    if (url.includes(STORY_BASE)) {
      if (init?.method === 'PUT') {
        const body = JSON.parse(init.body as string)
        const val = body.refresh_s ?? mockResponse.refresh_s
        return new Response(JSON.stringify({ refresh_s: val, source: 'runtime' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response(JSON.stringify(mockResponse), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }
    return origFetch(input, init)
  }
}

// TypeScript: window-Erweiterung
declare global {
  interface Window {
    _storyOrigFetch?: typeof fetch
  }
}

export function StoryMusicHealthConfig() {
  const [activeScenario, setActiveScenario] = useState(0)
  const [refreshMs, setRefreshMs] = useState(SCENARIOS[0].refreshMs)

  const scenario = SCENARIOS[activeScenario]
  installStoryFetch(scenario.mockResponse)

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#0d0d1a',
        color: '#e0e0e0',
        fontFamily: 'monospace',
        padding: 24,
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 24, borderBottom: '1px solid #333', paddingBottom: 12 }}>
        <h2 style={{ margin: 0, color: '#7986cb', fontSize: 18 }}>
          📖 Dev-Story: MusicHealthConfigPanel
        </h2>
        <p style={{ margin: '6px 0 0', fontSize: 11, color: '#888' }}>
          Isolierte Komponenten-Vorschau — Mock-API, kein Backend erforderlich
        </p>
      </div>

      {/* Szenario-Auswahl */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 11, color: '#aaa', marginBottom: 8 }}>Szenario wählen:</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {SCENARIOS.map((s, i) => (
            <button
              key={i}
              onClick={() => {
                setActiveScenario(i)
                setRefreshMs(s.refreshMs)
              }}
              style={{
                padding: '6px 14px',
                fontSize: 12,
                background: activeScenario === i ? '#1a2a4a' : '#1a1a2e',
                color: activeScenario === i ? '#90caf9' : '#888',
                border: `1px solid ${activeScenario === i ? '#7986cb' : '#333'}`,
                borderRadius: 6,
                cursor: 'pointer',
                fontFamily: 'monospace',
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
        <p style={{ fontSize: 11, color: '#666', margin: '8px 0 0' }}>
          💡 {scenario.description}
        </p>
      </div>

      {/* Divider */}
      <div
        style={{
          background: '#1a1a2e',
          border: '1px solid #2a2a3e',
          borderRadius: 8,
          padding: 16,
          maxWidth: 480,
        }}
      >
        <div style={{ fontSize: 10, color: '#555', marginBottom: 12 }}>
          RENDERED COMPONENT ↓
        </div>
        <MusicHealthConfigPanel
          key={`scenario-${activeScenario}`}
          base={STORY_BASE}
          musicHealthRefreshMs={refreshMs}
          onRefreshMsChange={(ms) => setRefreshMs(ms)}
        />
      </div>

      {/* State-Debug */}
      <div
        style={{
          marginTop: 20,
          background: '#111',
          border: '1px solid #222',
          borderRadius: 6,
          padding: 12,
          fontSize: 11,
          color: '#666',
          maxWidth: 480,
        }}
      >
        <strong style={{ color: '#444' }}>Debug-State:</strong>
        <pre style={{ margin: '6px 0 0', color: '#557' }}>
          {JSON.stringify(
            {
              activeScenario: scenario.label,
              refreshMs,
              mockResponse: scenario.mockResponse,
              storyBase: STORY_BASE,
            },
            null,
            2
          )}
        </pre>
      </div>

      {/* Footer */}
      <div style={{ marginTop: 24, fontSize: 10, color: '#333' }}>
        Route: <code>#/story/music-health-config</code> | Kirobi APK Dev-Stories
      </div>
    </div>
  )
}

export default StoryMusicHealthConfig
