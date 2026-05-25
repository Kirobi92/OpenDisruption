import { CoverageTrendData, CoverageTrendEntry, CoverageTrendMetric } from './types'

// --- Coverage Sparkline SVG (higher = better = green) ---
function CoverageSparkline({ entries, metricKey }: { entries: CoverageTrendEntry[]; metricKey: string }) {
  if (entries.length < 2) return null

  const W = 140
  const H = 36
  const PAD = 3
  const values = entries.map((e) => {
    const val = (e as unknown as Record<string, number>)[metricKey]
    return typeof val === 'number' ? val : 0
  })
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  // Higher coverage = better → rising line = green
  const improving = values[values.length - 1] >= values[0]
  const lineColor = improving ? '#4caf50' : '#f44336'

  const pts = values.map((v, i) => {
    const x = PAD + (i / (values.length - 1)) * (W - 2 * PAD)
    // Higher value = higher in SVG (better = up)
    const y = H - PAD - ((v - min) / range) * (H - 2 * PAD)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  const lastIdx = values.length - 1
  const lastX = PAD + (lastIdx / (values.length - 1)) * (W - 2 * PAD)
  const lastY = H - PAD - ((values[lastIdx] - min) / range) * (H - 2 * PAD)

  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} aria-label={`Coverage ${metricKey} Sparkline`} role="img">
      <polyline
        points={pts.join(' ')}
        fill="none"
        stroke={lineColor}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
        opacity="0.85"
      />
      {/* Last data point marker */}
      <circle cx={lastX.toFixed(1)} cy={lastY.toFixed(1)} r="2.5" fill={lineColor} />
      {/* Last value label */}
      <text x={lastX + 4} y={lastY + 4} fontSize="8" fill={lineColor}>
        {values[lastIdx].toFixed(0)}%
      </text>
    </svg>
  )
}

// --- Trend Badge (arrow + delta) ---
function TrendBadge({ trend, label }: { trend: CoverageTrendMetric; label: string }) {
  const dirColor =
    trend.direction === '▲' ? '#4caf50' :
    trend.direction === '▼' ? '#f44336' :
    '#aaa'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 64, gap: 1 }}>
      <span style={{ fontSize: 10, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
      <span style={{ fontSize: 24, fontWeight: 700, lineHeight: 1, color: dirColor }}>
        {trend.latest != null ? `${trend.latest.toFixed(0)}%` : '–'}
      </span>
      <span style={{ fontSize: 14, color: dirColor }}>
        {trend.direction}
        {trend.delta !== 0 && (
          <span style={{ fontSize: 10, marginLeft: 2 }}>
            {trend.delta > 0 ? `+${trend.delta.toFixed(1)}` : trend.delta.toFixed(1)}
          </span>
        )}
      </span>
    </div>
  )
}

// --- Main Panel ---
interface CoverageTrendPanelProps {
  coverageTrend: CoverageTrendData
  syncing: boolean
  syncResult: { status: string; message: string; newEntries: number } | null
  onSync: () => void
}

