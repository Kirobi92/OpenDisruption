'use client';

/**
 * DownloadHistoryPanel — APK Download-History mit Pagination
 *
 * OPE-188: Keyboard-Shortcut Anzeige im UI — kleines Tooltip/Hint „← →"
 *          wenn totalPages > 1 und Desktop-User-Agent erkannt
 * OPE-189: Seiten-Indikator Dots (bullet indicators statt Zahlen)
 * OPE-190: Accessibility aria-live Region: bei Tab-Fokus Ansage
 *
 * API: GET /api/proxy/api/download-history?page=1&page_size=5
 * ENV: KIROBI_DOWNLOAD_HISTORY_PAGE_SIZE (default 5) im API-Service
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import useSWR from 'swr';

// ── Types ────────────────────────────────────────────────────────────────────

interface DownloadHistorySnapshot {
  week: string;
  date: string;
  debug_downloads: number;
  release_downloads: number;
  total: number;
}

interface DownloadHistoryTagEntry {
  tag: string;
  snapshots: DownloadHistorySnapshot[];
  total_downloads: number;
  latest_week: string | null;
}

interface DownloadHistoryResponse {
  tags: DownloadHistoryTagEntry[];
  page: number;
  page_size: number;
  total_pages: number;
  total_tags: number;
  schema_version: string;
}

// ── Fetcher ──────────────────────────────────────────────────────────────────

const fetcher = (url: string) =>
  fetch(url).then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json() as Promise<DownloadHistoryResponse>;
  });

// ── Desktop-Detection ────────────────────────────────────────────────────────

function useIsDesktop(): boolean {
  const [isDesktop, setIsDesktop] = useState(false);
  useEffect(() => {
    const ua = navigator.userAgent;
    // Mobile/Tablet: Touch-only Geräte schließen wir aus
    const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua);
    setIsDesktop(!isMobile && window.innerWidth >= 768);
  }, []);
  return isDesktop;
}

// ── Sparkline Mini (Text-basiert) ────────────────────────────────────────────

function SparklineDots({ values }: { values: number[] }) {
  if (values.length === 0) return null;
  const max = Math.max(...values, 1);
  const bars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
  return (
    <span className="font-mono text-xs text-aurora-cyan/70 tracking-tight" aria-hidden="true">
      {values.slice(-8).map((v, i) => {
        const idx = Math.min(Math.floor((v / max) * (bars.length - 1)), bars.length - 1);
        return <span key={i}>{bars[idx]}</span>;
      })}
    </span>
  );
}

// ── Page Indicator Dots (OPE-189) ────────────────────────────────────────────

function PageDots({
  total,
  current,
  onSelect,
}: {
  total: number;
  current: number;
  onSelect: (page: number) => void;
}) {
  if (total <= 1) return null;
  return (
    <div className="flex items-center gap-1.5" role="group" aria-label="Seiten-Indikator">
      {Array.from({ length: total }, (_, i) => i + 1).map((p) => (
        <button
          key={p}
          onClick={() => onSelect(p)}
          aria-label={`Seite ${p}`}
          aria-current={p === current ? 'page' : undefined}
          className={`rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-aurora-cyan/60 ${
            p === current
              ? 'h-2.5 w-2.5 bg-aurora-cyan'
              : 'h-2 w-2 bg-white/20 hover:bg-white/40'
          }`}
        />
      ))}
    </div>
  );
}

// ── Keyboard Shortcut Hint (OPE-188) ─────────────────────────────────────────

function KeyboardHint({ show }: { show: boolean }) {
  if (!show) return null;
  return (
    <span
      className="inline-flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-xs text-white/40 select-none"
      aria-hidden="true"
      title="Navigiere mit Pfeiltasten"
    >
      <kbd className="font-mono">←</kbd>
      <kbd className="font-mono">→</kbd>
    </span>
  );
}

// ── Tag Card ──────────────────────────────────────────────────────────────────

function TagCard({ entry }: { entry: DownloadHistoryTagEntry }) {
  const totals = entry.snapshots.map((s) => s.total);
  const latest = entry.snapshots[entry.snapshots.length - 1];

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-semibold text-white font-mono">{entry.tag}</span>
        <span className="text-xs text-white/50">{entry.total_downloads} ges.</span>
      </div>
      {latest && (
        <div className="flex items-center gap-3 text-xs text-white/60">
          <span>🐛 {latest.debug_downloads}</span>
          <span>✅ {latest.release_downloads}</span>
          <span className="text-white/40">{latest.week}</span>
        </div>
      )}
      <SparklineDots values={totals} />
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export function DownloadHistoryPanel() {
  const [page, setPage] = useState(1);
  const isDesktop = useIsDesktop();

  // aria-live Announcement ref (OPE-190)
  const liveRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, error } = useSWR<DownloadHistoryResponse>(
    `/api/proxy/api/download-history?page=${page}&page_size=5`,
    fetcher,
    { refreshInterval: 60_000 },
  );

  const totalPages = data?.total_pages ?? 1;

  // Keyboard Navigation (OPE-188)
  const handleKey = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' && page < totalPages) {
        setPage((p) => p + 1);
      }
      if (e.key === 'ArrowLeft' && page > 1) {
        setPage((p) => p - 1);
      }
    },
    [page, totalPages],
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [handleKey]);

  // aria-live Ansage bei Seiten-Wechsel (OPE-190)
  useEffect(() => {
    if (liveRef.current && data) {
      liveRef.current.textContent = `Seite ${data.page} von ${data.total_pages} — ${data.tags.length} Tag(s) angezeigt`;
    }
  }, [data]);

  const showKeyboardHint = isDesktop && totalPages > 1;

  return (
    <section className="space-y-4" aria-label="APK Download-History">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h3 className="text-sm font-semibold text-white/80 uppercase tracking-wider">
          📊 APK Download-History
        </h3>
        {/* Keyboard-Hint: OPE-188 — nur Desktop + totalPages > 1 */}
        <KeyboardHint show={showKeyboardHint} />
      </div>

      {/* aria-live Region (OPE-190) — screen reader Ansage bei Tab-Fokus */}
      <div
        ref={liveRef}
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      />

      {/* Content */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-2xl bg-white/5" />
          ))}
        </div>
      )}

      {error && (
        <p className="text-xs text-amber-400/80">
          ⚠️ Download-History nicht verfügbar — API nicht erreichbar.
        </p>
      )}

      {data && data.total_tags === 0 && (
        <p className="text-xs text-white/40">
          Noch keine Download-Daten vorhanden. Skript{' '}
          <code className="font-mono">scripts/apk-download-history.py</code> ausführen.
        </p>
      )}

      {data && data.tags.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {data.tags.map((entry) => (
            <TagCard key={entry.tag} entry={entry} />
          ))}
        </div>
      )}

      {/* Pagination Footer */}
      {data && totalPages > 1 && (
        <div className="flex items-center justify-between gap-3 pt-1">
          {/* Prev */}
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            aria-label="Vorherige Seite"
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/60 transition hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            ← Zurück
          </button>

          {/* Dots (OPE-189) */}
          <PageDots total={totalPages} current={page} onSelect={setPage} />

          {/* Next */}
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            aria-label="Nächste Seite"
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/60 transition hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Weiter →
          </button>
        </div>
      )}
    </section>
  );
}
