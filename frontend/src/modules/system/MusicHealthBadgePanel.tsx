import { MusicHealthData } from './types'

type Props = {
  musicHealth: MusicHealthData
}

export function MusicHealthBadgePanel({ musicHealth }: Props) {
  const hm = musicHealth.heartmula
  const hmColor = hm.available && hm.model_exists ? '#4caf50'
               : hm.available && !hm.model_exists ? '#ffcc00'
               : '#f44336'
  const hmBg = hm.available && hm.model_exists ? '#1b3a1f'
              : hm.available && !hm.model_exists ? '#3a3000'
              : '#3a1b1b'
  const hmLabel = hm.available && hm.model_exists ? '❤️ HeartMuLa: bereit'
                : hm.available && !hm.model_exists ? '💛 HeartMuLa: kein Modell'
                : '❌ HeartMuLa: nicht verfügbar'

  return (
    <div className="gpuPanel" style={{ marginBottom: 14 }}>
      <strong>🎵 Music-Generation Service (Port 8013)</strong>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
        <span style={{
          background: musicHealth.status === 'healthy' ? '#1b3a1f' : '#3a1b1b',
          color: musicHealth.status === 'healthy' ? '#4caf50' : '#f44336',
          border: `1px solid ${musicHealth.status === 'healthy' ? '#4caf50' : '#f44336'}`,
          borderRadius: 4, padding: '2px 8px', fontSize: 11, fontWeight: 'bold',
        }}>
          {musicHealth.status === 'healthy' ? '✅ healthy' : '⚠️ degraded'}
        </span>
        <span
          title={hm.model_path ? `Modell-Pfad: ${hm.model_path}` : undefined}
          style={{ background: hmBg, color: hmColor, border: `1px solid ${hmColor}`, borderRadius: 4, padding: '2px 8px', fontSize: 11 }}
        >
          {hmLabel}
        </span>
        <span style={{
          background: musicHealth.audiocraft.available ? '#1b3a1f' : '#3a1b1b',
          color: musicHealth.audiocraft.available ? '#4caf50' : '#888',
          border: `1px solid ${musicHealth.audiocraft.available ? '#4caf50' : '#555'}`,
          borderRadius: 4, padding: '2px 8px', fontSize: 11,
        }}>
          {musicHealth.audiocraft.available ? '🎧 AudioCraft: aktiv' : '🎧 AudioCraft: Fallback'}
        </span>
        <span style={{
          background: musicHealth.database.ok ? '#1b3a1f' : '#3a1b1b',
          color: musicHealth.database.ok ? '#4caf50' : '#f44336',
          border: `1px solid ${musicHealth.database.ok ? '#4caf50' : '#f44336'}`,
          borderRadius: 4, padding: '2px 8px', fontSize: 11,
        }}>
          {musicHealth.database.ok ? '🗄️ DB: ok' : '🗄️ DB: Fehler'}
        </span>
      </div>
    </div>
  )
}
