import type { DashboardData, DashboardConfig } from './types'
import { Sparkline, markedRateColor } from './Sparkline'

type Props = {
  dashboard: DashboardData
  dashConfig: DashboardConfig
}

export function DashboardPanel({ dashboard, dashConfig }: Props) {
  return (
    <div className="gpuPanel" style={{ marginBottom: 14 }}>
      <strong>
        📊 Match-Log Dashboard
        {' '}
        <span style={{ fontSize: 12, fontWeight: 'normal', color: dashboard.trend === 'up' ? '#4caf50' : dashboard.trend === 'down' ? '#f44336' : '#888' }}>
          {dashboard.trend === 'up' ? '↑' : dashboard.trend === 'down' ? '↓' : '–'}
        </span>
        {' '}
        <span style={{ fontSize: 12, fontWeight: 'normal', color: '#888' }}>
          {dashboard.latest_assessment}
        </span>
      </strong>
      <div className="gpuLine" style={{ marginTop: 8 }}>
        <span>Ø MARKED-Rate</span>
        <span style={{ color: markedRateColor(dashboard.avg_marked_rate, dashConfig.marked_rate_green, dashConfig.marked_rate_yellow) }}>
          {dashboard.avg_marked_rate.toFixed(1)}%
        </span>
      </div>
      {dashboard.snapshots.length >= 2 && (
        <div style={{ marginTop: 8, marginBottom: 4 }}>
          <div style={{ fontSize: 10, color: '#666', marginBottom: 4 }}>MARKED-Rate Verlauf</div>
          <Sparkline snapshots={dashboard.snapshots} green={dashConfig.marked_rate_green} yellow={dashConfig.marked_rate_yellow} />
        </div>
      )}
      <div className="gpuLine">
        <span>Snapshots gesamt</span>
        <span style={{ color: '#ccc' }}>{dashboard.snapshots_total}</span>
      </div>
      <div className="gpuLine">
        <span>Min / Max MARKED</span>
        <span style={{ color: '#888', fontSize: 11 }}>
          {dashboard.min_marked_rate.toFixed(1)}% / {dashboard.max_marked_rate.toFixed(1)}%
        </span>
      </div>
      {dashboard.snapshots.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>Letzte Snapshots</div>
          <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ color: '#666', textAlign: 'left' }}>
                <th style={{ paddingBottom: 4 }}>Datum</th>
                <th style={{ paddingBottom: 4, textAlign: 'center' }}>MARKED</th>
                <th style={{ paddingBottom: 4, textAlign: 'center' }}>SKIP</th>
                <th style={{ paddingBottom: 4, textAlign: 'right' }}>Score</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.snapshots.slice(-10).reverse().map((snap, i) => (
                <tr key={i} style={{ borderTop: '1px solid #2a2a2a' }}>
                  <td style={{ padding: '3px 0', color: '#aaa' }}>{snap.timestamp.slice(0, 10)}</td>
                  <td style={{ textAlign: 'center', color: markedRateColor(snap.marked_rate_percent, dashConfig.marked_rate_green, dashConfig.marked_rate_yellow) }}>
                    {snap.marked_rate_percent.toFixed(1)}%
                  </td>
                  <td style={{ textAlign: 'center', color: '#888' }}>{snap.skip_rate_percent.toFixed(1)}%</td>
                  <td style={{ textAlign: 'right', color: '#666' }}>{snap.assessment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
