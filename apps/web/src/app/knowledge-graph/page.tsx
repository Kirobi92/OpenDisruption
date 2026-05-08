'use client';

import Link from 'next/link';

type IntegralStage = 'infrared' | 'magenta' | 'red' | 'amber' | 'orange' | 'green' | 'teal' | 'turquoise';
type KnowledgeZone = 'PUBLIC' | 'WORKSPACE';

interface GraphNode {
  id: string;
  label: string;
  stage: IntegralStage;
  zone: KnowledgeZone;
  x: number;
  y: number;
  z: number;
  radius: number;
  summary: string;
}

interface GraphEdge {
  source: string;
  target: string;
  strength: number;
}

const STAGE_COLORS: Record<IntegralStage, { glow: string; fill: string; text: string; label: string }> = {
  infrared: { glow: '#ef4444', fill: '#7f1d1d', text: 'text-red-200', label: 'Infrared · Energie' },
  magenta: { glow: '#d946ef', fill: '#701a75', text: 'text-fuchsia-200', label: 'Magenta · Mythos' },
  red: { glow: '#f97316', fill: '#7c2d12', text: 'text-orange-200', label: 'Rot · Kraft' },
  amber: { glow: '#f59e0b', fill: '#78350f', text: 'text-amber-200', label: 'Amber · Ordnung' },
  orange: { glow: '#fb923c', fill: '#9a3412', text: 'text-orange-100', label: 'Orange · Leistung' },
  green: { glow: '#22c55e', fill: '#14532d', text: 'text-emerald-200', label: 'Grün · Verbindung' },
  teal: { glow: '#14b8a6', fill: '#134e4a', text: 'text-teal-200', label: 'Teal · Integration' },
  turquoise: { glow: '#38bdf8', fill: '#0c4a6e', text: 'text-sky-200', label: 'Türkis · Ganzheit' },
};

const DEMO_NODES: GraphNode[] = [
  {
    id: 'core',
    label: 'KIDI Core',
    stage: 'turquoise',
    zone: 'WORKSPACE',
    x: 50,
    y: 50,
    z: 96,
    radius: 34,
    summary: 'Synthetischer Mittelpunkt für lokale Wissensnavigation.',
  },
  {
    id: 'agents',
    label: 'Agenten',
    stage: 'teal',
    zone: 'WORKSPACE',
    x: 28,
    y: 30,
    z: 76,
    radius: 23,
    summary: 'Demo-Knoten für orchestrierte Fähigkeiten.',
  },
  {
    id: 'vision',
    label: 'Vision',
    stage: 'green',
    zone: 'PUBLIC',
    x: 70,
    y: 28,
    z: 82,
    radius: 24,
    summary: 'Öffentliche, abstrakte Leitbild-Ebene ohne private Inhalte.',
  },
  {
    id: 'systems',
    label: 'Systeme',
    stage: 'orange',
    zone: 'WORKSPACE',
    x: 20,
    y: 68,
    z: 58,
    radius: 19,
    summary: 'Technische Services, APIs und lokale Infrastruktur.',
  },
  {
    id: 'rituals',
    label: 'Routinen',
    stage: 'amber',
    zone: 'WORKSPACE',
    x: 49,
    y: 76,
    z: 64,
    radius: 18,
    summary: 'Nur Demo-Struktur für wiederkehrende Abläufe.',
  },
  {
    id: 'creative',
    label: 'Kreativität',
    stage: 'magenta',
    zone: 'PUBLIC',
    x: 79,
    y: 66,
    z: 70,
    radius: 21,
    summary: 'Synthetische Projektenergie für Musik, Bild und Story.',
  },
  {
    id: 'security',
    label: 'Zonen-Gate',
    stage: 'red',
    zone: 'WORKSPACE',
    x: 39,
    y: 18,
    z: 62,
    radius: 17,
    summary: 'Schutzschicht: MVP zeigt ausschließlich PUBLIC/WORKSPACE-Demo.',
  },
  {
    id: 'spark',
    label: 'Impuls',
    stage: 'infrared',
    zone: 'PUBLIC',
    x: 86,
    y: 44,
    z: 44,
    radius: 15,
    summary: 'Lebendiger Startpunkt für Ideen — ohne reale Datenquelle.',
  },
];