export function CoverageTrendPanel({ coverageTrend, syncing, syncResult, onSync }: CoverageTrendPanelProps) {
  const titleRow = (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: syncing || syncResult ? 6 : 0 }}>
      <div className="systemCardTitle">🧪 Coverage Trend (Vitest)</div>
      <button
        onClick={onSync}
        disabled={syncing}
        style={{
          fontSize: 11,
          padding: '3px 10px',
          borderRadius: 5,
          border: '1px solid #444',
          background: syncing ? '#333' : '#2a2a2a',
          color: syncing ? '#888' : '#64b5f6',
          cursor: syncing ? 'wait' : 'pointer',
        }}
        title="Coverage-Daten von GitHub synchronisieren"
      >
        {syncing ? '⏳ Sync läuft…' : '🔄 Jetzt synchronisieren'}
      </button>
    </div>
  )

  // Sync-Feedback-Zeile
  const syncFeedback = syncResult ? (
    <div style={{
      fontSize: 11,
      padding: '4px 8px',
      borderRadius: 4,
      marginBottom: 6,
      background: syncResult.status === 'ok' ? '#1b3a1b' : syncResult.status === 'no_data' ? '#333' : '#3a1b1b',
      color: syncResult.status === 'ok' ? '#4caf50' : syncResult.status === 'no_data' ? '#888' : '#f44336',
    }}>
      {syncResult.status === 'ok' && syncResult.newEntries > 0 && (
        <>✅ {syncResult.message}</>
      )}
      {syncResult.status === 'ok' && syncResult.newEntries === 0 && (
        <>ℹ️ {syncResult.message}</>
      )}
      {syncResult.status === 'no_data' && (
        <>📭 {syncResult.message}</>
      )}
      {syncResult.status === 'error' && (
        <>❌ {syncResult.message}</>
      )}
    </div>
  ) : null

  if (!coverageTrend.available) {
    return (
      <div className="systemCard" style={{ opacity: 0.6 }}>
        {titleRow}
        {syncFeedback}
        <div style={{ fontSize: 12, color: '#888' }}>
          {coverageTrend.error ? `Fehler: ${coverageTrend.error}` : 'Noch keine Daten — coverage-trend.json nicht gefunden'}
        </div>
      </div>
    )
  }

  const { summary, entries } = coverageTrend
  if (!summary) {
    return (
      <div className="systemCard" style={{ opacity: 0.6 }}>
        {titleRow}
        {syncFeedback}
        <div style={{ fontSize: 12, color: '#888' }}>Keine Summary-Daten vorhanden.</div>
      </div>
    )
  }

  const metrics: { key: string; label: string; trend: CoverageTrendMetric }[] = [
    { key: 'statements_pct', label: 'Stmts', trend: summary.statements_trend },
    { key: 'branches_pct', label: 'Branch', trend: summary.branches_trend },
    { key: 'functions_pct', label: 'Funcs', trend: summary.functions_trend },
    { key: 'lines_pct', label: 'Lines', trend: summary.lines_trend },
  ]

  return (
    <div className="systemCard">
      {titleRow}
      {syncFeedback}

      {/* Latest badges with trend arrows */}
      <div style={{ display: 'flex', justifyContent: 'space-around', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
        {metrics.map((m) => (
          <TrendBadge key={m.key} trend={m.trend} label={m.label} />
        ))}
      </div>

      {/* Sparklines row */}
      {entries.length >= 2 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'center', marginBottom: 8 }}>
          {metrics.map((m) => (
            <div key={m.key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <CoverageSparkline entries={entries} metricKey={m.key} />
            </div>
          ))}
        </div>
      )}

      {/* Meta row */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 11, color: '#888', marginTop: 4 }}>
        {summary.total_runs > 0 && <span>Total Runs: {summary.total_runs}</span>}
        {summary.latest && (
          <span>
            Latest: Run{' '}
            <a
              href={`https://github.com/Kirobi92/OpenDisruption/actions/runs/${summary.latest.run_id}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#64b5f6' }}
            >
              #{summary.latest.run_id}
            </a>
          </span>
        )}
        {summary.latest && (
          <span title={summary.latest.started_at}>
            {summary.latest.started_at?.slice(0, 10) ?? '?'}
          </span>
        )}
      </div>

      {/* Per-metric min/max/avg details */}
      <div style={{ marginTop: 8 }}>
        <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ color: '#666', textAlign: 'left' }}>
              <th style={{ paddingBottom: 2 }}>Metrik</th>
              <th style={{ paddingBottom: 2, textAlign: 'center' }}>Min</th>
              <th style={{ paddingBottom: 2, textAlign: 'center' }}>Max</th>
              <th style={{ paddingBottom: 2, textAlign: 'center' }}>Ø letzte 5</th>
              <th style={{ paddingBottom: 2, textAlign: 'right' }}>Trend</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m) => (
              <tr key={m.key} style={{ borderTop: '1px solid #2a2a2a' }}>
                <td style={{ padding: '2px 0', color: '#aaa' }}>{m.label}</td>
                <td style={{ textAlign: 'center', color: '#888' }}>{m.trend.min != null ? `${m.trend.min.toFixed(0)}%` : '–'}</td>
                <td style={{ textAlign: 'center', color: '#888' }}>{m.trend.max != null ? `${m.trend.max.toFixed(0)}%` : '–'}</td>
                <td style={{ textAlign: 'center', color: '#888' }}>{m.trend.avg_last_5 != null ? `${m.trend.avg_last_5.toFixed(0)}%` : '–'}</td>
                <td style={{ textAlign: 'right', color: m.trend.direction === '▲' ? '#4caf50' : m.trend.direction === '▼' ? '#f44336' : '#aaa' }}>
                  {m.trend.interpretation}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
