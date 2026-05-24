import { type AudioStatus } from './types'

type Props = {
  audioStatus: AudioStatus
}

export function AudioStatusPanel({ audioStatus }: Props) {
  return (
    <div className="gpuPanel" style={{ marginBottom: 14 }}>
      <strong>🎙️ Kirobi Audio — Live-Verbindung</strong>
      <div className="gpuLine">
        <span>Aktive Verbindungen</span>
        <span style={{ color: audioStatus.active_connections > 0 ? '#4caf50' : '#888' }}>
          {audioStatus.active_connections > 0 ? `● ${audioStatus.active_connections}` : '○ keine'}
        </span>
      </div>
      <div className="gpuLine">
        <span>Idle seit</span>
        <span style={{ color: audioStatus.idle_s > 300 ? '#ff9800' : '#ccc' }}>
          {Math.round(audioStatus.idle_s)}s {audioStatus.idle_s > 300 ? '⚠️' : ''}
        </span>
      </div>
      <div className="gpuLine">
        <span>Status</span>
        <span style={{ color: audioStatus.status === 'ok' ? '#4caf50' : '#f44336' }}>
          {audioStatus.status.toUpperCase()}
        </span>
      </div>
      <div className="gpuLine">
        <span>Letzter Alert</span>
        <span style={{ color: audioStatus.last_alert_ts ? '#ff9800' : '#4caf50' }}>
          {audioStatus.last_alert_ts
            ? new Date(audioStatus.last_alert_ts * 1000).toLocaleTimeString('de-DE')
            : '✅ kein Alert'}
        </span>
      </div>
      {audioStatus.idle_limit_mode && (
        <div className="gpuLine">
          <span>Modus</span>
          <span style={{ color: audioStatus.idle_limit_mode === 'day' ? '#ffcc00' : '#7986cb' }}>
            {audioStatus.idle_limit_mode === 'day' ? '☀️ Tag' : audioStatus.idle_limit_mode === 'night' ? '🌙 Nacht' : audioStatus.idle_limit_mode}
          </span>
        </div>
      )}
      {audioStatus.idle_limit_s != null && (
        <div className="gpuLine">
          <span>Idle-Schwelle</span>
          <span style={{ color: '#888' }}>{Math.round(audioStatus.idle_limit_s / 60)} Min</span>
        </div>
      )}
    </div>
  )
}
