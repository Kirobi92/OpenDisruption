'use client';

// VaultGraph3DHighEnd — Vanilla Three.js 3D-Wissensgraph (kein @react-three/fiber)
// RTX 3090 Ziel: 60fps · 1042 Knoten · 220 Kanten · 5200 Partikel · UnrealBloom
// Gemountet via useEffect, sauber disposed beim Unmount

import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { SMAAPass } from 'three/examples/jsm/postprocessing/SMAAPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';

// ─── Typen ────────────────────────────────────────────────────────────────────

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
}

interface RepoLink {
  source: string | RepoNode;
  target: string | RepoNode;
  type: string;
}

interface RepoGraph {
  nodes: RepoNode[];
  links: RepoLink[];
  meta: {
    generated_at: string;
    node_count: number;
    link_count: number;
    edge_types: string[];
  };
}

type ColorMode = 'zone' | 'quadrant' | 'spiral' | 'dir';

// ─── Farbtabellen (Zone, Quadrant, Spiral, Kantentypus) ───────────────────────

const ZONE_COLORS: Record<string, string> = {
  PUBLIC:         '#5eead4',
  WORKSPACE:      '#a78bfa',
  FAMILY_PRIVATE: '#e879f9',
  QUARANTINE:     '#fbbf24',
  SACRED:         '#fb7185',
};

const QUADRANT_COLORS: Record<string, string> = {
  UL: '#5eead4',
  UR: '#a78bfa',
  LL: '#e879f9',
  LR: '#fbbf24',
};

const SPIRAL_COLORS: Record<string, string> = {
  beige:     '#d4cfa8',
  purple:    '#9b5de5',
  red:       '#ef4444',
  blue:      '#60a5fa',
  orange:    '#fb923c',
  green:     '#22c55e',
  yellow:    '#fde047',
  turquoise: '#2dd4bf',
};

const EDGE_COLORS: Record<string, string> = {
  wikilink:    '#5eead4',
  import:      '#a78bfa',
  'service-dep': '#e879f9',
  'agent-call': '#fbbf24',
  'zone-flow':  '#fb7185',
};

// Konsistente Farbe aus Verzeichnis-String via HSL-Hashing
function dirToColor(dir: string): string {
  let h = 0;
  for (let i = 0; i < dir.length; i++) h = (Math.imul(31, h) + dir.charCodeAt(i)) | 0;
  return `hsl(${Math.abs(h) % 360}, 70%, 62%)`;
}

function getNodeColor(node: RepoNode, mode: ColorMode): string {
  switch (mode) {
    case 'zone':     return ZONE_COLORS[node.zone]       ?? '#888888';
    case 'quadrant': return QUADRANT_COLORS[node.quadrant] ?? '#888888';
    case 'spiral':   return SPIRAL_COLORS[node.spiral]   ?? '#888888';
    case 'dir':      return dirToColor(node.dir);
  }
}

// ─── GLSL Shaders (Inline-Strings, kein .glsl-Import) ────────────────────────

// Knoten-Vertex: instanceMatrix + instanceColor + Puls-Animation + Hover-Highlight
const NODE_VERT = /* glsl */`
  attribute mat4  instanceMatrix;
  attribute vec3  instanceColor;
  attribute float aPhase;
  attribute float aHighlight;

  uniform float uTime;

  varying vec3  vColor;
  varying vec3  vNormal;
  varying vec3  vViewPos;
  varying float vHighlight;

  void main() {
    vColor     = instanceColor;
    vHighlight = aHighlight;

    // Normale in View-Space (nur Translation+UniformScale → normalMatrix reicht)
    vNormal = normalize(normalMatrix * normal);

    // Sanfte Puls-Animation pro Instanz (reduzierte Bewegung via JS kontrolliert)
    float pulse = 1.0 + sin(uTime * 1.5 + aPhase) * 0.045;
    pulse += aHighlight * 0.25;

    vec4 worldPos = instanceMatrix * vec4(position * pulse, 1.0);
    vec4 viewPos  = viewMatrix * worldPos;
    vViewPos      = viewPos.xyz;
    gl_Position   = projectionMatrix * viewPos;
  }
`;

// Knoten-Fragment: Diffuse + Rim-Light + Hover-Glow
const NODE_FRAG = /* glsl */`
  precision highp float;

  varying vec3  vColor;
  varying vec3  vNormal;
  varying vec3  vViewPos;
  varying float vHighlight;

  void main() {
    vec3 norm    = normalize(vNormal);
    vec3 viewDir = normalize(-vViewPos);

    // Rim-Effekt (Fresnel)
    float rim = pow(1.0 - max(dot(viewDir, norm), 0.0), 2.2);

    // Einfaches Diffuse-Modell
    float diffuse = max(dot(norm, normalize(vec3(1.0, 2.0, 1.0))), 0.0) * 0.4 + 0.6;

    vec3 col = vColor * diffuse;
    col += rim * vColor * 2.5;
    col += vHighlight * vec3(1.0, 1.0, 1.0) * 0.6;

    gl_FragColor = vec4(col, 1.0);
  }
`;

