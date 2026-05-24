import { type MilestoneFiredData, type MilestoneConfig } from './types'

type Props = {
  milestoneFired: MilestoneFiredData | null
  milestoneConfig: MilestoneConfig | null
}

export function MilestoneFiredPanel({ milestoneFired, milestoneConfig }: Props) {
  // Alle konfigurierten Tags aus milestone-config + fired zusammenführen
  const configTags = milestoneConfig
    ? Object.keys(milestoneConfig.config.tag_overrides).length > 0
      ? Object.keys(milestoneConfig.config.tag_overrides)
      : []
    : []
  const firedTags = milestoneFired ? Object.keys(milestoneFired.fired) : []
  const allTags = Array.from(new Set([...firedTags, ...configTags])).sort()

  return (
    <div className="gpuPanel" style={{ marginBottom: 14 }}>
      <strong>🏆 Milestone-Status (gefeuerte Alerts)</strong>
      {allTags.length === 0 ? (
        <p style={{ fontSize: 11, color: '#888', marginTop: 8 }}>
          Noch keine Milestones konfiguriert.
        </p>
      ) : (
        <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse', marginTop: 8 }}>
          <thead>
            <tr style={{ color: '#666', textAlign: 'left' }}>
              <th style={{ paddingBottom: 4 }}>Release-Tag</th>
              <th style={{ paddingBottom: 4, textAlign: 'center' }}>Höchster</th>
              <th style={{ paddingBottom: 4, textAlign: 'center' }}>Anzahl</th>
              <th style={{ paddingBottom: 4, textAlign: 'right' }}>Alle Thresholds</th>
            </tr>
          </thead>
          <tbody>
            {allTags.map((tag) => {
              const entry = milestoneFired?.fired[tag]
              const thresholds = milestoneConfig?.config.tag_overrides[tag]
                ?? milestoneConfig?.config.global_milestones
                ?? []
              const hasFired = entry && entry.count > 0
              return (
                <tr key={tag} style={{ borderTop: '1px solid #2a2a2a' }}>
                  <td style={{ padding: '3px 0', color: '#aaa' }}>{tag}</td>
                  <td style={{ textAlign: 'center', color: hasFired ? '#ffcc00' : '#555', fontWeight: hasFired ? 'bold' : 'normal' }}>
                    {hasFired ? `🎉 ${entry.highest_fired}` : '—'}
                  </td>
                  <td style={{ textAlign: 'center', color: '#888' }}>
                    {entry ? entry.count : 0}
                  </td>
                  <td style={{ textAlign: 'right', fontSize: 10 }}>
                    {hasFired ? (
                      <span style={{ color: '#666' }}>{entry.fired_thresholds.join(', ')}</span>
                    ) : (
                      <span style={{ color: '#444', fontStyle: 'italic' }}>
                        Noch keine Milestones erreicht
                        {thresholds.length > 0 ? ` (nächster: ${Math.min(...thresholds)})` : ''}
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