const DEMO_EDGES: GraphEdge[] = [
  { source: 'core', target: 'agents', strength: 0.92 },
  { source: 'core', target: 'vision', strength: 0.88 },
  { source: 'core', target: 'systems', strength: 0.8 },
  { source: 'core', target: 'rituals', strength: 0.72 },
  { source: 'core', target: 'creative', strength: 0.76 },
  { source: 'agents', target: 'security', strength: 0.7 },
  { source: 'vision', target: 'creative', strength: 0.66 },
  { source: 'systems', target: 'security', strength: 0.82 },
  { source: 'creative', target: 'spark', strength: 0.6 },
];

function findNode(id: string): GraphNode {
  const node = DEMO_NODES.find((candidate) => candidate.id === id);
  if (!node) throw new Error(`Demo graph is inconsistent: missing node ${id}`);
  return node;
}

function projectionStyle(node: GraphNode): React.CSSProperties {
  const scale = 0.74 + node.z / 260;
  const depthBlur = Math.max(0, (100 - node.z) / 34);
  return {
    left: `${node.x}%`,
    top: `${node.y}%`,
    width: `${node.radius * scale}px`,
    height: `${node.radius * scale}px`,
    filter: `drop-shadow(0 0 ${16 + node.z / 4}px ${STAGE_COLORS[node.stage].glow}) blur(${depthBlur * 0.18}px)`,
    transform: `translate(-50%, -50%) scale(${scale})`,
    zIndex: Math.round(node.z),
  };
}

