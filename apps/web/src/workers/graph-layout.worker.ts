// graph-layout.worker.ts — Web Worker für 3D-Force-Directed-Layout
// Coulomb-Abstoßung + Hooke-Federn + Gravitationszentrum, rein in 3D
// Läuft auf eigenem Thread, postet Float32Array-Positions ~30 Hz

export {};  // ESM-Modul-Markierung damit TypeScript das als Modul behandelt

interface NodeInput {
  id: string;
  size: number;
}

interface LinkInput {
  source: string;
  target: string;
}

interface NodeState {
  x: number; y: number; z: number;
  vx: number; vy: number; vz: number;
}

// Simulationsparameter
const REPULSION   = 1400;   // Coulomb-Konstante
const SPRING_K    = 0.030;  // Federkonstante
const SPRING_LEN  = 14;     // Ruhelänge der Kanten
const GRAVITY     = 0.038;  // Anziehung zum Ursprung
const DAMPING     = 0.80;   // Geschwindigkeitsdämpfung
const INTERVAL_MS = 33;     // ~30 Hz
const WARMUP_TICKS = 160;   // Initiale Ticks ohne Ausgabe

let nodes: NodeState[] = [];
let links: Array<[number, number]> = [];
let nodeCount = 0;
let running = false;
let temperature = 1.0;
let tickInterval: ReturnType<typeof setInterval> | null = null;

// Fibonacci-Kugel für gleichmäßige Startverteilung
function initPositions(): void {
  const goldenAngle = Math.PI * (1 + Math.sqrt(5));
  for (let i = 0; i < nodeCount; i++) {
    const phi = Math.acos(1 - 2 * (i + 0.5) / nodeCount);
    const theta = goldenAngle * i;
    const r = 30 + Math.random() * 50;
    nodes[i] = {
      x: r * Math.sin(phi) * Math.cos(theta),
      y: r * Math.sin(phi) * Math.sin(theta),
      z: r * Math.cos(phi),
      vx: 0, vy: 0, vz: 0,
    };
  }
}

function step(): void {
  const alpha = Math.min(temperature, 1.0);

  // Coulomb-Abstoßung O(N²) — bei 1042 Knoten ~500K Operationen, ~10ms/Tick in V8
  for (let i = 0; i < nodeCount; i++) {
    const a = nodes[i];
    for (let j = i + 1; j < nodeCount; j++) {
      const b = nodes[j];
      let dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
      let d2 = dx * dx + dy * dy + dz * dz;
      // Kleine Distanzen: zufällige Jitter-Abstandssicherung
      if (d2 < 0.04) {
        dx = (Math.random() - 0.5);
        dy = (Math.random() - 0.5);
        dz = (Math.random() - 0.5);
        d2 = 0.75;
      }
      const d = Math.sqrt(d2);
      const f = (REPULSION * alpha) / d2;
      const fx = f * dx / d, fy = f * dy / d, fz = f * dz / d;
      a.vx -= fx; a.vy -= fy; a.vz -= fz;
      b.vx += fx; b.vy += fy; b.vz += fz;
    }
  }

  // Hooke-Federn (Kanten)
  for (const [si, ti] of links) {
    const a = nodes[si], b = nodes[ti];
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
    const d = Math.max(Math.sqrt(dx * dx + dy * dy + dz * dz), 0.1);
    const stretch = d - SPRING_LEN;
    const f = SPRING_K * stretch * alpha;
    const fx = f * dx / d, fy = f * dy / d, fz = f * dz / d;
    a.vx += fx; a.vy += fy; a.vz += fz;
    b.vx -= fx; b.vy -= fy; b.vz -= fz;
  }

  // Integration + Gravitation zum Zentrum
  for (let i = 0; i < nodeCount; i++) {
    const n = nodes[i];
    n.vx = (n.vx - n.x * GRAVITY * alpha) * DAMPING;
    n.vy = (n.vy - n.y * GRAVITY * alpha) * DAMPING;
    n.vz = (n.vz - n.z * GRAVITY * alpha) * DAMPING;
    n.x += n.vx;
    n.y += n.vy;
    n.z += n.vz;
  }

  temperature = Math.max(temperature * 0.9986, 0.01);
}

// Positions als transferierbaren ArrayBuffer senden
function postPositions(): void {
  const buf = new Float32Array(nodeCount * 3);
  for (let i = 0; i < nodeCount; i++) {
    buf[i * 3]     = nodes[i].x;
    buf[i * 3 + 1] = nodes[i].y;
    buf[i * 3 + 2] = nodes[i].z;
  }
  const ab = buf.buffer.slice(0);
  // postMessage als globale Funktion im Worker-Kontext
  (self as unknown as { postMessage(data: unknown, transfer: Transferable[]): void }).postMessage(
    { type: 'positions', positions: ab },
    [ab],
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
(self as any).onmessage = (e: MessageEvent) => {
  const msg = e.data as { type: string; nodes?: NodeInput[]; links?: LinkInput[] };

  if (msg.type === 'init') {
    const rawNodes = msg.nodes ?? [];
    const rawLinks = msg.links ?? [];

    nodeCount = rawNodes.length;
    nodes = new Array(nodeCount);

    // ID → Index-Mapping
    const idxMap = new Map<string, number>();
    rawNodes.forEach((n, i) => idxMap.set(n.id, i));

    // Kanten als Index-Paare
    links = rawLinks
      .map(l => [idxMap.get(l.source) ?? -1, idxMap.get(l.target) ?? -1] as [number, number])
      .filter(([s, t]) => s >= 0 && t >= 0);

    initPositions();
    temperature = 1.0;
    running = true;

    // Warmup-Phase: Simulation vor erstem Post stabilisieren
    for (let i = 0; i < WARMUP_TICKS; i++) step();
    postPositions();

    if (tickInterval) clearInterval(tickInterval);
    tickInterval = setInterval(() => {
      if (!running) return;
      step();
      postPositions();
    }, INTERVAL_MS);

  } else if (msg.type === 'pause') {
    running = false;

  } else if (msg.type === 'resume') {
    running = true;

  } else if (msg.type === 'reseed') {
    initPositions();
    temperature = 0.5;
    running = true;
  }
};
