export type ServiceCategory =
  | 'ai-agent'      // Hermes, OpenClaw, OpenCode, Flowise, Open-WebUI
  | 'knowledge'     // Qdrant, Vault Graph, Embeddings, Retrieval, Ingest
  | 'communication' // Kirobi PWA, Voice App, Telegram bots, Voice Processing
  | 'generation'    // Image, Music, Video, Media
  | 'infrastructure'; // API, Auth, Ollama, Model Routing, Analytics

export interface DashboardServiceDefinition {
  name: string;
  label: string;
  description: string;
  /** External host port (for display and direct URL fallback) */
  port: number;
  category: ServiceCategory;
  healthEndpoint: string;
  openInBrowser: boolean;
  /** Caddy reverse-proxy path (relative to origin). Use instead of :port when set. */
  caddyPath?: string;
  /** Short badge text (optional) */
  badge?: string;
}

const DEFAULT_TAILSCALE_HOST = process.env.NEXT_PUBLIC_TAILSCALE_HOST ?? 'pop-os.taildd322d.ts.net';
const DEFAULT_LAN_HOST = process.env.NEXT_PUBLIC_LAN_HOST ?? '192.168.178.10';

export const AI_AGENT_SERVICES: DashboardServiceDefinition[] = [
  {
    name: 'hermes-runtime',
    label: 'Hermes Dashboard',
    description: 'Hermes / Kirobi — Haupt-KI-Orchestrator. Terminal, Skill-Tree, MCP-Tools, Telegram-Gateway.',
    port: 9119,
    category: 'ai-agent',
    healthEndpoint: '/api/proxy/hermes-runtime',
    openInBrowser: true,
    caddyPath: '/hermes/',
    badge: 'Orchestrator',
  },
  {
    name: 'openclaw-gateway',
    label: 'OpenClaw Gateway',
    description: 'OpenClaw-Agent für Dateisystem-Operationen, Git-Workflows und Code-Ausführung.',
    port: 18789,
    category: 'ai-agent',
    healthEndpoint: '/api/proxy/openclaw-gateway',
    openInBrowser: true,
    caddyPath: '/openclaw/',
  },
  {
    name: 'opencode',
    label: 'OpenCode Studio',
    description: 'Lokales KI-Code-Studio (OpenCode). Multi-Modell, Datei-Editor, GitHub Copilot.',
    port: 4096,
    category: 'ai-agent',
    healthEndpoint: '/api/proxy/opencode',
    openInBrowser: true,
    badge: 'Code-KI',
  },
  {
    name: 'flowise',
    label: 'Flowise Builder',
    description: 'Visuelle LangChain-/Flowise-Pipelines für Agent-Flows, RAG-Ketten und Automatisierungen.',
    port: 3001,
    category: 'ai-agent',
    healthEndpoint: '/api/proxy/flowise',
    openInBrowser: true,
    caddyPath: '/flowise/',
  },
  {
    name: 'open-webui',
    label: 'Open-WebUI Chat',
    description: 'Chat-Oberfläche für alle Ollama-Modelle mit Prompt-Vorlagen, Verlauf und Multi-User.',
    port: 3000,
    category: 'ai-agent',
    healthEndpoint: '/api/proxy/open-webui',
    openInBrowser: true,
    caddyPath: '/open-webui/',
  },
];