export default function KnowledgeGraphPage() {
  return (
    <main className="min-h-screen overflow-hidden bg-slate-950 text-white">
      <section className="relative isolate min-h-screen px-4 py-8 sm:px-8 lg:px-12">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_25%,rgba(56,189,248,0.26),transparent_34%),radial-gradient(circle_at_20%_80%,rgba(34,197,94,0.16),transparent_26%),radial-gradient(circle_at_82%_70%,rgba(217,70,239,0.18),transparent_28%)]" />
        <div className="absolute inset-0 -z-10 opacity-30 [background-image:linear-gradient(rgba(148,163,184,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.12)_1px,transparent_1px)] [background-size:64px_64px]" />

        <div className="mx-auto flex max-w-[1800px] flex-col gap-6 2xl:gap-8">
          <header className="flex flex-col gap-4 rounded-3xl border border-white/10 bg-slate-900/60 p-5 shadow-2xl shadow-sky-950/40 backdrop-blur md:flex-row md:items-end md:justify-between">
            <div>
              <p className="mb-2 text-sm font-semibold uppercase tracking-[0.35em] text-sky-300">KIDI Knowledge Graph · Demo MVP</p>
              <h1 className="max-w-4xl text-4xl font-black tracking-tight text-white sm:text-5xl 2xl:text-7xl">
                Integraler Wissensraum in synthetischem Licht
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300 sm:text-base 2xl:text-xl">
                Eine sichere, lokale Vorschau: keine echten privaten Graphdaten, keine externen Services, nur kuratierte PUBLIC/WORKSPACE-Demo-Knoten.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 text-xs text-slate-300">
              <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1">synthetisch</span>
              <span className="rounded-full border border-sky-400/30 bg-sky-400/10 px-3 py-1">SVG/CSS only</span>
              <span className="rounded-full border border-violet-400/30 bg-violet-400/10 px-3 py-1">4K ready</span>
            </div>
          </header>

          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px] 2xl:grid-cols-[minmax(0,1fr)_440px]">
            <section className="relative min-h-[62vh] overflow-hidden rounded-[2rem] border border-sky-300/15 bg-slate-950/70 shadow-2xl shadow-sky-950/50 backdrop-blur 2xl:min-h-[72vh]">
              <div className="absolute inset-0 animate-pulse bg-[conic-gradient(from_120deg_at_50%_50%,rgba(239,68,68,0.08),rgba(217,70,239,0.1),rgba(245,158,11,0.08),rgba(34,197,94,0.1),rgba(20,184,166,0.1),rgba(56,189,248,0.14),rgba(239,68,68,0.08))]" />
              <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                <defs>
                  <linearGradient id="edgeGlow" x1="0" x2="1" y1="0" y2="1">
                    <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.15" />
                    <stop offset="50%" stopColor="#22c55e" stopOpacity="0.42" />
                    <stop offset="100%" stopColor="#d946ef" stopOpacity="0.2" />
                  </linearGradient>
                </defs>
                {DEMO_EDGES.map((edge) => {
                  const source = findNode(edge.source);
                  const target = findNode(edge.target);
                  return (
                    <line
                      key={`${edge.source}-${edge.target}`}
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      stroke="url(#edgeGlow)"
                      strokeLinecap="round"
                      strokeWidth={0.18 + edge.strength * 0.28}
                    />
                  );
                })}
              </svg>

              <div className="absolute inset-0 [perspective:1200px]">
                <div className="absolute inset-8 rounded-full border border-sky-200/10 shadow-[inset_0_0_80px_rgba(56,189,248,0.12)] [transform:rotateX(62deg)_rotateZ(-12deg)]" />
                {DEMO_NODES.map((node) => {
                  const colors = STAGE_COLORS[node.stage];
                  return (
                    <article
                      key={node.id}
                      className="group absolute rounded-full border border-white/30 bg-slate-900/70 transition-transform duration-500 hover:scale-125 focus-within:scale-125"
                      style={projectionStyle(node)}
                    >
                      <button
                        type="button"
                        className="h-full w-full rounded-full outline-none ring-offset-2 ring-offset-slate-950 focus:ring-2 focus:ring-sky-200"
                        style={{ background: `radial-gradient(circle at 35% 25%, #ffffff, ${colors.glow} 24%, ${colors.fill} 72%)` }}
                        aria-label={`${node.label}: ${node.summary}`}
                      />
                      <div className="pointer-events-none absolute left-1/2 top-full mt-3 w-44 -translate-x-1/2 rounded-2xl border border-white/10 bg-slate-950/90 p-3 text-center opacity-0 shadow-2xl transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100">
                        <p className={`text-sm font-bold ${colors.text}`}>{node.label}</p>
                        <p className="mt-1 text-[11px] leading-4 text-slate-300">{node.summary}</p>
                        <p className="mt-2 text-[10px] uppercase tracking-widest text-slate-500">{node.zone}</p>
                      </div>
                    </article>
                  );
                })}
              </div>

              <div className="absolute bottom-4 left-4 right-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-xs text-slate-300 backdrop-blur">
                <span>Rendering: CSS-Perspektive + SVG-Kanten, dependency-frei</span>
                <span>Demo-Knoten: {DEMO_NODES.length} · Kanten: {DEMO_EDGES.length}</span>
              </div>
            </section>

            <aside className="space-y-4 rounded-[2rem] border border-white/10 bg-slate-900/70 p-5 shadow-2xl shadow-slate-950/50 backdrop-blur">
              <div>
                <h2 className="text-xl font-bold text-white 2xl:text-2xl">MVP-Architektur</h2>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  Route <code className="rounded bg-slate-800 px-1.5 py-0.5">/knowledge-graph</code> bleibt lokal und nutzt aktuell nur statisch typisierte Demo-Daten im Client.
                </p>
              </div>

              <div className="grid gap-2">
                {Object.entries(STAGE_COLORS).map(([stage, colors]) => (
                  <div key={stage} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2">
                    <span className="flex items-center gap-2 text-sm text-slate-200">
                      <span className="h-3 w-3 rounded-full" style={{ backgroundColor: colors.glow, boxShadow: `0 0 16px ${colors.glow}` }} />
                      {colors.label}
                    </span>
                  </div>
                ))}
              </div>

              <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4">
                <h3 className="font-semibold text-emerald-200">Sicherheitsmodell</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-emerald-50/80">
                  <li>Keine echten privaten Graphdaten.</li>
                  <li>Nur PUBLIC/WORKSPACE-Demo-Zonen.</li>
                  <li>Späterer Live-Zugriff ausschließlich über <code>/api/*</code> mit Zonengate.</li>
                </ul>
              </div>

              <Link href="/status" className="block rounded-2xl border border-sky-400/30 bg-sky-400/10 px-4 py-3 text-center font-semibold text-sky-100 transition-colors hover:bg-sky-400/20">
                Stack-Status prüfen
              </Link>
            </aside>
          </div>
        </div>
      </section>
    </main>
  );
}
