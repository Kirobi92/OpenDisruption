'use client';

/**
 * ObsidianVaultGraph — lädt /graph.json (Obsidian-Vault, erzeugt von
 * infra/scripts/build-vault-graph.py) und rendert ihn als 2-D Force-Graph.
 *
 * Knoten = Markdown-Notes   · Kanten = [[wikilinks]]
 * Farbe = Zone (WORKSPACE / FAMILY_PRIVATE / PUBLIC / QUARANTINE / SACRED)
 * Größe ∝ eingehende Links
 */

import { useEffect, useRef, useState, useMemo } from 'react';
import dynamic from 'next/dynamic';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false }) as any;

interface VaultNode {
  id: string;
  label: string;
  group: string;
  zone: string;
  agent?: string;
  tags?: string[];
  size: number;
  x?: number;
  y?: number;
  [key: string]: unknown;
}
interface VaultLink {
  source: string | VaultNode;
  target: string | VaultNode;
  [key: string]: unknown;
}
interface VaultGraph {
  nodes: VaultNode[];
  links: VaultLink[];
  meta: {
    generated_at: string;
    node_count: number;
    link_count: number;
  };
}

const ZONE_COLORS: Record<string, string> = {
  PUBLIC: '#5eead4',
  WORKSPACE: '#a78bfa',
  FAMILY_PRIVATE: '#e879f9',
  QUARANTINE: '#fbbf24',
  SACRED: '#fb7185',
};

const ZONE_LABELS: Record<string, string> = {
  PUBLIC: 'Öffentlich',
  WORKSPACE: 'Workspace',
  FAMILY_PRIVATE: 'Familie',
  QUARANTINE: 'Quarantäne',
  SACRED: 'Sakral',
};

function nodeColor(n: VaultNode): string {
  return ZONE_COLORS[n.zone] ?? '#5eead4';
}