export const KNOWLEDGE_SERVICES: DashboardServiceDefinition[] = [
  {
    name: 'qdrant',
    label: 'Qdrant Vector DB',
    description: 'Vektor-Datenbank für Embeddings und zonengetrennte RAG-Collections. UI-Dashboard inklusive.',
    port: 6333,
    category: 'knowledge',
    healthEndpoint: '/api/proxy/qdrant',
    openInBrowser: true,
    caddyPath: '/qdrant/',
    badge: 'Vektordatenbank',
  },
  {
    name: 'vault-graph',
    label: 'Vault 3D Graph',
    description: 'Interaktiver 3D-Wissens-Graph aller Kirobi-Dokumente. ThreeJS + SvelteKit.',
    port: 3007,
    category: 'knowledge',
    healthEndpoint: '/api/proxy/web-svelte',
    openInBrowser: true,
    caddyPath: '/v2/graph',
    badge: '3D Graph',
  },
  {
    name: 'knowledge-graph-3d',
    label: 'Knowledge Graph 3D',
    description: 'High-End 3D-Wissens-Visualisierung aus der Kirobi-PWA mit WebGL-Rendering.',
    port: 3002,
    category: 'knowledge',
    healthEndpoint: '/api/proxy/web',
    openInBrowser: true,
    caddyPath: '/knowledge-graph-3d',
  },
  {
    name: 'embeddings',
    label: 'Embeddings Service',
    description: 'nomic-embed-text (768dim) — Einzel-, Batch- und Store-Endpunkte für Vektorisierung.',
    port: 8004,
    category: 'knowledge',
    healthEndpoint: '/api/proxy/embeddings/health',
    openInBrowser: false,
  },
  {
    name: 'retrieval',
    label: 'RAG / Retrieval',
    description: 'Semantische Suche und RAG über alle Qdrant-Collections. SACRED immer 403.',
    port: 8006,
    category: 'knowledge',
    healthEndpoint: '/api/proxy/retrieval/health',
    openInBrowser: false,
  },
  {
    name: 'ingest',
    label: 'Document Ingest',
    description: 'Dokument-Upload, Text-Parsing, Chunking und ingest_jobs-Tracking.',
    port: 8007,
    category: 'knowledge',
    healthEndpoint: '/api/proxy/ingest/health',
    openInBrowser: false,
  },
];

export const COMMUNICATION_SERVICES: DashboardServiceDefinition[] = [
  {
    name: 'web',
    label: 'Kirobi PWA',
    description: 'Primäre Familien-App mit Chat, Datei-Upload, Suche, Einstellungen und Wissensbasis.',
    port: 3002,
    category: 'communication',
    healthEndpoint: '/api/proxy/web',
    openInBrowser: true,
    caddyPath: '/',
    badge: 'Haupt-App',
  },
  {
    name: 'voice-app',
    label: 'Voice Interface',
    description: 'Sprach-UI mit MediaRecorder, Echtzeit-STT/TTS und sprachgesteuerten Sessions.',
    port: 3004,
    category: 'communication',
    healthEndpoint: '/api/proxy/voice-app',
    openInBrowser: true,
  },
  {
    name: 'telegram-hermes',
    label: 'Hermes Telegram Bot',
    description: 'Telegram-Gateway für Hermes — natürlichsprachige Steuerung des gesamten Systems.',
    port: 8015,
    category: 'communication',
    healthEndpoint: '/api/proxy/telegram-hermes/health',
    openInBrowser: false,
    badge: 'Telegram',
  },
  {
    name: 'telegram',
    label: 'KeyCodi Telegram Bot',
    description: 'Telegram-Bot-Interface mit Zone-Gate, Cron-Meldungen und KeyCodi-Befehlen.',
    port: 8005,
    category: 'communication',
    healthEndpoint: '/api/proxy/telegram/ready',
    openInBrowser: false,
  },
  {
    name: 'voice-processing',
    label: 'STT / TTS Processing',
    description: 'Whisper STT (lokal) + Piper TTS — Voice-Bridge für alle Sprach-Interfaces.',
    port: 8001,
    category: 'communication',
    healthEndpoint: '/api/proxy/voice-processing/health',
    openInBrowser: false,
  },
];

export const GENERATION_SERVICES: DashboardServiceDefinition[] = [
  {
    name: 'image-generation',
    label: 'Bild-Generierung',
    description: 'KI-Bildgenerierung via Ollama / Stable Diffusion mit generated_images-Tracking.',
    port: 8011,
    category: 'generation',
    healthEndpoint: '/api/proxy/image-generation/health',
    openInBrowser: false,
  },
  {
    name: 'music-generation',
    label: 'Musik-Generierung',
    description: 'Asynchrone Musik-Jobs mit generated_tracks-Verwaltung und MIDI-Export.',
    port: 8013,
    category: 'generation',
    healthEndpoint: '/api/proxy/music-generation/health',
    openInBrowser: false,
  },
  {
    name: 'video-generation',
    label: 'Video-Generierung',
    description: 'Asynchrone Video-Generierung und generated_videos-Verwaltung.',
    port: 8014,
    category: 'generation',
    healthEndpoint: '/api/proxy/video-generation/health',
    openInBrowser: false,
  },
  {
    name: 'media-processing',
    label: 'Medienverarbeitung',
    description: 'Pillow- und Mutagen-basierte Medienverarbeitung mit graceful Fallbacks.',
    port: 8012,
    category: 'generation',
    healthEndpoint: '/api/proxy/media-processing/health',
    openInBrowser: false,
  },
];

