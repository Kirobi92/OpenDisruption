import type { ScAlertEvent } from './types'

const PAGE_LIMIT = 5

type Props = {
  scAlerts: ScAlertEvent[]
  total: number
  offset: number
  hasMore: boolean
  onPrev: () => void
  onNext: () => void
}

export function ScAlertsPanel({ scAlerts, total, offset, hasMore, onPrev, onNext }: Props) {
  const currentPage = Math.floor(offset / PAGE_LIMIT) + 1
  const totalPages = Math.ceil(total / PAGE_LIMIT) || 1

  if (scAlerts.length === 0 && offset === 0) {
    return (
      <div className="gpuPanel" style={{ marginBottom: 14 }}>
        <strong>🛡️ SC-Alert-History</strong>
        <div className="systemMeta" style={{ marginTop: 8, color: '#888' }}>
          Keine SC-Alerts bisher — shellcheck sauber ✅
        </div>
      </div>
    )
  }

  return (
    <div className="gpuPanel" style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong>🛡️ SC-Alert-History ({total} gesamt)</strong>
        {totalPages > 1 && (
          <span style={{ fontSize: 11, color: '#888' }}>
            Seite {currentPage} / {totalPages}
          </span>
        )}
      </div>
      <div style={{ overflowX: 'auto', marginTop: 8 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
          <thead>
            <tr>
              <th style={thStyle}>Zeitstempel</th>
              <th style={thStyle}>Run-ID</th>
              <th style={thStyle}>SC-Count</th>
              <th style={thStyle}>Threshold</th>
              <th style={thStyle}>Delta</th>
            </tr>
          </thead>
          <tbody>
            {scAlerts.map((alert) => {
              const date = new Date(alert.timestamp).toLocaleString('de-DE')
              return (
                <tr key={`${alert.run_id}-${alert.timestamp}`} style={{ borderBottom: '1px solid #333' }}>
                  <td style={tdStyle}>
                    <span style={{ color: '#ff9800' }}>{date}</span>
                  </td>
                  <td style={tdStyle}>
                    <a
                      href={`https://github.com/Kirobi92/OpenDisruption/actions/runs/${alert.run_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: '#64b5f6', textDecoration: 'none' }}
                      title={`Run vom ${alert.run_started_at}`}
                    >
                      #{alert.run_id}
                    </a>
                  </td>
                  <td style={{ ...tdStyle, color: alert.sc_issue_count > 0 ? '#ff5252' : '#4caf50', fontWeight: 'bold' }}>
                    {alert.sc_issue_count}
                  </td>
                  <td style={{ ...tdStyle, color: '#aaa' }}>{alert.threshold}</td>
                  <td style={{ ...tdStyle, color: alert.delta > 0 ? '#ff5252' : alert.delta < 0 ? '#4caf50' : '#aaa' }}>
                    {alert.delta > 0 ? `+${alert.delta}` : alert.delta}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
          <button
            onClick={onPrev}
            disabled={offset === 0}
            aria-label="Vorherige Seite SC-Alerts"
            style={{
              ...navBtnStyle,
              opacity: offset === 0 ? 0.3 : 1,
              cursor: offset === 0 ? 'not-allowed' : 'pointer',
            }}
          >
            ← Prev
          </button>
          <button
            onClick={onNext}
            disabled={!hasMore}
            aria-label="Nächste Seite SC-Alerts"
            style={{
              ...navBtnStyle,
              opacity: !hasMore ? 0.3 : 1,
              cursor: !hasMore ? 'not-allowed' : 'pointer',
            }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}

const navBtnStyle: React.CSSProperties = {
  padding: '3px 10px',
  fontSize: 11,
  background: '#2a2a2a',
  color: '#ccc',
  border: '1px solid #444',
  borderRadius: 4,
}

const thStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '4px 6px',
  color: '#888',
  fontWeight: 'normal',
  borderBottom: '1px solid #444',
  whiteSpace: 'nowrap',
}

const tdStyle: React.CSSProperties = {
  padding: '3px 6px',
  color: '#ccc',
  verticalAlign: 'middle',
}