// Halo-Vertex: größere Sphäre, stärkerer Puls
const HALO_VERT = /* glsl */`
  attribute mat4  instanceMatrix;
  attribute vec3  instanceColor;
  attribute float aPhase;
  attribute float aHighlight;

  uniform float uTime;

  varying vec3  vColor;
  varying vec3  vNormal;
  varying vec3  vViewPos;
  varying float vHighlight;

  void main() {
    vColor     = instanceColor;
    vHighlight = aHighlight;
    vNormal    = normalize(normalMatrix * normal);

    float pulse = 1.0 + sin(uTime * 1.2 + aPhase + 1.1) * 0.07;
    pulse += aHighlight * 0.6;

    vec4 worldPos = instanceMatrix * vec4(position * pulse, 1.0);
    vec4 viewPos  = viewMatrix * worldPos;
    vViewPos      = viewPos.xyz;
    gl_Position   = projectionMatrix * viewPos;
  }
`;

// Halo-Fragment: reines Fresnel-Glühen, additiv
const HALO_FRAG = /* glsl */`
  precision highp float;

  varying vec3  vColor;
  varying vec3  vNormal;
  varying vec3  vViewPos;
  varying float vHighlight;

  void main() {
    vec3 viewDir = normalize(-vViewPos);
    vec3 norm    = normalize(vNormal);

    // Fresnel: stark an Rändern, null in der Mitte
    float fresnel = pow(1.0 - max(dot(viewDir, norm), 0.0), 1.8);
    float alpha   = fresnel * (0.35 + vHighlight * 0.5);

    vec3 col = vColor + vHighlight * 0.4;
    gl_FragColor = vec4(col, alpha);
  }
`;

// Kanten-Vertex: Farbe + aLineT weitergeben
const EDGE_VERT = /* glsl */`
  attribute vec3  color;
  attribute float aLineT;

  varying vec3  vColor;
  varying float vLineT;

  void main() {
    vColor  = color;
    vLineT  = aLineT;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

// Kanten-Fragment: animierter Dash-Flow entlang der Kante
const EDGE_FRAG = /* glsl */`
  precision highp float;

  uniform float uTime;
  uniform float uOpacity;

  varying vec3  vColor;
  varying float vLineT;

  void main() {
    // Bewegende Energie-Welle entlang der Kante
    float t    = fract(vLineT * 7.0 - uTime * 0.5);
    float dash = smoothstep(0.0, 0.12, t) * (1.0 - smoothstep(0.45, 0.58, t));

    // Basis-Sichtbarkeit im "Off"-Segment
    float intensity = 0.06 + dash * 0.94;
    gl_FragColor = vec4(vColor * intensity, intensity * uOpacity);
  }
`;

// Mote-Vertex: schwebende Datenpunkte
const MOTE_VERT = /* glsl */`
  uniform float uTime;

  void main() {
    vec3 pos = position;
    // Subtile vertikale Schwingung
    pos.y += sin(uTime * 0.6 + position.x * 0.08 + position.z * 0.05) * 0.6;

    vec4 mvPos    = modelViewMatrix * vec4(pos, 1.0);
    gl_PointSize  = 3.0 * (80.0 / -mvPos.z);
    gl_Position   = projectionMatrix * mvPos;
  }
`;

// Mote-Fragment: weiches Kreissymbol
const MOTE_FRAG = /* glsl */`
  precision mediump float;

  void main() {
    float d     = length(gl_PointCoord - 0.5) * 2.0;
    float alpha = (1.0 - smoothstep(0.4, 1.0, d)) * 0.55;
    gl_FragColor = vec4(0.37, 0.92, 0.83, alpha);
  }
`;

// Vignetten-Shader (letzter Pass)
const VIG_VERT = /* glsl */`
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const VIG_FRAG = /* glsl */`
  precision mediump float;

  uniform sampler2D tDiffuse;
  uniform float     uOffset;
  uniform float     uDarkness;

  varying vec2 vUv;

  void main() {
    vec4  texel   = texture2D(tDiffuse, vUv);
    vec2  uv      = (vUv - 0.5) * 2.0 * uOffset;
    float vignette = 1.0 - dot(uv, uv) * uDarkness * 0.22;
    gl_FragColor  = vec4(texel.rgb * max(vignette, 0.0), texel.a);
  }
`;

// ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

function nodeId(v: string | RepoNode): string {
  return typeof v === 'string' ? v : v.id;
}

// ─── Komponente ───────────────────────────────────────────────────────────────

export interface VaultGraph3DHighEndProps {
  initialColorMode?: ColorMode;
  initialAutoRotate?: boolean;
}

