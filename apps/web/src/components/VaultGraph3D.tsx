'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import dynamic from 'next/dynamic';

// 2D canvas-only graph (still on Next side — true 3D lives in /v2/graph SvelteKit).
// Source: /repo-graph.json — entire OpenDisruption repo classified by zone,
// AQAL quadrant, Spiral Dynamics, agent ownership and edge type.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false }) as any;

interface RepoNode {
  id: string;
  label: string;
  dir: string;
  ext: string;
  zone: string;
  quadrant: string;
  spiral: string;
  agent?: string;
  tags?: string[];
  size: number;
  x?: number;
  y?: number;
  [key: string]: unknown;
}
interface RepoLink {
  source: string | RepoNode;
  target: string | RepoNode;
  type: string;
  [key: string]: unknown;
}
interface RepoGraph {
  nodes: RepoNode[];
  links: RepoLink[];
  meta: {
    generated_at: string;
    node_count: number;
    link_count: number;
    edge_types: string[];
    quadrants: Record<string, string>;
    spirals: string[];
  };
}

const ZONE_COLORS: Record<string, string> = {
  PUBLIC: '#5eead4',
  WORKSPACE: '#a78bfa',
  FAMILY_PRIVATE: '#e879f9',
  QUARANTINE: '#fbbf24',
  SACRED: '#fb7185',
};
const QUADRANT_COLORS: Record<string, string> = {
  UL: '#5eead4',
  UR: '#a78bfa',
  LL: '#e879f9',
  LR: '#fbbf24',
};
const SPIRAL_COLORS: Record<string, string> = {
  beige: '#d4cfa8',
  purple: '#9b5de5',
  red: '#ef4444',
  blue: '#60a5fa',
  orange: '#fb923c',
  green: '#22c55e',
  yellow: '#fde047',
  turquoise: '#2dd4bf',
};
const EDGE_COLORS: Record<string, string> = {
  wikilink: '#5eead4',
  import: '#a78bfa',
  'service-dep': '#e879f9',
  'agent-call': '#fbbf24',
  'zone-flow': '#fb7185',
};
const QUADRANT_LABELS: Record<string, string> = {
  UL: 'Bewusstsein',
  UR: 'Verhalten',
  LL: 'Kultur',
  LR: 'Systeme',
};

type ColorMode = 'zone' | 'quadrant' | 'spiral' | 'dir';

function hashHue(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h % 360;
}

function colorFor(node: RepoNode, mode: ColorMode): string {
  if (node.dir === 'ghost') return '#475569';
  if (mode === 'quadrant') return QUADRANT_COLORS[node.quadrant] || '#5eead4';
  if (mode === 'spiral') return SPIRAL_COLORS[node.spiral] || '#5eead4';
  if (mode === 'dir') return `hsl(${hashHue(node.dir)}, 70%, 65%)`;
  return ZONE_COLORS[node.zone] || '#5eead4';
}

