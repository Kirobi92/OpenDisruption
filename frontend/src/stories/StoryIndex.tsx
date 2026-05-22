/**
 * StoryIndex — /#/story
 * Automatisch generierte Liste aller verfügbaren Dev-Stories.
 * Wird aus STORY_ROUTES in App.tsx befüllt.
 */

export interface StoryRoute {
  path: string
  label: string
  description?: string
}

// Zentrale Registry — bei neuen Stories hier ergänzen
export const STORY_ROUTES_META: StoryRoute[] = [
  {
    path: '/story/music-health-config',
    label: 'MusicHealthConfigPanel',
    description: 'GET/PUT /api/music-health-config — Refresh-Intervall anzeigen & editieren (3 Szenarien: Default/ENV/Runtime)',
  },
  {
    path: '/story/system-module',
    label: 'SystemModule — DashboardPanel & MilestoneFiredPanel',
    description: 'Isolierte Vorschau: DashboardPanel (MAR/Skip-Rate/Sparkline) + MilestoneFiredPanel (leer & mit Daten) — Mock-Props, kein Backend',
  },
]

export function StoryIndex(): JSX.Element {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#1a1a2e',
        color: '#e0e0e0',
        fontFamily: 'monospace',
        padding: '24px 16px',
      }}
    >
      <div style={{ maxWidth: 640, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ color: '#7986cb', fontSize: 11, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>
            Kirobi Dev-Stories
          </div>
          <h1 style={{ margin: 0, fontSize: 22, color: '#fff', fontWeight: 700 }}>
            📖 Story Index
          </h1>
          <div style={{ color: '#888', fontSize: 12, marginTop: 6 }}>
            {STORY_ROUTES_META.length} {STORY_ROUTES_META.length === 1 ? 'Story' : 'Stories'} verfügbar
          </div>
        </div>

        {/* Story List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {STORY_ROUTES_META.map((story) => (
            <a
              key={story.path}
              href={`#${story.path}`}
              style={{
                display: 'block',
                padding: '14px 16px',
                background: '#16213e',
                border: '1px solid #2a2a4a',
                borderRadius: 8,
                textDecoration: 'none',
                color: 'inherit',
                transition: 'border-color 0.15s ease',
              }}
              onMouseEnter={(e) => {
                ;(e.currentTarget as HTMLAnchorElement).style.borderColor = '#7986cb'
              }}
              onMouseLeave={(e) => {
                ;(e.currentTarget as HTMLAnchorElement).style.borderColor = '#2a2a4a'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                <span style={{ color: '#7986cb', fontSize: 13, fontWeight: 700 }}>
                  {story.label}
                </span>
                <span
                  style={{
                    background: '#0f3460',
                    color: '#7986cb',
                    fontSize: 10,
                    padding: '1px 6px',
                    borderRadius: 4,
                    letterSpacing: 1,
                    textTransform: 'uppercase',
                  }}
                >
                  STORY
                </span>
              </div>
              {story.description && (
                <div style={{ color: '#aaa', fontSize: 12, lineHeight: 1.5 }}>
                  {story.description}
                </div>
              )}
              <div style={{ color: '#555', fontSize: 11, marginTop: 6 }}>
                #{story.path}
              </div>
            </a>
          ))}
        </div>

        {/* Footer */}
        <div
          style={{
            marginTop: 40,
            padding: '12px 0',
            borderTop: '1px solid #2a2a4a',
            color: '#444',
            fontSize: 11,
            textAlign: 'center',
          }}
        >
          Neue Stories in{' '}
          <code style={{ color: '#7986cb' }}>src/stories/StoryIndex.tsx → STORY_ROUTES_META</code>
          {' '}eintragen
        </div>
      </div>
    </div>
  )
}