export default function ObsidianVaultGraph() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [graph, setGraph] = useState<VaultGraph | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [size, setSize] = useState({ w: 800, h: 560 });
  const [hover, setHover] = useState<VaultNode | null>(null);
  const [search, setSearch] = useState('');
  const [enabledZones, setEnabledZones] = useState<Record<string, boolean>>({
    PUBLIC: true,
    WORKSPACE: true,
    FAMILY_PRIVATE: true,
    QUARANTINE: true,
    SACRED: false, // SACRED by default hidden
  });

  // Fetch vault graph
  useEffect(() => {
    let cancelled = false;
    fetch('/graph.json')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data: VaultGraph) => {
        if (!cancelled) setGraph(data);
      })
      .catch((e) => !cancelled && setError(String(e)));
    return () => { cancelled = true; };
  }, []);

  // Resize observer
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => setSize({ w: el.clientWidth, h: el.clientHeight });
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const data = useMemo(() => {
    if (!graph) return { nodes: [], links: [] };
    const q = search.trim().toLowerCase();
    const visible = (n: VaultNode) =>
      enabledZones[n.zone] !== false &&
      (q === '' || n.label.toLowerCase().includes(q) || (n.tags ?? []).some(t => t.toLowerCase().includes(q)));
    const visNodes = graph.nodes.filter(visible);
    const ids = new Set(visNodes.map((n) => n.id));
    const visLinks = graph.links.filter(
      (l) =>
        ids.has(typeof l.source === 'string' ? l.source : l.source.id) &&
        ids.has(typeof l.target === 'string' ? l.target : l.target.id),
    );
    return { nodes: visNodes, links: visLinks };
  }, [graph, enabledZones, search]);

  if (error) {
    return (
      <div className="flex h-72 items-center justify-center rounded-2xl border border-red-500/30 bg-red-500/10">
        <p className="text-sm text-red-300">Graph konnte nicht geladen werden — {error}</p>
      </div>
    );
  }

  if (!graph) {
    return (
      <div className="flex h-72 items-center justify-center rounded-2xl border border-white/10 bg-void-950/60">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-pulse rounded-full bg-gradient-to-br from-aurora-cyan/40 via-aurora-violet/40 to-aurora-magenta/40 blur-md" />
          <p className="mt-4 font-mono text-xs uppercase tracking-[0.4em] text-white/50">
            Lade Vault-Graph…
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Note suchen…"
          className="h-9 flex-1 min-w-[180px] rounded-xl border border-white/10 bg-void-900/60 px-3 text-sm text-white placeholder-white/30 outline-none focus:border-aurora-cyan/50"
        />
        <div className="flex flex-wrap gap-2">
          {Object.entries(ZONE_LABELS).map(([zone, label]) => (
            <button
              key={zone}
              onClick={() => setEnabledZones((z) => ({ ...z, [zone]: !z[zone] }))}
              className="inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium transition"
              style={{
                borderColor: enabledZones[zone] ? ZONE_COLORS[zone] + '60' : '#374151',
                backgroundColor: enabledZones[zone] ? ZONE_COLORS[zone] + '20' : 'transparent',
                color: enabledZones[zone] ? ZONE_COLORS[zone] : '#6b7280',
              }}
            >
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: enabledZones[zone] ? ZONE_COLORS[zone] : '#374151' }}
              />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Meta */}
      <div className="flex gap-4 text-xs text-white/40">
        <span>{data.nodes.length} Notes</span>
        <span>{data.links.length} Verbindungen</span>
        <span>Stand: {new Date(graph.meta.generated_at).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })}</span>
      </div>

      {/* Graph canvas */}
      <div
        ref={containerRef}
        className="relative h-[560px] w-full overflow-hidden rounded-3xl border border-white/10 bg-gray-950"
      >
        {data.nodes.length > 0 && (
          <ForceGraph2D
            width={size.w}
            height={size.h}
            graphData={data}
            nodeId="id"
            nodeLabel={(n: VaultNode) =>
              `${n.label}${n.tags?.length ? '\n' + n.tags.join(', ') : ''}`
            }
            nodeColor={(n: VaultNode) => nodeColor(n)}
            nodeRelSize={4}
            nodeVal={(n: VaultNode) => Math.max(1, n.size)}
            linkColor={() => '#374151'}
            linkWidth={1}
            linkDirectionalParticles={1}
            linkDirectionalParticleWidth={1.5}
            linkDirectionalParticleColor={() => '#5eead4'}
            backgroundColor="#030712"
            onNodeHover={(n: VaultNode | null) => setHover(n)}
            nodeCanvasObject={(
              n: VaultNode,
              ctx: CanvasRenderingContext2D,
              globalScale: number,
            ) => {
              const r = Math.max(3, Math.sqrt(Math.max(1, n.size)) * 3);
              const x = n.x ?? 0;
              const y = n.y ?? 0;
              // glow
              ctx.beginPath();
              ctx.arc(x, y, r + 2, 0, 2 * Math.PI);
              ctx.fillStyle = nodeColor(n) + '30';
              ctx.fill();
              // core
              ctx.beginPath();
              ctx.arc(x, y, r, 0, 2 * Math.PI);
              ctx.fillStyle = nodeColor(n);
              ctx.fill();
              // label at sufficient zoom
              if (globalScale > 1.4 || (hover && hover.id === n.id)) {
                const label = n.label.length > 22 ? n.label.slice(0, 20) + '…' : n.label;
                const fs = Math.max(8, 10 / globalScale);
                ctx.font = `${fs}px monospace`;
                ctx.fillStyle = '#ffffffcc';
                ctx.textAlign = 'center';
                ctx.fillText(label, x, y + r + fs + 1);
              }
            }}
          />
        )}
        {data.nodes.length === 0 && (
          <div className="flex h-full items-center justify-center text-sm text-white/30">
            Keine Notes für die aktiven Filter.
          </div>
        )}

        {/* Hover tooltip */}
        {hover && (
          <div className="pointer-events-none absolute left-4 top-4 max-w-xs rounded-2xl border border-white/10 bg-gray-900/90 p-3 backdrop-blur-sm">
            <p className="text-sm font-semibold text-white">{hover.label}</p>
            <p className="mt-1 font-mono text-[10px] text-white/40">{hover.id}</p>
            {(hover.tags ?? []).length > 0 && (
              <p className="mt-1 text-xs text-white/50">{hover.tags!.join(', ')}</p>
            )}
            <div className="mt-2 flex items-center gap-1.5">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: nodeColor(hover) }}
              />
              <span className="text-xs text-white/50">{hover.zone}</span>
              <span className="text-xs text-white/30">· {hover.size} Links</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
