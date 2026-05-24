import { type ScTrendData, type ScTrendEntry } from './types'

// SVG Sparkline für SC_ISSUE_COUNT (weniger = besser → Trend-Farbe invertiert)
function ScSparkline({ entries }: { entries: ScTrendEntry[] }) {
  if (entries.length < 2) return null

  const W = 200
  const H = 48
  const PAD = 4
  const counts = entries.map((e) => e.sc_issue_count)
  const min = Math.min(...counts)
  const max = Math.max(...counts)
  const range = max - min || 1

  // Letzter Wert ≤ Erster Wert → Verbesserung (grün), sonst rot
  const improving = counts[counts.length - 1] <= counts[0]
  const lineColor = improving ? '#4caf50' : '#f44336'

  const pts = counts.map((c, i) => {
    const x = PAD + (i / (counts.length - 1)) * (W - 2 * PAD)
    // Invertiert: niedrigerer Wert = höher im SVG (besser = oben)
    const y = PAD + ((c - min) / range) * (H - 2 * PAD)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  const lastIdx = counts.length - 1
  const lastX = PAD + (lastIdx / (counts.length - 1)) * (W - 2 * PAD)
  const lastY = PAD + ((counts[lastIdx] - min) / range) * (H - 2 * PAD)

  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} aria-label="SC Issue Count Sparkline" role="img">
      <polyline
        points={pts.join(' ')}
        fill="none"
        stroke={lineColor}
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {/* Letzter Datenpunkt markieren */}
      <circle cx={lastX.toFixed(1)} cy={lastY.toFixed(1)} r="3.5" fill={lineColor} />
    </svg>
  )
}

function trendBadgeStyle(direction: string | null): React.CSSProperties {
  if (direction === '▼') return { color: '#4caf50', fontWeight: 700 }   // weniger Findings = gut
  if (direction === '▲') return { color: '#f44336', fontWeight: 700 }   // mehr Findings = schlecht
  return { color: '#aaa', fontWeight: 700 }
}

interface ScTrendPanelProps {
  scTrend: ScTrendData
}

export function ScTrendPanel({ scTrend }: ScTrendPanelProps) {
  if (!scTrend.available) {
    return (
      <div className="systemCard" style={{ opacity: 0.6 }}>
        <div className="systemCardTitle">🔍 SC Issue Trend</div>
        <div style={{ fontSize: 12, color: '#888' }}>
          {scTrend.error ? `Fehler: ${scTrend.error}` : 'Noch keine Daten (sc-trend.json nicht gefunden)'}
        </div>
      </div>
    )
  }

  const { summary, entries } = scTrend

  return (
    <div className="systemCard">
      <div className="systemCardTitle">🔍 SC Issue Trend</div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
        {/* latest_count Badge */}
        {summary?.latest_count != null && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 56 }}>
            <span style={{
              fontSize: 28,
              fontWeight: 800,
              lineHeight: 1,
              color: summary.latest_count === 0 ? '#4caf50' : summary.latest_count <= 5 ? '#ffcc00' : '#f44336',
            }}>
              {summary.latest_count}
            </span>
            <span style={{ fontSize: 10, color: '#888', marginTop: 2 }}>Findings</span>
          </div>
        )}

        {/* Sparkline */}
        {entries.length >= 2 && (
          <div style={{ flex: 1, minWidth: 120 }}>
            <ScSparkline entries={entries} />
          </div>
        )}

        {/* Trend-Pfeil + Interpretation */}
        {summary && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 100 }}>
            <span style={{ fontSize: 22, ...trendBadgeStyle(summary.trend_direction) }}>
              {summary.trend_direction ?? '→'}
              {summary.trend_delta != null && (
                <span style={{ fontSize: 13, marginLeft: 4 }}>
                  {summary.trend_delta > 0 ? `+${summary.trend_delta}` : summary.trend_delta}
                </span>
              )}
            </span>
            <span style={{ fontSize: 11, color: '#bbb' }}>{summary.interpretation}</span>
          </div>
        )}
      </div>

      {/* Meta-Zeile */}
      {summary && (
        <div style={{ display: 'flex', gap: 16, marginTop: 8, flexWrap: 'wrap', fontSize: 11, color: '#888' }}>
          {summary.valid_runs > 0 && <span>Runs: {summary.valid_runs}</span>}
          {summary.min_count != null && <span>Min: {summary.min_count}</span>}
          {summary.max_count != null && <span>Max: {summary.max_count}</span>}
          {summary.avg_last_5 != null && <span>Ø letzte 5: {summary.avg_last_5}</span>}
        </div>
      )}
    </div>
  )
}
