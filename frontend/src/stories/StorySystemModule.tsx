import { type DashboardData, type DashboardConfig, type MilestoneFiredData, type MilestoneConfig } from '../modules/system/types'
import { DashboardPanel } from '../modules/system/DashboardPanel'
import { MilestoneFiredPanel } from '../modules/system/MilestoneFiredPanel'

/**
 * Dev-Story: /story/system-module
 *
 * Isolierte Komponenten-Vorschau für DashboardPanel und MilestoneFiredPanel.
 * Alle Sub-Komponenten des SystemModule einzeln sichtbar — kein Backend erforderlich.
 *
 * Usage:
 *   http://localhost:5173/#/story/system-module
 */

// --- Mock-Daten DashboardPanel ---
function makeSnap(timestamp: string, marked_rate_percent: number) {
  const total = 100
  const matched = Math.round(total * marked_rate_percent / 100)
  return {
    timestamp,
    matched_count: matched,
    skip_count: total - matched,
    dry_run_count: 0,
    total_count: total,
    marked_rate_percent,
    skip_rate_percent: 100 - marked_rate_percent,
    top_strategies: [],
    quality_score: marked_rate_percent,
    assessment: marked_rate_percent >= 85 ? 'quality ok' : 'needs review',
  }
}

const MOCK_DASHBOARD_DATA: DashboardData = {
  status: 'ok',
  schema_version: '1',
  snapshots: [
    makeSnap('2026-05-15T00:00:00Z', 80),
    makeSnap('2026-05-16T00:00:00Z', 83),
    makeSnap('2026-05-17T00:00:00Z', 85),
    makeSnap('2026-05-18T00:00:00Z', 82),
    makeSnap('2026-05-19T00:00:00Z', 87),
    makeSnap('2026-05-20T00:00:00Z', 86),
    makeSnap('2026-05-21T00:00:00Z', 87.5),
  ],
  snapshots_total: 7,
  avg_marked_rate: 84.4,
  min_marked_rate: 80,
  max_marked_rate: 87.5,
  latest_assessment: 'quality ok',
  trend: 'up',
}

const MOCK_DASHBOARD_CONFIG: DashboardConfig = {
  marked_rate_green: 85,
  marked_rate_yellow: 70,
}

// --- Mock-Daten MilestoneFiredPanel ---
const MOCK_MILESTONES_EMPTY: MilestoneFiredData = {
  status: 'ok',
  fired: {},
}

const MOCK_MILESTONE_FIRED_WITH_DATA: MilestoneFiredData = {
  status: 'ok',
  fired: {
    'v14': {
      fired_thresholds: [100, 500],
      highest_fired: 500,
      count: 2,
    },
    'v13': {
      fired_thresholds: [100],
      highest_fired: 100,
      count: 1,
    },
  },
}

const MOCK_MILESTONE_CONFIG: MilestoneConfig = {
  status: 'ok',
  config: {
    global_milestones: [100, 500, 1000],
    tag_overrides: {
      'v14': [100, 500, 1000],
      'v13': [100, 500],
    },
  },
  ts: Date.now() / 1000,
}

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <h3 style={{ margin: 0, color: '#7986cb', fontSize: 14 }}>{title}</h3>
      {subtitle && (
        <p style={{ margin: '4px 0 0', fontSize: 11, color: '#666' }}>{subtitle}</p>
      )}
    </div>
  )
}

function StorySection({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <div
      style={{
        background: '#16213e',
        border: '1px solid #2a2a4a',
        borderRadius: 8,
        padding: 16,
        marginBottom: 28,
      }}
    >
      <div style={{ fontSize: 10, color: '#555', marginBottom: 12, letterSpacing: 1, textTransform: 'uppercase' }}>
        RENDERED: {label}
      </div>
      {children}
    </div>
  )
}

export function StorySystemModule() {
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
      <div style={{ marginBottom: 32, borderBottom: '1px solid #333', paddingBottom: 16 }}>
        <h2 style={{ margin: 0, color: '#7986cb', fontSize: 20 }}>
          📖 Dev-Story: SystemModule
        </h2>
        <p style={{ margin: '6px 0 0', fontSize: 11, color: '#888' }}>
          Isolierte Vorschau: DashboardPanel + MilestoneFiredPanel · Mock-Props, kein Backend erforderlich
        </p>
      </div>

      {/* DashboardPanel */}
      <SectionHeader
        title="DashboardPanel"
        subtitle="Match-Log-Report Qualitätskennzahlen — avg MAR, Trend, Sparkline, Snapshots"
      />
      <StorySection label="DashboardPanel (trend=up, avg=84.4%)">
        <DashboardPanel dashboard={MOCK_DASHBOARD_DATA} dashConfig={MOCK_DASHBOARD_CONFIG} />
      </StorySection>

      {/* MilestoneFiredPanel — leer */}
      <SectionHeader
        title="MilestoneFiredPanel — Keine Milestones"
        subtitle="Fallback-UI wenn fired={} und keine Tag-Overrides"
      />
      <StorySection label="MilestoneFiredPanel (empty)">
        <MilestoneFiredPanel milestoneFired={MOCK_MILESTONES_EMPTY} milestoneConfig={null} />
      </StorySection>

      {/* MilestoneFiredPanel — mit Daten */}
      <SectionHeader
        title="MilestoneFiredPanel — Mit Milestone-Einträgen"
        subtitle="v14 (2 gefeuert: 100+500), v13 (1 gefeuert: 100) + Config global_milestones=[100,500,1000]"
      />
      <StorySection label="MilestoneFiredPanel (v14 + v13 fired)">
        <MilestoneFiredPanel
          milestoneFired={MOCK_MILESTONE_FIRED_WITH_DATA}
          milestoneConfig={MOCK_MILESTONE_CONFIG}
        />
      </StorySection>

      {/* Footer */}
      <div
        style={{
          marginTop: 32,
          padding: '12px 0',
          borderTop: '1px solid #222',
          fontSize: 10,
          color: '#333',
        }}
      >
        Route: <code style={{ color: '#7986cb' }}>#/story/system-module</code> | Kirobi APK Dev-Stories
      </div>
    </div>
  )
}

export default StorySystemModule
