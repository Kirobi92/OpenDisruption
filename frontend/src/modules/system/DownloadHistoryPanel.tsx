import { useMemo } from 'react'
import { type DownloadHistoryData } from './types'
import { DownloadSparkline } from './DownloadSparkline'

type Props = {
  downloadHistory: DownloadHistoryData
  dlHistPage: Record<string, number>
  focusedTag: string | null
  dlAriaAnnouncement: string
  dlSwipePulse: Record<string, boolean>
  isDesktopUA: boolean
  onPageChange: (tag: string, page: number) => void
  onFocus: (tag: string) => void
  onBlur: () => void
  onTouchStart: (tag: string, e: React.TouchEvent) => void
  onTouchEnd: (tag: string, e: React.TouchEvent) => void
}

const PAGE_SIZE = 8

export function DownloadHistoryPanel({
  downloadHistory,
  dlHistPage,
  focusedTag,
  dlAriaAnnouncement,
  dlSwipePulse,
  isDesktopUA,
  onPageChange,
  onFocus,
  onBlur,
  onTouchStart,
  onTouchEnd,
}: Props) {
  return (
    <div className="gpuPanel" style={{ marginBottom: 14 }}>
      {/* aria-live Region für Screenreader-Ankündigung bei Tab-Fokus */}
      <div
        aria-live="polite"
        aria-atomic="true"
        style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0,0,0,0)', whiteSpace: 'nowrap' }}
      >
        {dlAriaAnnouncement}
      </div>
      <strong>📥 APK Download-History</strong>
      {Object.entries(downloadHistory.tags).map(([tag, entry]) => {
        const snaps = entry.snapshots
        const totalPages = Math.max(1, Math.ceil(snaps.length / PAGE_SIZE))
        // pageIdx 0 = neueste Seite
        const pageIdx = dlHistPage[tag] ?? 0
        const clampedPage = Math.min(pageIdx, totalPages - 1)
        // Slice: pageIdx 0 = last PAGE_SIZE snaps
        const fromEnd = (clampedPage + 1) * PAGE_SIZE
        const toEnd = clampedPage * PAGE_SIZE
        const pageSnaps = snaps.slice(
          Math.max(0, snaps.length - fromEnd),
          snaps.length - toEnd
        )
        const canPrev = clampedPage < totalPages - 1 // older
        const canNext = clampedPage > 0 // newer
        return (
          <div
            key={tag}
            tabIndex={0}
            role="region"
            aria-label={`Download-Verlauf für ${tag}${focusedTag === tag ? ' — navigierbar mit Pfeiltasten' : ''}`}
            onFocus={() => onFocus(tag)}
            onBlur={onBlur}
            onTouchStart={(e) => onTouchStart(tag, e)}
            onTouchEnd={(e) => onTouchEnd(tag, e)}
            style={{
              marginTop: 10,
              borderTop: '1px solid #2a2a2a',
              paddingTop: 8,
              outline: focusedTag === tag ? '2px solid #7986cb' : 'none',
              outlineOffset: focusedTag === tag ? 3 : 0,
              borderRadius: focusedTag === tag ? 6 : 0,
              paddingLeft: focusedTag === tag ? 6 : 0,
              paddingRight: focusedTag === tag ? 6 : 0,
              transition: 'outline 0.15s ease, padding 0.15s ease, opacity 0.15s ease',
              touchAction: 'pan-y',
              opacity: dlSwipePulse[tag] ? 0.3 : 1,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
              <span style={{ color: '#7986cb', fontWeight: 'bold', fontSize: 12 }}>{tag}</span>
              <span style={{ color: '#aaa', fontSize: 11 }}>
                {entry.total_downloads} total {entry.trend}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 4 }}>
              <span style={{ fontSize: 10, color: '#888' }}>🐛 Debug: {entry.latest_debug}</span>
              <span style={{ fontSize: 10, color: '#888' }}>✅ Release: {entry.latest_release}</span>
              {entry.latest_week && <span style={{ fontSize: 10, color: '#555' }}>{entry.latest_week}</span>}
            </div>
            <DownloadSparkline snapshots={pageSnaps} />
            {totalPages > 1 && (
              <div style={{ display: 'flex', gap: 6, marginTop: 6, alignItems: 'center' }}>
                <button
                  type="button"
                  disabled={!canPrev}
                  onClick={() => onPageChange(tag, clampedPage + 1)}
                  aria-label="Ältere Einträge"
                  style={{ fontSize: 10, padding: '2px 7px', opacity: canPrev ? 1 : 0.3, cursor: canPrev ? 'pointer' : 'default' }}
                >←</button>
                {/* Bullet-Dot Seiten-Indikatoren statt "1/N" Textlabel */}
                <div
                  role="tablist"
                  aria-label={`Seite ${clampedPage + 1} von ${totalPages}`}
                  style={{ display: 'flex', gap: 4, alignItems: 'center' }}
                >
                  {Array.from({ length: totalPages }, (_, i) => (
                    <button
                      key={i}
                      type="button"
                      role="tab"
                      aria-selected={i === clampedPage}
                      aria-label={`Seite ${i + 1}`}
                      onClick={() => onPageChange(tag, i)}
                      style={{
                        width: i === clampedPage ? 8 : 6,
                        height: i === clampedPage ? 8 : 6,
                        borderRadius: '50%',
                        background: i === clampedPage ? '#7986cb' : '#444',
                        border: 'none',
                        padding: 0,
                        cursor: 'pointer',
                        transition: 'background 0.2s ease, width 0.2s ease, height 0.2s ease',
                        flexShrink: 0,
                      }}
                    />
                  ))}
                </div>
                <button
                  type="button"
                  disabled={!canNext}
                  onClick={() => onPageChange(tag, clampedPage - 1)}
                  aria-label="Neuere Einträge"
                  style={{ fontSize: 10, padding: '2px 7px', opacity: canNext ? 1 : 0.3, cursor: canNext ? 'pointer' : 'default' }}
                >→</button>
                {isDesktopUA && (
                  <span
                    aria-hidden="true"
                    title="Pfeiltasten ← → navigieren zwischen Seiten"
                    style={{
                      fontSize: 9,
                      color: '#555',
                      marginLeft: 4,
                      userSelect: 'none',
                      fontFamily: 'monospace',
                      letterSpacing: '0.5px',
                    }}
                  >← →</span>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
