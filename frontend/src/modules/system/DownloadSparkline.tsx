import { DownloadSnapshot } from './types'

// SVG Download-Sparkline (totals über Zeit)
export function DownloadSparkline({ snapshots }: { snapshots: DownloadSnapshot[] }) {
  if (snapshots.length < 2) {
    return (
      <span style={{ fontSize: 11, color: '#888' }}>
        {snapshots.length === 1 ? `${snapshots[0].total} ↗` : '– keine Daten'}
      </span>
    )
  }
  const W = 120
  const H = 30
  const PAD = 3
  const totals = snapshots.map((s) => s.total)
  const min = Math.min(...totals)
  const max = Math.max(...totals)
  const range = max - min || 1
  const pts = totals.map((v, i) => {
    const x = PAD + (i / (totals.length - 1)) * (W - 2 * PAD)
    const y = H - PAD - ((v - min) / range) * (H - 2 * PAD)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  const lastSnap = snapshots[snapshots.length - 1]
  const lastX = parseFloat(pts[pts.length - 1].split(',')[0])
  const lastY = parseFloat(pts[pts.length - 1].split(',')[1])
  return (
    <svg width={W} height={H} style={{ display: 'block', overflow: 'visible' }}>
      <polyline
        points={pts.join(' ')}
        fill="none"
        stroke="#7986cb"
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
        opacity="0.85"
      />
      {snapshots.map((snap, i) => {
        const [cx, cy] = pts[i].split(',').map(parseFloat)
        const isLast = i === snapshots.length - 1
        return (
          <circle key={i} cx={cx} cy={cy} r={isLast ? 3 : 2} fill="#7986cb" opacity={isLast ? 1 : 0.55}>
            <title>{snap.week}: {snap.total} gesamt (🐛{snap.debug_downloads} ✅{snap.release_downloads})</title>
          </circle>
        )
      })}
      <text x={lastX + 5} y={lastY + 4} fontSize="9" fill="#7986cb">{lastSnap.total}</text>
    </svg>
  )
}