export default function VaultGraph3D() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [graph, setGraph] = useState<RepoGraph | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [size, setSize] = useState({ w: 800, h: 600 });
  const [hover, setHover] = useState<RepoNode | null>(null);

  const [colorMode, setColorMode] = useState<ColorMode>('zone');
  const [enabledEdgeTypes, setEnabledEdgeTypes] = useState<Record<string, boolean>>({
    wikilink: true,
    import: true,
    'service-dep': true,
    'agent-call': true,
    'zone-flow': true,
  });
  const [enabledQuadrants, setEnabledQuadrants] = useState<Record<string, boolean>>({
    UL: true,
    UR: true,
    LL: true,
    LR: true,
  });
  const [enabledZones, setEnabledZones] = useState<Record<string, boolean>>({
    PUBLIC: true,
    WORKSPACE: true,
    FAMILY_PRIVATE: true,
    QUARANTINE: true,
    SACRED: true,
  });
  const [search, setSearch] = useState('');

  useEffect(() => {
    let cancelled = false;
    fetch('/repo-graph.json')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data: RepoGraph) => {
        if (!cancelled) setGraph(data);
      })
      .catch((e) => !cancelled && setError(String(e)));
    return () => {
      cancelled = true;
    };
  }, []);

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
    const nodeVisible = (n: RepoNode) =>
      enabledQuadrants[n.quadrant] !== false &&
      enabledZones[n.zone] !== false &&
      (q === '' || n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q));
    const visibleNodes = graph.nodes.filter(nodeVisible);
    const visibleIds = new Set(visibleNodes.map((n) => n.id));
    const visibleLinks = graph.links.filter(
      (l) =>
        enabledEdgeTypes[l.type] !== false &&
        visibleIds.has(typeof l.source === 'string' ? l.source : l.source.id) &&
        visibleIds.has(typeof l.target === 'string' ? l.target : l.target.id),
    );
    return {
      nodes: visibleNodes.map((n) => ({ ...n })),
      links: visibleLinks.map((l) => ({ ...l })),
    };
  }, [graph, enabledEdgeTypes, enabledQuadrants, enabledZones, search]);

  const counts = useMemo(() => {
    if (!graph) return { totalN: 0, totalL: 0, visN: 0, visL: 0 };
    return {
      totalN: graph.nodes.length,
      totalL: graph.links.length,
      visN: data.nodes.length,
      visL: data.links.length,
    };
  }, [graph, data]);

  return (
    <div className="relative h-[78vh] w-full overflow-hidden rounded-3xl border border-white/10 bg-void-950/60 backdrop-blur-xl">
      <div ref={containerRef} className="absolute inset-0">
        {graph && (
          <ForceGraph2D
            graphData={data}
            width={size.w}
            height={size.h}
            backgroundColor="rgba(4,6,20,0)"
            nodeRelSize={3.5}
            nodeVal={((n: RepoNode) => Math.min(20, 1 + n.size * 1.4)) as never}
            linkColor={((l: RepoLink) => (EDGE_COLORS[l.type] || '#a78bfa') + '55') as never}
            linkWidth={((l: RepoLink) => (l.type === 'zone-flow' ? 1.4 : 0.55)) as never}
            linkDirectionalParticles={2}
            linkDirectionalParticleSpeed={0.005}
            linkDirectionalParticleWidth={1.6}
            linkDirectionalParticleColor={((l: RepoLink) => EDGE_COLORS[l.type] || '#e879f9') as never}
            onNodeHover={((n: RepoNode | null) => setHover(n)) as never}
            enableNodeDrag
            warmupTicks={60}
            cooldownTicks={200}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
            nodeCanvasObject={((node: RepoNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const r = (1 + Math.log2(1 + node.size) * 1.6) / Math.max(globalScale, 0.6);
              const color = colorFor(node, colorMode);
              const x = node.x ?? 0;
              const y = node.y ?? 0;
              const halo = ctx.createRadialGradient(x, y, 0, x, y, r * 4);
              halo.addColorStop(0, color);
              halo.addColorStop(0.4, color + '55');
              halo.addColorStop(1, 'transparent');
              ctx.fillStyle = halo;
              ctx.globalAlpha = 0.55;
              ctx.beginPath();
              ctx.arc(x, y, r * 4, 0, Math.PI * 2);
              ctx.fill();
              ctx.globalAlpha = 1;
              ctx.fillStyle = color;
              ctx.beginPath();
              ctx.arc(x, y, r, 0, Math.PI * 2);
              ctx.fill();
              if (globalScale > 1.5) {
                ctx.globalAlpha = 0.85;
                ctx.fillStyle = '#e7eefc';
                ctx.font = `${10 / globalScale}px Inter, sans-serif`;
                ctx.textAlign = 'center';
                ctx.fillText(node.label, x, y + r + 8 / globalScale);
              }
              ctx.globalAlpha = 1;
            }) as never}
            nodeCanvasObjectMode={() => 'replace'}
          />
        )}
      </div>

      {/* Header / Stats */}
      <div className="pointer-events-none absolute left-4 top-4 max-w-md rounded-2xl border border-aurora-cyan/30 bg-void-900/85 px-4 py-3 text-xs backdrop-blur-md">
        <div className="font-mono uppercase tracking-[0.3em] text-aurora-cyan">
          OpenDisruption · Live Repo Graph
        </div>
        {graph ? (
          <div className="mt-1 text-white/70">
            {counts.visN} / {counts.totalN} files · {counts.visL} / {counts.totalL} edges
          </div>
        ) : error ? (
          <div className="mt-1 text-rose-300">{error}</div>
        ) : (
          <div className="mt-1 text-white/50">Loading repo graph…</div>
        )}
      </div>

      {/* Filter sidebar */}
      <div className="pointer-events-auto absolute right-4 top-4 max-h-[calc(78vh-2rem)] w-72 overflow-y-auto rounded-2xl border border-white/10 bg-void-900/85 p-4 text-xs text-white/80 backdrop-blur-md">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Suche Datei / Pfad…"
          className="mb-3 w-full rounded-lg border border-white/10 bg-void-950/60 px-3 py-2 text-xs text-white placeholder:text-white/40 focus:border-aurora-cyan focus:outline-none"
        />

        <Section title="Färbung">
          <div className="grid grid-cols-2 gap-1">
            {(['zone', 'quadrant', 'spiral', 'dir'] as ColorMode[]).map((m) => (
              <button
                key={m}
                onClick={() => setColorMode(m)}
                className={`rounded-lg border px-2 py-1.5 text-[10px] uppercase tracking-wider transition ${
                  colorMode === m
                    ? 'border-aurora-cyan bg-aurora-cyan/15 text-aurora-cyan'
                    : 'border-white/10 hover:border-white/30'
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </Section>

        <Section title="Zonen">
          {Object.entries(ZONE_COLORS).map(([z, c]) => (
            <Toggle
              key={z}
              label={z}
              color={c}
              checked={enabledZones[z]}
              onChange={(v) => setEnabledZones((s) => ({ ...s, [z]: v }))}
            />
          ))}
        </Section>

        <Section title="AQAL Quadranten">
          {Object.entries(QUADRANT_COLORS).map(([q, c]) => (
            <Toggle
              key={q}
              label={`${q} · ${QUADRANT_LABELS[q]}`}
              color={c}
              checked={enabledQuadrants[q]}
              onChange={(v) => setEnabledQuadrants((s) => ({ ...s, [q]: v }))}
            />
          ))}
        </Section>

        <Section title="Edge-Typen (Strahlen)">
          {Object.entries(EDGE_COLORS).map(([t, c]) => (
            <Toggle
              key={t}
              label={t}
              color={c}
              checked={enabledEdgeTypes[t]}
              onChange={(v) => setEnabledEdgeTypes((s) => ({ ...s, [t]: v }))}
            />
          ))}
        </Section>

        {colorMode === 'spiral' && (
          <Section title="Spiral Dynamics Legend">
            <div className="grid grid-cols-2 gap-1">
              {Object.entries(SPIRAL_COLORS).map(([s, c]) => (
                <span
                  key={s}
                  className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-2 py-1 text-[10px]"
                >
                  <span className="h-2 w-2 rounded-full" style={{ background: c, boxShadow: `0 0 6px ${c}` }} />
                  {s}
                </span>
              ))}
            </div>
          </Section>
        )}
      </div>

      {/* Hover detail */}
      {hover && (
        <div className="pointer-events-none absolute bottom-4 left-4 max-w-lg rounded-2xl border border-aurora-magenta/30 bg-void-900/90 p-4 text-sm backdrop-blur-md">
          <div className="font-semibold text-white">{hover.label}</div>
          <div className="mt-1 font-mono text-[10px] uppercase tracking-[0.25em] text-white/50">
            {hover.zone} · {hover.quadrant} · {hover.spiral} · {hover.dir}
          </div>
          <div className="mt-1 font-mono text-[10px] text-white/40">{hover.id}</div>
          {hover.agent && (
            <div className="mt-1 text-[11px] text-aurora-cyan">agent: {hover.agent}</div>
          )}
          {hover.tags && hover.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {hover.tags.map((t) => (
                <span
                  key={t}
                  className="rounded-full border border-aurora-cyan/30 px-2 py-0.5 text-[10px] text-aurora-cyan"
                >
                  #{t}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <div className="mb-2 font-mono text-[10px] uppercase tracking-[0.25em] text-aurora-cyan/80">{title}</div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function Toggle({
  label,
  color,
  checked,
  onChange,
}: {
  label: string;
  color: string;
  checked: boolean | undefined;
  onChange: (v: boolean) => void;
}) {
  const on = checked !== false;
  return (
    <button
      onClick={() => onChange(!on)}
      className={`flex w-full items-center gap-2 rounded-lg border px-2 py-1.5 text-left text-[11px] transition ${
        on ? 'border-white/20 bg-white/5' : 'border-white/5 bg-void-950/60 opacity-50'
      }`}
    >
      <span
        className="h-2.5 w-2.5 rounded-full"
        style={{ background: color, boxShadow: on ? `0 0 8px ${color}` : 'none' }}
      />
      <span className="flex-1 truncate">{label}</span>
      <span className="font-mono text-[9px] text-white/40">{on ? 'ON' : 'OFF'}</span>
    </button>
  );
}
