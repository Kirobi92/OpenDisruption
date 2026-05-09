export type SurfaceKind = 'native' | 'ops' | 'workbench';

export interface RuntimeSurface {
  id: string;
  label: string;
  path: string;
  directPath: string;
  summary: string;
  badge: string;
  kind: SurfaceKind;
  guard?: string;
}

export interface RuntimeProbe {
  id: string;
  path: string;
}

export const RUNTIME_SURFACES: RuntimeSurface[] = [
  {
    id: 'knowledge-base',
    label: 'Knowledge Base',
    path: '/knowledge-base',
    directPath: '/knowledge-base',
    summary: 'Uploads, Wissenssuche, Graph-Einstieg und Zonenüberblick an einem Ort.',
    badge: 'Native',
    kind: 'native',
    guard: 'JWT',
  },
  {
    id: 'agents-hub',
    label: 'Agents',
    path: '/agents-hub',
    directPath: '/agents-hub',
    summary: 'Hermes, Opencode, KeyCodi und Operator-Signale in einer Ansicht.',
    badge: 'Native',
    kind: 'native',
    guard: 'JWT',
  },
  {
    id: 'chat',
    label: 'Chat',
    path: '/chat',
    directPath: '/chat',
    summary: 'Direkter Einstieg in lokale Gespräche und Assistenz.',
    badge: 'Native',
    kind: 'native',
    guard: 'JWT',
  },
  {
    id: 'search',
    label: 'Knowledge Search',
    path: '/search',
    directPath: '/search',
    summary: 'RAG, Upload-Treffer und Zonenwissen durchsuchen.',
    badge: 'Native',
    kind: 'native',
    guard: 'JWT',
  },
  {
    id: 'upload',
    label: 'Upload',
    path: '/upload',
    directPath: '/upload',
    summary: 'Dateien und Schnellnotizen lokal in Zonen einspeisen.',
    badge: 'Native',
    kind: 'native',
    guard: 'JWT',
  },
  {
    id: 'developer-studio',
    label: 'Developer Studio',
    path: '/developer-studio',
    directPath: '/developer-studio',
    summary: 'VS Code Deep Link, Opencode-Workbench und repo-nahe Developer-Shortcuts.',
    badge: 'Native',
    kind: 'native',
    guard: 'Local workstation',
  },
  {
    id: 'dashboard',
    label: 'Ops Dashboard',
    path: '/dashboard/',
    directPath: '/dashboard/',
    summary: 'Service-, Task- und Analytics-Oberfläche für Operatoren.',
    badge: 'Ops',
    kind: 'ops',
    guard: 'Local operator',
  },
  {
    id: 'agents',
    label: 'Agent Registry',
    path: '/dashboard/agents',
    directPath: '/dashboard/agents',
    summary: 'Agentenrollen, Berechtigungen und Zustände einsehen.',
    badge: 'Ops',
    kind: 'ops',
    guard: 'Local operator',
  },
  {
    id: 'services',
    label: 'Service Matrix',
    path: '/dashboard/services',
    directPath: '/dashboard/services',
    summary: 'Alle Laufzeitdienste, Ports und Health-Probes an einem Ort.',
    badge: 'Ops',
    kind: 'ops',
    guard: 'Local operator',
  },
  {
    id: 'open-webui',
    label: 'Open WebUI',
    path: '/workbench?surface=open-webui',
    directPath: '/open-webui/',
    summary: 'LLM-Workbench für tiefe Modellinteraktion und Experimente.',
    badge: 'Workbench',
    kind: 'workbench',
    guard: 'Secure edge path + Open WebUI login',
  },
  {
    id: 'flowise',
    label: 'Flowise',
    path: '/workbench?surface=flowise',
    directPath: '/flowise/',
    summary: 'Visuelle Flow- und Agent-Orchestrierung über Caddy.',
    badge: 'Workbench',
    kind: 'workbench',
    guard: 'Secure edge path + Flowise login',
  },
  {
    id: 'qdrant',
    label: 'Qdrant',
    path: '/workbench?surface=qdrant',
    directPath: '/qdrant/dashboard/',
    summary: 'Vektor-DB-Diagnostik und Collection-Checks.',
    badge: 'Workbench',
    kind: 'workbench',
    guard: 'Secure edge path; direct tab preferred',
  },
];

export const RUNTIME_PROBES: RuntimeProbe[] = [
  { id: 'api', path: '/api/health' },
  { id: 'auth', path: '/api/auth/health' },
  { id: 'telegram', path: '/telegram/health' },
  { id: 'voice', path: '/voice/health' },
];
