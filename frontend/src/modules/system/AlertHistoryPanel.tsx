import { AlertEntry } from './types'

type Props = {
  alerts: AlertEntry[]
  dismissing: Set<number>
  onDismiss: (ts: number) => void
  onTouchStart: (ts: number, e: React.TouchEvent) => void
  onTouchMove: (ts: number, e: React.TouchEvent) => void
}

export function AlertHistoryPanel({ alerts, dismissing, onDismiss, onTouchStart, onTouchMove }: Props) {
  return (
    <div className="gpuPanel" style={{ marginBottom: 14 }}>
      <strong>🔔 Alert-History (letzte {alerts.length})</strong>
      {alerts.map((alert) => (
        <div
          key={alert.ts}
          className="gpuLine"
          style={{
            flexDirection: 'column',
            alignItems: 'flex-start',
            gap: 2,
            borderBottom: '1px solid #333',
            paddingBottom: 6,
            marginTop: 6,
            opacity: dismissing.has(alert.ts) ? 0.4 : 1,
            transition: 'opacity 0.2s',
            touchAction: 'pan-y',
          }}
          onTouchStart={(e) => onTouchStart(alert.ts, e)}
          onTouchMove={(e) => onTouchMove(alert.ts, e)}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
            <span style={{ color: '#ff9800', fontSize: 11 }}>
              {new Date(alert.ts * 1000).toLocaleString('de-DE')}
            </span>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ color: '#888', fontSize: 11 }}>idle {Math.round(alert.idle_s)}s</span>
              <button
                type="button"
                title="Quittieren"
                disabled={dismissing.has(alert.ts)}
                onClick={() => onDismiss(alert.ts)}
                style={{
                  background: 'none',
                  border: '1px solid #555',
                  borderRadius: 4,
                  color: '#aaa',
                  cursor: 'pointer',
                  fontSize: 11,
                  padding: '1px 6px',
                  lineHeight: '1.4',
                }}
              >
                ✕
              </button>
            </div>
          </div>
          <span style={{ color: '#ccc', fontSize: 11 }}>⚠️ Idle-Alert — {alert.active_connections} Verbindungen aktiv</span>
        </div>
      ))}
    </div>
  )
}
