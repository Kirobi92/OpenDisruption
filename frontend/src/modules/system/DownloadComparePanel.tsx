import { type DownloadCompareData } from './types'

type Props = {
  downloadCompare: DownloadCompareData
}

export function DownloadComparePanel({ downloadCompare }: Props) {
  return (
    <div className="gpuPanel" style={{ marginBottom: 14, overflowX: 'auto' }}>
      <strong>📊 APK Download-Vergleich (Tag-Matrix)</strong>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 8, fontSize: 11 }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left', color: '#7986cb', padding: '4px 8px', borderBottom: '1px solid #333' }}>Woche</th>
            {downloadCompare.tags.map((tag) => (
              <th key={tag} style={{ textAlign: 'center', color: '#7986cb', padding: '4px 8px', borderBottom: '1px solid #333', whiteSpace: 'nowrap' }}>
                {tag}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {downloadCompare.weeks.map((week) => (
            <tr key={week} style={{ borderBottom: '1px solid #1e1e1e' }}>
              <td style={{ color: '#888', padding: '3px 8px', whiteSpace: 'nowrap' }}>{week}</td>
              {downloadCompare.tags.map((tag) => {
                const cell = downloadCompare.matrix[week]?.[tag]
                return (
                  <td key={tag} style={{ textAlign: 'center', padding: '3px 8px', color: cell ? '#ccc' : '#333' }}>
                    {cell
                      ? <span title={`🐛 ${cell.debug} debug  ✅ ${cell.release} release`}>{cell.total}</span>
                      : '—'}
                  </td>
                )
              })}
            </tr>
          ))}
          {/* Summen-Zeile */}
          <tr style={{ borderTop: '2px solid #333', fontWeight: 'bold' }}>
            <td style={{ color: '#aaa', padding: '4px 8px' }}>Gesamt</td>
            {downloadCompare.tags.map((tag) => (
              <td key={tag} style={{ textAlign: 'center', padding: '4px 8px', color: '#7986cb' }}>
                {downloadCompare.tag_totals[tag] ?? 0}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  )
}