export const INFRASTRUCTURE_SERVICES: DashboardServiceDefinition[] = [
  {
    name: 'ollama',
    label: 'Ollama LLM Host',
    description: 'Lokaler Modell-Host für alle Chat-, Reasoning-, Code- und Embedding-Modelle.',
    port: 11434,
    category: 'infrastructure',
    healthEndpoint: '/api/proxy/ollama/api/tags',
    openInBrowser: false,
    badge: 'LLM Host',
  },
  {
    name: 'api',
    label: 'Main API',
    description: 'Haupt-API: Conversations, Messages, Ollama-Bridge und Dashboard-Daten.',
    port: 8003,
    category: 'infrastructure',
    healthEndpoint: '/api/proxy/api/health',
    openInBrowser: false,
  },
  {
    name: 'auth',
    label: 'JWT Auth',
    description: 'JWT-Authentifizierung, Zone-Permissions und Audit-Log.',
    port: 8002,
    category: 'infrastructure',
    healthEndpoint: '/api/proxy/auth/health',
    openInBrowser: false,
  },
  {
    name: 'model-routing',
    label: 'Model Routing',
    description: 'Deterministisches Routing zwischen lokalen Ollama-Modellen und externen APIs.',
    port: 8009,
    category: 'infrastructure',
    healthEndpoint: '/api/proxy/model-routing/health',
    openInBrowser: false,
  },
  {
    name: 'analytics',
    label: 'Analytics',
    description: 'Event-Tracking sowie Zonen-, Tages- und Modell-Statistiken.',
    port: 8010,
    category: 'infrastructure',
    healthEndpoint: '/api/proxy/analytics/health',
    openInBrowser: false,
  },
  {
    name: 'web-svelte',
    label: 'Svelte Web (v2)',
    description: 'Alternative SvelteKit-Oberfläche mit Vault-Graph, Login-Flows und Komponenten-Bibliothek.',
    port: 3007,
    category: 'infrastructure',
    healthEndpoint: '/api/proxy/web-svelte',
    openInBrowser: true,
    caddyPath: '/v2/',
  },
];

export const ALL_DASHBOARD_SERVICES = [
  ...AI_AGENT_SERVICES,
  ...KNOWLEDGE_SERVICES,
  ...COMMUNICATION_SERVICES,
  ...GENERATION_SERVICES,
  ...INFRASTRUCTURE_SERVICES,
];

// Legacy exports (keep backward compat with page.tsx overview)
export const WEB_FRONTEND_SERVICES = AI_AGENT_SERVICES;
export const BACKEND_API_SERVICES = INFRASTRUCTURE_SERVICES;

function isPrivateLanHost(hostname: string): boolean {
  return hostname.startsWith('192.168.') || hostname.startsWith('10.') || /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname);
}

function isTailscaleHost(hostname: string): boolean {
  return hostname.startsWith('100.') || hostname.endsWith('.ts.net') || hostname === DEFAULT_TAILSCALE_HOST;
}

export function resolveServiceHost(hostname: string): string {
  if (!hostname) return DEFAULT_LAN_HOST;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return hostname;
  if (isTailscaleHost(hostname)) return DEFAULT_TAILSCALE_HOST;
  if (hostname === DEFAULT_LAN_HOST || isPrivateLanHost(hostname)) return DEFAULT_LAN_HOST;
  return hostname;
}

/** Fallback: direct host:port URL (for services without a Caddy path) */
export function getServiceUrl(port: number): string {
  const hostname = typeof window === 'undefined' ? DEFAULT_LAN_HOST : resolveServiceHost(window.location.hostname);
  return `http://${hostname}:${port}`;
}

/**
 * Returns the best open URL for a service.
 * Prefers <origin><caddyPath> so it works transparently over Tailscale/LAN.
 */
export function getServiceOpenUrl(service: DashboardServiceDefinition): string | null {
  if (!service.openInBrowser) return null;
  if (typeof window === 'undefined') return null;
  if (service.caddyPath) {
    return `${window.location.protocol}//${window.location.hostname}${service.caddyPath}`;
  }
  return getServiceUrl(service.port);
}
