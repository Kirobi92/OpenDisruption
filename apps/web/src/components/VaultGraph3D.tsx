'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import dynamic from 'next/dynamic';

// 2D canvas-only graph — sidesteps the @react-three/fiber + Next.js 15
// reconciler incompatibility. Still beautiful: glowing nodes, animated
// directional particles, zone-coloured.
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
  source: string;
  target: string;
  [key: string]: unknown;
}
interface VaultGraph {
  nodes: VaultNode[];
  links: VaultLink[];
  meta: { generated_at: string; node_count: number; link_count: number };
}

const ZONE_COLORS: Record<string, string> = {
  PUBLIC: '#5eead4',
  WORKSPACE: '#a78bfa',
  FAMILY_PRIVATE: '#e879f9',
  QUARANTINE: '#fbbf24',
};
const GHOST_COLOR = '#475569';

function colorFor(node: VaultNode): string {
  if (node.group === 'ghost') return GHOST_COLOR;
  return ZONE_COLORS[node.zone] || '#5eead4';
}

export default function VaultGraph3D() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [graph, setGraph] = useState<VaultGraph | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [size, setSize] = useState({ w: 800, h: 600 });
  const [hover, setHover] = useState<VaultNode | null>(null);

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
    return {
      nodes: graph.nodes.map((n) => ({ ...n })),
      links: graph.links.map((l) => ({ ...l })),
    };
  }, [graph]);

  return (
    <div className="relative h-[78vh] w-full overflow-hidden rounded-3xl border border-white/10 bg-void-950/60 backdrop-blur-xl">
      <div ref={containerRef} className="absolute inset-0">
        {graph && (
          <ForceGraph2D
            graphData={data}
            width={size.w}
            height={size.h}
            backgroundColor="rgba(4,6,20,0)"
            nodeRelSize={4}
            nodeVal={((n: VaultNode) => Math.min(20, 1 + n.size * 1.4)) as never}
            nodeColor={((n: VaultNode) => colorFor(n)) as never}
            linkColor={(() => 'rgba(167,139,250,0.32)') as never}
            linkWidth={0.6}
            linkDirectionalParticles={2}
            linkDirectionalParticleSpeed={0.005}
            linkDirectionalParticleWidth={1.6}
            linkDirectionalParticleColor={(() => '#e879f9') as never}
            onNodeHover={((n: VaultNode | null) => setHover(n)) as never}
            enableNodeDrag
            warmupTicks={40}
            cooldownTicks={140}
            d3AlphaDecay={0.025}
            d3VelocityDecay={0.28}
            nodeCanvasObject={((node: VaultNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const r = (1 + Math.log2(1 + node.size) * 1.6) / Math.max(globalScale, 0.6);
              const color = colorFor(node);
              const x = node.x ?? 0;
              const y = node.y ?? 0;
              // halo
              const halo = ctx.createRadialGradient(x, y, 0, x, y, r * 4);
              halo.addColorStop(0, color);
              halo.addColorStop(0.4, color + '55');
              halo.addColorStop(1, 'transparent');
              ctx.fillStyle = halo;
              ctx.globalAlpha = 0.55;
              ctx.beginPath();
              ctx.arc(x, y, r * 4, 0, Math.PI * 2);
              ctx.fill();
              // core
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

      {/* Overlay UI */}
      <div className="pointer-events-none absolute left-4 top-4 max-w-sm rounded-2xl border border-aurora-cyan/30 bg-void-900/80 px-4 py-3 text-xs backdrop-blur-md">
        <div className="font-mono uppercase tracking-[0.3em] text-aurora-cyan">Vault · Live</div>
        {graph ? (
          <div className="mt-1 text-white/70">
            {graph.meta.node_count} nodes · {graph.meta.link_count} links
            <div className="mt-2 flex flex-wrap gap-2">
              {Object.entries(ZONE_COLORS).map(([zone, color]) => (
                <span
                  key={zone}
                  className="inline-flex items-center gap-1.5 rounded-full border border-white/10 px-2 py-0.5"
                >
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ background: color, boxShadow: `0 0 8px ${color}` }}
                  />
                  {zone}
                </span>
              ))}
            </div>
          </div>
        ) : error ? (
          <div className="mt-1 text-rose-300">{error}</div>
        ) : (
          <div className="mt-1 text-white/50">Loading graph…</div>
        )}
      </div>

      {hover && (
        <div className="pointer-events-none absolute right-4 top-4 max-w-sm rounded-2xl border border-aurora-magenta/30 bg-void-900/85 p-4 text-sm backdrop-blur-md">
          <div className="font-semibold text-white">{hover.label}</div>
          <div className="mt-1 font-mono text-[10px] uppercase tracking-[0.25em] text-white/50">
            {hover.zone} · {hover.group}
          </div>
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
          <div className="mt-2 text-[11px] text-white/40">{hover.id}</div>
        </div>
      )}
    </div>
  );
}
