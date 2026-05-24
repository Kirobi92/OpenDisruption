import { DashboardSnapshot } from './types'

// MARKED-Rate Farbschwellen — werden zur Laufzeit via /api/dashboard-config aus dem Backend geladen
// Build-time ENV (VITE_MARKED_RATE_GREEN/YELLOW) dienen nur als Fallback falls der Endpoint nicht erreichbar ist
export const BUILD_TIME_GREEN = Number(import.meta.env.VITE_MARKED_RATE_GREEN ?? 50)
export const BUILD_TIME_YELLOW = Number(import.meta.env.VITE_MARKED_RATE_YELLOW ?? 20)

export function markedRateColor(rate: number, green: number, yellow: number): string {
  if (rate >= green) return '#4caf50'
  if (rate >= yellow) return '#ffcc00'
  return '#f44336'
}

// SVG Sparkline für MARKED-Rate über letzte Snapshots
export function Sparkline({ snapshots, green, yellow }: { snapshots: DashboardSnapshot[]; green: number; yellow: number }) {
  if (snapshots.length < 2) return null

  const W = 180
  const H = 40
  const PAD = 4
  const rates = snapshots.map((s) => s.marked_rate_percent)
  const min = Math.min(...rates)
  const max = Math.max(...rates)
  const range = max - min || 1

  const pts = rates.map((r, i) => {
    const x = PAD + (i / (rates.length - 1)) * (W - 2 * PAD)
    const y = H - PAD - ((r - min) / range) * (H - 2 * PAD)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  const polyline = pts.join(' ')
  const lastRate = rates[rates.length - 1]
  const lastX = parseFloat(pts[pts.length - 1].split(',')[0])
  const lastY = parseFloat(pts[pts.length - 1].split(',')[1])

  return (
    <svg width={W} height={H} style={{ display: 'block', overflow: 'visible' }}>
      <polyline
        points={polyline}
        fill="none"
        stroke={markedRateColor(lastRate, green, yellow)}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
        opacity="0.85"
      />
      {snapshots.map((snap, i) => {
        const [cx, cy] = pts[i].split(',').map(parseFloat)
        const isLast = i === snapshots.length - 1
        const dateLabel = snap.timestamp.slice(0, 10)
        const tooltipText = `${dateLabel} — MARKED: ${snap.marked_rate_percent.toFixed(1)}%`
        return (
          <circle key={i} cx={cx} cy={cy} r={isLast ? 3 : 2} fill={markedRateColor(snap.marked_rate_percent, green, yellow)} opacity={isLast ? 1 : 0.6}>
            <title>{tooltipText}</title>
          </circle>
        )
      })}
      <text x={lastX + 5} y={lastY + 4} fontSize="9" fill={markedRateColor(lastRate, green, yellow)}>
        {lastRate.toFixed(1)}%
      </text>
    </svg>
  )
}