export default function VaultGraph3DHighEnd({
  initialColorMode = 'zone',
  initialAutoRotate = true,
}: VaultGraph3DHighEndProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // UI-State
  const [hoveredNode,  setHoveredNode]  = useState<RepoNode | null>(null);
  const [selectedNode, setSelectedNode] = useState<RepoNode | null>(null);
  const [drawerOpen,   setDrawerOpen]   = useState(false);
  const [colorMode,    setColorMode]    = useState<ColorMode>(initialColorMode);
  const [autoRotate,   setAutoRotate]   = useState(initialAutoRotate);
  const [fps,          setFps]          = useState(60);
  const [stats, setStats] = useState({ nodes: 0, edges: 0, tris: 0 });

  // Refs für Three.js-Objekte — außerhalb von React-Render-Zyklen
  const nodeMeshRef  = useRef<THREE.InstancedMesh | null>(null);
  const haloMeshRef  = useRef<THREE.InstancedMesh | null>(null);
  const graphRef     = useRef<RepoGraph | null>(null);
  const colorModeRef = useRef<ColorMode>(initialColorMode);
  const autoRotateRef= useRef(initialAutoRotate);
  const colorDirty   = useRef(false);

  // Stale-Closure-sichere Sync für autoRotate-Controls
  useEffect(() => {
    autoRotateRef.current = autoRotate;
  }, [autoRotate]);

  // Farb-Modus-Änderung propagieren
  useEffect(() => {
    colorModeRef.current = colorMode;
    colorDirty.current   = true;
  }, [colorMode]);

  // ─── Haupt-Effekt: Three.js-Lifecycle ─────────────────────────────────────
  useEffect(() => {
    const maybeEl = containerRef.current;
    if (!maybeEl || typeof window === 'undefined') return;
    const el: HTMLDivElement = maybeEl; // explizit non-null für Closure-Narrowing

    let rafId   = 0;
    let worker: Worker | null = null;
    let cancelled = false;

    // Positions-Cache aus Worker (x,y,z je Knoten)
    let latestPositions: Float32Array | null = null;
    let positionsDirty = false;

    // Hover-Index-Tracking
    let prevHovered = -1;

    // FPS-Tracking
    let lastTime   = performance.now();
    let frameCount = 0;
    let fpsAccum   = 0;

    // Pointer-Vektor für Raycaster
    const pointer = new THREE.Vector2(-9999, -9999);

    // ── Renderer ────────────────────────────────────────────────────────────
    const renderer = new THREE.WebGLRenderer({
      antialias:             true,
      alpha:                 true,
      powerPreference:       'high-performance',
      logarithmicDepthBuffer: true,
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(el.clientWidth, el.clientHeight);
    renderer.toneMapping         = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    renderer.outputColorSpace    = THREE.SRGBColorSpace;
    el.appendChild(renderer.domElement);

    // ── Szene + Kamera ──────────────────────────────────────────────────────
    const scene  = new THREE.Scene();
    scene.fog    = new THREE.FogExp2(0x020414, 0.002);

    const camera = new THREE.PerspectiveCamera(60, el.clientWidth / el.clientHeight, 0.1, 2000);
    camera.position.set(0, 25, 90);

    // ── OrbitControls ───────────────────────────────────────────────────────
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping  = true;
    controls.dampingFactor  = 0.08;
    controls.autoRotate     = autoRotateRef.current;
    controls.autoRotateSpeed = 0.35;
    controls.minDistance    = 5;
    controls.maxDistance    = 600;

    // ── Sternfeld (5000 Punkte, statisch) ───────────────────────────────────
    const STAR_COUNT = 5000;
    const starPos = new Float32Array(STAR_COUNT * 3);
    for (let i = 0; i < STAR_COUNT; i++) {
      const phi   = Math.acos(2 * Math.random() - 1);
      const theta = 2 * Math.PI * Math.random();
      const r     = 120 + Math.random() * 120;
      starPos[i * 3]     = r * Math.sin(phi) * Math.cos(theta);
      starPos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      starPos[i * 3 + 2] = r * Math.cos(phi);
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({
      color:        0xffffff,
      size:         0.28,
      sizeAttenuation: true,
      transparent:  true,
      opacity:      0.55,
      blending:     THREE.AdditiveBlending,
      depthWrite:   false,
    });
    scene.add(new THREE.Points(starGeo, starMat));

    // ── Ambient Motes (200 schwebende Datenpunkte) ──────────────────────────
    const MOTE_COUNT  = 200;
    const motePos     = new Float32Array(MOTE_COUNT * 3);
    const moteVel     = new Float32Array(MOTE_COUNT * 3);
    for (let i = 0; i < MOTE_COUNT; i++) {
      const phi   = Math.acos(2 * Math.random() - 1);
      const theta = 2 * Math.PI * Math.random();
      const r     = 40 + Math.random() * 35;
      motePos[i * 3]     = r * Math.sin(phi) * Math.cos(theta);
      motePos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      motePos[i * 3 + 2] = r * Math.cos(phi);
      moteVel[i * 3]     = (Math.random() - 0.5) * 0.03;
      moteVel[i * 3 + 1] = (Math.random() - 0.5) * 0.015;
      moteVel[i * 3 + 2] = (Math.random() - 0.5) * 0.03;
    }
    const moteGeo = new THREE.BufferGeometry();
    moteGeo.setAttribute('position', new THREE.BufferAttribute(motePos, 3));
    (moteGeo.attributes.position as THREE.BufferAttribute).setUsage(THREE.DynamicDrawUsage);

    const moteMat = new THREE.ShaderMaterial({
      uniforms:    { uTime: { value: 0 } },
      vertexShader:   MOTE_VERT,
      fragmentShader: MOTE_FRAG,
      transparent: true,
      blending:    THREE.AdditiveBlending,
      depthWrite:  false,
    });
    const motePoints = new THREE.Points(moteGeo, moteMat);
    scene.add(motePoints);

    // ─── Graph-Daten laden + Meshes erstellen ─────────────────────────────
    async function buildGraph() {
      const res   = await fetch('/repo-graph.json');
      const graph = await res.json() as RepoGraph;
      if (cancelled) return;

      graphRef.current = graph;
      const nodes = graph.nodes;
      const links = graph.links;

      // Index-Map: node-id → Array-Index
      const idxMap = new Map<string, number>();
      nodes.forEach((n, i) => idxMap.set(n.id, i));

      setStats(s => ({ ...s, nodes: nodes.length, edges: links.length }));

      // ── Shared Geometrie für Knoten + Halos ─────────────────────────────
      const nodeGeo = new THREE.SphereGeometry(1, 32, 32);
      const haloGeo = new THREE.SphereGeometry(1, 24, 16);

      // Per-Instanz-Phasen und Highlight-Buffer
      const phases     = new Float32Array(nodes.length);
      const highlights = new Float32Array(nodes.length);
      for (let i = 0; i < nodes.length; i++) phases[i] = Math.random() * Math.PI * 2;

      function addInstanceAttrs(geo: THREE.BufferGeometry) {
        geo.setAttribute('aPhase',     new THREE.InstancedBufferAttribute(phases.slice(), 1));
        geo.setAttribute('aHighlight', new THREE.InstancedBufferAttribute(highlights.slice(), 1));
      }
      addInstanceAttrs(nodeGeo);
      addInstanceAttrs(haloGeo);

      // ── Knoten-ShaderMaterial ────────────────────────────────────────────
      const nodeMat = new THREE.ShaderMaterial({
        uniforms:       { uTime: { value: 0 } },
        vertexShader:   NODE_VERT,
        fragmentShader: NODE_FRAG,
      });

      const nodeMesh = new THREE.InstancedMesh(nodeGeo, nodeMat, nodes.length);
      nodeMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      nodeMesh.frustumCulled = false;

      // ── Halo-ShaderMaterial ──────────────────────────────────────────────
      const haloMat = new THREE.ShaderMaterial({
        uniforms:       { uTime: { value: 0 } },
        vertexShader:   HALO_VERT,
        fragmentShader: HALO_FRAG,
        transparent:    true,
        blending:       THREE.AdditiveBlending,
        depthWrite:     false,
      });

      const haloMesh = new THREE.InstancedMesh(haloGeo, haloMat, nodes.length);
      haloMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      haloMesh.frustumCulled = false;

      // Farben + Start-Matrizen setzen
      const col   = new THREE.Color();
      const dummy = new THREE.Object3D();

      function applyColors(mode: ColorMode) {
        nodes.forEach((n, i) => {
          col.set(getNodeColor(n, mode));
          nodeMesh.setColorAt(i, col);
          haloMesh.setColorAt(i, col);
        });
        if (nodeMesh.instanceColor) nodeMesh.instanceColor.needsUpdate = true;
        if (haloMesh.instanceColor) haloMesh.instanceColor.needsUpdate = true;
      }
      applyColors(colorModeRef.current);

      nodes.forEach((n, i) => {
        const s = Math.max(0.35, Math.log2(1 + (n.size || 1)) * 1.5);
        dummy.position.set(0, 0, 0);
        dummy.scale.setScalar(s);
        dummy.updateMatrix();
        nodeMesh.setMatrixAt(i, dummy.matrix);

        dummy.scale.setScalar(s * 4);
        dummy.updateMatrix();
        haloMesh.setMatrixAt(i, dummy.matrix);
      });
      nodeMesh.instanceMatrix.needsUpdate = true;
      haloMesh.instanceMatrix.needsUpdate = true;

      scene.add(nodeMesh);
      scene.add(haloMesh);

      nodeMeshRef.current = nodeMesh;
      haloMeshRef.current = haloMesh;

      // ── Kanten (LineSegments) ────────────────────────────────────────────
      const edgeCount    = links.length;
      const edgePosArr   = new Float32Array(edgeCount * 2 * 3);
      const edgeColArr   = new Float32Array(edgeCount * 2 * 3);
      const lineTArr     = new Float32Array(edgeCount * 2);

      links.forEach((link, i) => {
        const ec = new THREE.Color(EDGE_COLORS[link.type] ?? '#888888');
        edgeColArr[i * 6]     = ec.r; edgeColArr[i * 6 + 1] = ec.g; edgeColArr[i * 6 + 2] = ec.b;
        edgeColArr[i * 6 + 3] = ec.r; edgeColArr[i * 6 + 4] = ec.g; edgeColArr[i * 6 + 5] = ec.b;
        lineTArr[i * 2]     = 0;   // Startpunkt
        lineTArr[i * 2 + 1] = 1;   // Endpunkt
      });

      const edgeGeo = new THREE.BufferGeometry();
      edgeGeo.setAttribute('position', new THREE.BufferAttribute(edgePosArr, 3));
      edgeGeo.setAttribute('color',    new THREE.BufferAttribute(edgeColArr, 3));
      edgeGeo.setAttribute('aLineT',   new THREE.BufferAttribute(lineTArr, 1));
      (edgeGeo.attributes.position as THREE.BufferAttribute).setUsage(THREE.DynamicDrawUsage);

      const edgeMat = new THREE.ShaderMaterial({
        uniforms:       { uTime: { value: 0 }, uOpacity: { value: 0.65 } },
        vertexShader:   EDGE_VERT,
        fragmentShader: EDGE_FRAG,
        transparent:    true,
        blending:       THREE.AdditiveBlending,
        depthWrite:     false,
        vertexColors:   true,
      });

      const edgeLines = new THREE.LineSegments(edgeGeo, edgeMat);
      edgeLines.frustumCulled = false;
      scene.add(edgeLines);

      // ── Postprocessing ───────────────────────────────────────────────────
      const composer  = new EffectComposer(renderer);
      composer.addPass(new RenderPass(scene, camera));

      const bloom = new UnrealBloomPass(
        new THREE.Vector2(el.clientWidth, el.clientHeight),
        1.2,   // strength
        0.65,  // radius
        0.38,  // threshold
      );
      composer.addPass(bloom);

      const smaa = new SMAAPass();
      composer.addPass(smaa);

      composer.addPass(new OutputPass());

      const vignette = new ShaderPass({
        uniforms:       { tDiffuse: { value: null }, uOffset: { value: 0.92 }, uDarkness: { value: 1.4 } },
        vertexShader:   VIG_VERT,
        fragmentShader: VIG_FRAG,
      });
      composer.addPass(vignette);

      // ── Raycaster ────────────────────────────────────────────────────────
      const raycaster = new THREE.Raycaster();

      function onPointerMove(e: PointerEvent) {
        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x  = ((e.clientX - rect.left) / rect.width)  *  2 - 1;
        pointer.y  = -((e.clientY - rect.top)  / rect.height) *  2 + 1;
      }

      function onClick(e: MouseEvent) {
        raycaster.setFromCamera(pointer, camera);
        const hits = raycaster.intersectObject(nodeMesh);
        if (hits.length > 0 && hits[0].instanceId !== undefined) {
          e.stopPropagation();
          const idx = hits[0].instanceId;
          setSelectedNode(nodes[idx]);
          setDrawerOpen(true);
        }
      }

      function onKeyDown(e: KeyboardEvent) {
        if (e.key === 'Escape') setDrawerOpen(false);
      }

      renderer.domElement.addEventListener('pointermove', onPointerMove);
      renderer.domElement.addEventListener('click', onClick);
      document.addEventListener('keydown', onKeyDown);

      // ── Resize Observer ──────────────────────────────────────────────────
      const ro = new ResizeObserver(() => {
        const w = el.clientWidth, h = el.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
        composer.setSize(w, h);
      });
      ro.observe(el);

      // ── Web Worker: Force-Directed Layout ───────────────────────────────
      worker = new Worker(
        new URL('../workers/graph-layout.worker.ts', import.meta.url),
        { type: 'module' },
      );

      worker.postMessage({
        type:  'init',
        nodes: nodes.map(n => ({ id: n.id, size: n.size })),
        links: links.map(l => ({ source: nodeId(l.source), target: nodeId(l.target) })),
      });

      worker.onmessage = (e: MessageEvent<{ type: string; positions: ArrayBuffer }>) => {
        if (e.data.type === 'positions') {
          latestPositions = new Float32Array(e.data.positions);
          positionsDirty  = true;
        }
      };

      // ── Positionen auf InstancedMesh anwenden ───────────────────────────
      function applyPositions(pos: Float32Array) {
        nodes.forEach((n, i) => {
          const x  = pos[i * 3], y = pos[i * 3 + 1], z = pos[i * 3 + 2];
          const s  = Math.max(0.35, Math.log2(1 + (n.size || 1)) * 1.5);
          dummy.position.set(x, y, z);
          dummy.scale.setScalar(s);
          dummy.updateMatrix();
          nodeMesh.setMatrixAt(i, dummy.matrix);

          dummy.scale.setScalar(s * 4);
          dummy.updateMatrix();
          haloMesh.setMatrixAt(i, dummy.matrix);
        });
        nodeMesh.instanceMatrix.needsUpdate = true;
        haloMesh.instanceMatrix.needsUpdate = true;

        // Kanten-Positionen aktualisieren
        const edgePosAttr = edgeGeo.attributes.position as THREE.BufferAttribute;
        links.forEach((link, i) => {
          const si = idxMap.get(nodeId(link.source));
          const ti = idxMap.get(nodeId(link.target));
          if (si === undefined || ti === undefined) return;
          edgePosAttr.setXYZ(i * 2,     pos[si * 3], pos[si * 3 + 1], pos[si * 3 + 2]);
          edgePosAttr.setXYZ(i * 2 + 1, pos[ti * 3], pos[ti * 3 + 1], pos[ti * 3 + 2]);
        });
        edgePosAttr.needsUpdate = true;
      }

      // ── Animation Loop ───────────────────────────────────────────────────
      const clock = new THREE.Clock();

      function animate() {
        rafId = requestAnimationFrame(animate);

        const now   = performance.now();
        const rawDt = (now - lastTime) / 1000;
        lastTime    = now;
        frameCount++;

        // Rollierender FPS-Mittelwert (alle 30 Frames)
        fpsAccum += 1 / Math.max(rawDt, 0.001);
        if (frameCount % 30 === 0) {
          setFps(Math.round(fpsAccum / 30));
          fpsAccum = 0;
        }

        const time = clock.getElapsedTime();

        // Controls aktualisieren (autoRotate aus Ref lesen)
        controls.autoRotate = autoRotateRef.current;
        controls.update();

        // Uniforms zeitbasiert aktualisieren
        nodeMat.uniforms.uTime.value  = time;
        haloMat.uniforms.uTime.value  = time;
        edgeMat.uniforms.uTime.value  = time;
        moteMat.uniforms.uTime.value  = time;

        // Worker-Positionen anwenden (wenn neue vorhanden)
        if (positionsDirty && latestPositions) {
          applyPositions(latestPositions);
          positionsDirty = false;
        }

        // Farb-Modus-Änderung anwenden
        if (colorDirty.current) {
          applyColors(colorModeRef.current);
          colorDirty.current = false;
        }

        // Hover-Raycasting
        raycaster.setFromCamera(pointer, camera);
        const hits       = raycaster.intersectObject(nodeMesh);
        const hoverIdx   = hits.length > 0 && hits[0].instanceId !== undefined
          ? hits[0].instanceId : -1;

        if (hoverIdx !== prevHovered) {
          // Altes Highlight zurücksetzen
          if (prevHovered >= 0) {
            const hA = nodeGeo.getAttribute('aHighlight') as THREE.InstancedBufferAttribute;
            const hH = haloGeo.getAttribute('aHighlight') as THREE.InstancedBufferAttribute;
            hA.setX(prevHovered, 0); hH.setX(prevHovered, 0);
            hA.needsUpdate = true;   hH.needsUpdate = true;
          }
          // Neues Highlight setzen
          if (hoverIdx >= 0) {
            const hA = nodeGeo.getAttribute('aHighlight') as THREE.InstancedBufferAttribute;
            const hH = haloGeo.getAttribute('aHighlight') as THREE.InstancedBufferAttribute;
            hA.setX(hoverIdx, 1); hH.setX(hoverIdx, 1);
            hA.needsUpdate = true; hH.needsUpdate = true;
            setHoveredNode(nodes[hoverIdx]);
          } else {
            setHoveredNode(null);
          }
          prevHovered = hoverIdx;
        }

        // Mote-Positionen: langsame Rotation + Drift
        const angle = 0.0008;
        const cosA  = Math.cos(angle), sinA = Math.sin(angle);
        for (let i = 0; i < MOTE_COUNT; i++) {
          const x = motePos[i * 3], z = motePos[i * 3 + 2];
          motePos[i * 3]     = x * cosA - z * sinA;
          motePos[i * 3 + 2] = x * sinA + z * cosA;
          motePos[i * 3 + 1] += moteVel[i * 3 + 1];
          // Begrenzung
          const r = Math.sqrt(motePos[i*3]**2 + motePos[i*3+1]**2 + motePos[i*3+2]**2);
          if (r > 90) { motePos[i*3] *= 0.99; motePos[i*3+1] *= 0.99; motePos[i*3+2] *= 0.99; }
        }
        (moteGeo.attributes.position as THREE.BufferAttribute).needsUpdate = true;

        // GPU-Stats alle 120 Frames
        if (frameCount % 120 === 0) {
          setStats({ nodes: nodes.length, edges: links.length, tris: renderer.info.render.triangles });
        }

        composer.render();
      }

      animate();

      // ── Cleanup-Funktion ─────────────────────────────────────────────────
      return () => {
        cancelAnimationFrame(rafId);
        ro.disconnect();
        renderer.domElement.removeEventListener('pointermove', onPointerMove);
        renderer.domElement.removeEventListener('click', onClick);
        document.removeEventListener('keydown', onKeyDown);
        worker?.terminate();

        // Three.js-Objekte freigeben
        nodeGeo.dispose(); haloGeo.dispose(); edgeGeo.dispose();
        starGeo.dispose(); moteGeo.dispose();
        nodeMat.dispose(); haloMat.dispose(); edgeMat.dispose();
        starMat.dispose(); moteMat.dispose();
        composer.dispose();
        renderer.dispose();

        if (renderer.domElement.parentNode) {
          renderer.domElement.parentNode.removeChild(renderer.domElement);
        }
        nodeMeshRef.current = null;
        haloMeshRef.current = null;
        graphRef.current    = null;
      };
    }

    // Cleanup-Handle (async aus buildGraph)
    let innerCleanup: (() => void) | null = null;

    buildGraph()
      .then(cleanup => { if (!cancelled && cleanup) innerCleanup = cleanup; })
      .catch(console.error);

    return () => {
      cancelled = true;
      innerCleanup?.();
      if (!innerCleanup) {
        // Fallback: falls buildGraph noch läuft
        cancelAnimationFrame(rafId);
        worker?.terminate();
        renderer.dispose();
        if (renderer.domElement.parentNode) {
          renderer.domElement.parentNode.removeChild(renderer.domElement);
        }
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);  // Einmalig mounten — Updates via Refs

  // ─── JSX: Canvas-Container + HUD + Drawer ────────────────────────────────

  const colorModeLabels: Record<ColorMode, string> = {
    zone:     'Zone',
    quadrant: 'Quadrant',
    spiral:   'Spiral',
    dir:      'Verzeichnis',
  };

  return (
    <div className="relative w-full h-full min-h-[80vh] bg-void-950 rounded-2xl overflow-hidden">
      {/* Three.js Canvas-Mount-Punkt */}
      <div ref={containerRef} className="absolute inset-0" />

      {/* ── HUD: oben links ─────────────────────────────────────────────── */}
      <div className="absolute top-3 left-3 z-10 flex flex-col gap-1 pointer-events-none">
        <div className="flex items-center gap-2 rounded-lg bg-black/50 px-2.5 py-1 backdrop-blur-sm">
          <span className={`font-mono text-xs ${fps >= 55 ? 'text-green-400' : fps >= 30 ? 'text-yellow-400' : 'text-red-400'}`}>
            {fps} fps
          </span>
          <span className="text-white/30">·</span>
          <span className="font-mono text-[10px] text-white/50">{stats.nodes} nodes</span>
          <span className="text-white/30">·</span>
          <span className="font-mono text-[10px] text-white/50">{stats.edges} edges</span>
          {stats.tris > 0 && (
            <>
              <span className="text-white/30">·</span>
              <span className="font-mono text-[10px] text-white/40">{(stats.tris / 1000).toFixed(1)}k △</span>
            </>
          )}
        </div>
      </div>

      {/* ── Hover-Tooltip ────────────────────────────────────────────────── */}
      {hoveredNode && !drawerOpen && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10 pointer-events-none">
          <div className="rounded-lg bg-black/70 px-3 py-1.5 backdrop-blur-sm border border-white/10 text-center max-w-[280px]">
            <div className="text-xs font-medium text-white truncate">{hoveredNode.label}</div>
            <div className="mt-0.5 flex items-center justify-center gap-1.5">
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ backgroundColor: ZONE_COLORS[hoveredNode.zone] ?? '#888' }}
              />
              <span className="font-mono text-[10px] text-white/60">{hoveredNode.zone}</span>
              <span className="text-white/30">·</span>
              <span className="font-mono text-[10px] text-white/50">{hoveredNode.dir}</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Rechte Steuerleiste ──────────────────────────────────────────── */}
      <div className="absolute top-3 right-3 z-10 flex flex-col gap-2">
        {/* Farb-Modus */}
        <div className="rounded-xl bg-black/55 backdrop-blur-sm border border-white/10 p-2 flex flex-col gap-1">
          <div className="font-mono text-[9px] uppercase tracking-widest text-white/40 px-1 mb-0.5">Farbe</div>
          {(Object.keys(colorModeLabels) as ColorMode[]).map(m => (
            <button
              key={m}
              onClick={() => setColorMode(m)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all text-left ${
                colorMode === m
                  ? 'bg-aurora-violet/30 text-aurora-violet border border-aurora-violet/40'
                  : 'text-white/50 hover:text-white hover:bg-white/5'
              }`}
            >
              {colorModeLabels[m]}
            </button>
          ))}
        </div>

        {/* Auto-Rotation */}
        <button
          onClick={() => setAutoRotate(v => !v)}
          className={`rounded-xl px-3 py-2 text-xs font-medium backdrop-blur-sm border transition-all ${
            autoRotate
              ? 'bg-aurora-cyan/20 text-aurora-cyan border-aurora-cyan/30'
              : 'bg-black/55 text-white/50 border-white/10 hover:text-white'
          }`}
        >
          {autoRotate ? '⟳ Auto' : '⊙ Manuell'}
        </button>

        {/* Worker-Neustart */}
        <button
          onClick={() => {
            // Neue Zufallspositionen anfordern
            const wRef = (window as typeof window & { __kgWorker?: Worker }).__kgWorker;
            wRef?.postMessage({ type: 'reseed' });
          }}
          className="rounded-xl px-3 py-2 text-xs font-medium backdrop-blur-sm border border-white/10 bg-black/55 text-white/50 hover:text-white transition-all"
        >
          ⚡ Reseed
        </button>
      </div>

      {/* ── Zonen-Legende ────────────────────────────────────────────────── */}
      <div className="absolute bottom-3 left-3 z-10 rounded-xl bg-black/55 backdrop-blur-sm border border-white/10 p-2">
        <div className="font-mono text-[9px] uppercase tracking-widest text-white/40 mb-1">Zonen</div>
        <div className="flex flex-col gap-0.5">
          {Object.entries(ZONE_COLORS).map(([zone, color]) => (
            <div key={zone} className="flex items-center gap-1.5">
              <span className="inline-block w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
              <span className="font-mono text-[10px] text-white/60">{zone}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Kanten-Legende ───────────────────────────────────────────────── */}
      <div className="absolute bottom-3 right-3 z-10 rounded-xl bg-black/55 backdrop-blur-sm border border-white/10 p-2">
        <div className="font-mono text-[9px] uppercase tracking-widest text-white/40 mb-1">Kanten</div>
        <div className="flex flex-col gap-0.5">
          {Object.entries(EDGE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5">
              <span className="inline-block w-4 h-0.5 flex-shrink-0" style={{ backgroundColor: color }} />
              <span className="font-mono text-[10px] text-white/60">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Detail-Drawer (Knoten-Info) ──────────────────────────────────── */}
      {drawerOpen && selectedNode && (
        <div className="absolute inset-y-0 right-0 z-20 w-80 max-w-full flex flex-col">
          <div className="h-full bg-black/80 backdrop-blur-xl border-l border-white/10 flex flex-col p-5 overflow-y-auto">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-aurora-cyan/70">
                  Knoten-Detail
                </div>
                <h2 className="mt-1 text-base font-semibold text-white break-all">
                  {selectedNode.label}
                </h2>
              </div>
              <button
                onClick={() => setDrawerOpen(false)}
                aria-label="Schließen"
                className="ml-2 mt-0.5 flex-shrink-0 rounded-lg p-1.5 text-white/40 hover:text-white hover:bg-white/10 transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Metadaten */}
            <div className="space-y-3 text-sm">
              {[
                { label: 'Zone',       value: selectedNode.zone,     color: ZONE_COLORS[selectedNode.zone] },
                { label: 'Quadrant',   value: selectedNode.quadrant, color: QUADRANT_COLORS[selectedNode.quadrant] },
                { label: 'Spiral',     value: selectedNode.spiral,   color: SPIRAL_COLORS[selectedNode.spiral] },
                { label: 'Verzeichnis',value: selectedNode.dir,      color: null },
                { label: 'Datei-Typ',  value: selectedNode.ext,      color: null },
                { label: 'Größe',      value: String(selectedNode.size), color: null },
              ].map(({ label, value, color }) => (
                <div key={label} className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-24 text-white/40">{label}</span>
                  <span className="flex items-center gap-1.5 text-white/80 break-all">
                    {color && (
                      <span className="inline-block w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                    )}
                    {value}
                  </span>
                </div>
              ))}

              {selectedNode.agent && (
                <div className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-24 text-white/40">Agent</span>
                  <span className="text-aurora-violet/80 break-all">{selectedNode.agent}</span>
                </div>
              )}

              {selectedNode.tags && selectedNode.tags.length > 0 && (
                <div className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-24 text-white/40">Tags</span>
                  <div className="flex flex-wrap gap-1">
                    {selectedNode.tags.map(tag => (
                      <span
                        key={tag}
                        className="rounded px-1.5 py-0.5 bg-aurora-violet/15 text-aurora-violet text-[10px] font-mono"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-3 border-t border-white/10">
                <div className="font-mono text-[10px] text-white/30 break-all">{selectedNode.id}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Lade-Indikator wenn noch kein Knoten sichtbar */}
      {stats.nodes === 0 && (
        <div className="absolute inset-0 z-5 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <div className="mx-auto h-16 w-16 animate-pulse rounded-full bg-gradient-to-br from-aurora-cyan/30 via-aurora-violet/30 to-aurora-magenta/30 blur-lg" />
            <p className="mt-5 font-mono text-xs uppercase tracking-[0.4em] text-white/40">
              3D-Graph materialisiert…
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
