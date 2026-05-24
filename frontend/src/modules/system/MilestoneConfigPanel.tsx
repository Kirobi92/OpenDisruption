import { type MilestoneConfig } from './types'

type Props = {
  milestoneConfig: MilestoneConfig
  mcEditMode: boolean
  mcGlobalInput: string
  mcTagInput: string
  mcTagThresholdsInput: string
  mcSaving: boolean
  mcError: string
  mcSuccess: string
  onToggleEdit: () => void
  onGlobalInputChange: (v: string) => void
  onTagInputChange: (v: string) => void
  onTagThresholdsInputChange: (v: string) => void
  onSaveGlobal: () => void
  onSaveTag: () => void
  onDeleteTag: (tag: string) => void
}

export function MilestoneConfigPanel({
  milestoneConfig,
  mcEditMode,
  mcGlobalInput,
  mcTagInput,
  mcTagThresholdsInput,
  mcSaving,
  mcError,
  mcSuccess,
  onToggleEdit,
  onGlobalInputChange,
  onTagInputChange,
  onTagThresholdsInputChange,
  onSaveGlobal,
  onSaveTag,
  onDeleteTag,
}: Props) {
  return (
    <div className="gpuPanel" style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong>⚙️ Milestone-Config bearbeiten</strong>
        <button
          type="button"
          onClick={onToggleEdit}
          style={{ fontSize: 11, padding: '2px 10px', cursor: 'pointer' }}
        >{mcEditMode ? 'Schließen' : 'Bearbeiten'}</button>
      </div>

      {/* Live-Ansicht der aktuellen Config */}
      <div style={{ marginTop: 8 }}>
        <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>Globale Thresholds</div>
        <div style={{ fontSize: 12, color: '#7986cb' }}>
          {milestoneConfig.config.global_milestones.length > 0
            ? milestoneConfig.config.global_milestones.join(', ')
            : <span style={{ color: '#555', fontStyle: 'italic' }}>Keine konfiguriert</span>}
        </div>
      </div>

      {Object.keys(milestoneConfig.config.tag_overrides).length > 0 && (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>Tag-Overrides</div>
          <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ color: '#666' }}>
                <th style={{ textAlign: 'left', paddingBottom: 4 }}>Tag</th>
                <th style={{ textAlign: 'left', paddingBottom: 4 }}>Thresholds</th>
                {mcEditMode && <th style={{ paddingBottom: 4 }}></th>}
              </tr>
            </thead>
            <tbody>
              {Object.entries(milestoneConfig.config.tag_overrides).map(([tag, thresholds]) => (
                <tr key={tag} style={{ borderTop: '1px solid #2a2a2a' }}>
                  <td style={{ padding: '3px 0', color: '#aaa' }}>{tag}</td>
                  <td style={{ color: '#7986cb' }}>{(thresholds as number[]).join(', ')}</td>
                  {mcEditMode && (
                    <td style={{ textAlign: 'right' }}>
                      <button
                        type="button"
                        disabled={mcSaving}
                        onClick={() => onDeleteTag(tag)}
                        style={{ fontSize: 10, padding: '1px 6px', cursor: 'pointer', color: '#f44336', border: '1px solid #f44336', background: 'none', borderRadius: 3 }}
                      >🗑️</button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {mcEditMode && (
        <div style={{ marginTop: 12, borderTop: '1px solid #333', paddingTop: 10 }}>
          {/* Globale Thresholds ändern */}
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>Globale Thresholds setzen (kommagetrennt)</div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <input
                type="text"
                value={mcGlobalInput}
                onChange={(e) => onGlobalInputChange(e.target.value)}
                placeholder={milestoneConfig.config.global_milestones.join(', ') || '5, 10, 25, 50, 100'}
                style={{ flex: 1, fontSize: 12, padding: '4px 8px', background: '#1e1e1e', border: '1px solid #444', color: '#ccc', borderRadius: 4 }}
                aria-label="Globale Milestone-Thresholds"
              />
              <button
                type="button"
                disabled={mcSaving || !mcGlobalInput.trim()}
                onClick={onSaveGlobal}
                style={{ fontSize: 11, padding: '4px 12px', cursor: mcSaving ? 'default' : 'pointer', opacity: mcSaving ? 0.5 : 1 }}
              >Speichern</button>
            </div>
          </div>

          {/* Tag-Override hinzufügen */}
          <div>
            <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>Tag-Override hinzufügen / überschreiben</div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
              <input
                type="text"
                value={mcTagInput}
                onChange={(e) => onTagInputChange(e.target.value)}
                placeholder="z.B. v10.8-debug"
                style={{ width: 130, fontSize: 12, padding: '4px 8px', background: '#1e1e1e', border: '1px solid #444', color: '#ccc', borderRadius: 4 }}
                aria-label="Release-Tag für Override"
              />
              <input
                type="text"
                value={mcTagThresholdsInput}
                onChange={(e) => onTagThresholdsInputChange(e.target.value)}
                placeholder="3, 5, 10"
                style={{ flex: 1, fontSize: 12, padding: '4px 8px', background: '#1e1e1e', border: '1px solid #444', color: '#ccc', borderRadius: 4 }}
                aria-label="Thresholds für Tag-Override"
              />
              <button
                type="button"
                disabled={mcSaving || !mcTagInput.trim() || !mcTagThresholdsInput.trim()}
                onClick={onSaveTag}
                style={{ fontSize: 11, padding: '4px 12px', cursor: mcSaving ? 'default' : 'pointer', opacity: mcSaving ? 0.5 : 1 }}
              >Setzen</button>
            </div>
          </div>
        </div>
      )}

      {mcError && <div style={{ marginTop: 8, color: '#f44336', fontSize: 11 }}>⚠️ {mcError}</div>}
      {mcSuccess && <div style={{ marginTop: 8, color: '#4caf50', fontSize: 11 }}>{mcSuccess}</div>}
    </div>
  )
}
