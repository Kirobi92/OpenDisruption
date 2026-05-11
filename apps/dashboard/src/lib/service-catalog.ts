export type ServiceCategory = 'web' | 'backend';

export interface DashboardServiceDefinition {
  name: string;
  label: string;
  description: string;
  port: number;
  category: ServiceCategory;
  healthEndpoint: string;
  openInBrowser: boolean;
}

const DEFAULT_TAILSCALE_HOST = process.env.NEXT_PUBLIC_TAILSCALE_HOST ?? 'pop-os.taildd322d.ts.net';
const DEFAULT_LAN_HOST = process.env.NEXT_PUBLIC_LAN_HOST ?? '192.168.178.10';

export const WEB_FRONTEND_SERVICES: DashboardServiceDefinition[] = [
  {
    name: 'open-webui',
    label: 'Open-WebUI Chat',
    description: 'Zusatzoberfläche für Chat, Modellwechsel und Prompt-Workflows.',
    port: 3000,
    category: 'web',
    healthEndpoint: '/api/proxy/open-webui',
    openInBrowser: true,
  },
  {
    name: 'flowise',
    label: 'Flowise',
    description: 'LangChain-/Flowise-Builder für visuelle Pipelines und Agent-Flows.',
    port: 3001,
    category: 'web',
    healthEndpoint: '/api/proxy/flowise',
    openInBrowser: true,
  },
  {
    name: 'web',
    label: 'Kirobi PWA',
    description: 'Primäre Familienoberfläche für Chat, Upload, Suche und Einstellungen.',
    port: 3002,
    category: 'web',
    healthEndpoint: '/api/proxy/web',
    openInBrowser: true,
  },
  {
    name: 'dashboard',
    label: 'Control Center',
    description: 'Zentrale Operator-Konsole für Services, Tasks, Agenten und Konfiguration.',
    port: 3003,
    category: 'web',
    healthEndpoint: '/api/proxy/dashboard',
    openInBrowser: true,
  },
  {
    name: 'voice-app',
    label: 'Voice Interface',
    description: 'Next.js Voice-UI für Mikrofon, STT/TTS und sprachgesteuerte Sessions.',
    port: 3004,
    category: 'web',
    healthEndpoint: '/api/proxy/voice-app',
    openInBrowser: true,
  },
  {
    name: 'web-svelte',
    label: 'Svelte Web',
    description: 'Alternative Svelte-Oberfläche für die Web-App und Login-Flows.',
    port: 3007,
    category: 'web',
    healthEndpoint: '/api/proxy/web-svelte',
    openInBrowser: true,
  },
  {
    name: 'ollama',
    label: 'Ollama API',
    description: 'Lokaler Modell-Host für Chat-, Reasoning-, Code- und Embedding-Modelle.',
    port: 11434,
    category: 'web',
    healthEndpoint: '/api/proxy/ollama/api/tags',
    openInBrowser: true,
  },
  {
    name: 'qdrant',
    label: 'Qdrant Vector DB',
    description: 'Vektor-Datenbank für Embeddings, Retrieval und zonengetrennte Collections.',
    port: 6333,
    category: 'web',
    healthEndpoint: '/api/proxy/qdrant',
    openInBrowser: true,
  },
  {
    name: 'hermes-runtime',
    label: 'Hermes Agent Dashboard',
    description: 'Dashboard und Gateway für den externen Hermes-Agent-Runtime-Track.',
    port: 9119,
    category: 'web',
    healthEndpoint: '/api/proxy/hermes-runtime',
    openInBrowser: true,
  },
  {
    name: 'openclaw-gateway',
    label: 'OpenClaw Gateway',
    description: 'Gateway für den OpenClaw-Agenten mit lokaler Steuerung und Healthchecks.',
    port: 18789,
    category: 'web',
    healthEndpoint: '/api/proxy/openclaw-gateway',
    openInBrowser: true,
  },
];

export const BACKEND_API_SERVICES: DashboardServiceDefinition[] = [
  {
    name: 'auth',
    label: 'JWT Auth',
    description: 'JWT-Authentifizierung, Zone-Permissions und Audit-Log.',
    port: 8002,
    category: 'backend',
    healthEndpoint: '/api/proxy/auth/health',
    openInBrowser: false,
  },
  {
    name: 'api',
    label: 'Main API',
    description: 'Haupt-API, Ollama-Bridge, Conversations, Messages und Dashboard-Daten.',
    port: 8003,
    category: 'backend',
    healthEndpoint: '/api/proxy/api/health',
    openInBrowser: false,
  },
  {
    name: 'voice-processing',
    label: 'STT / TTS',
    description: 'Whisper STT, Piper TTS und Voice-Bridge für Sprachinteraktionen.',
    port: 8001,
    category: 'backend',
    healthEndpoint: '/api/proxy/voice-processing/health',
    openInBrowser: false,
  },
  {
    name: 'embeddings',
    label: 'Embeddings',
    description: 'Embedding-Service für Einzel-, Batch- und Store-Operationen.',
    port: 8004,
    category: 'backend',
    healthEndpoint: '/api/proxy/embeddings/health',
    openInBrowser: false,
  },
  {
    name: 'telegram',
    label: 'Telegram Bot',
    description: 'Telegram-Bot-Interface mit Zone-Gate und optionalem Hermes-Bot.',
    port: 8005,
    category: 'backend',
    healthEndpoint: '/api/proxy/telegram/health',
    openInBrowser: false,
  },
  {
    name: 'ingest',
    label: 'Document Ingest',
    description: 'Upload, Parsing und ingest_jobs-Verarbeitung für neue Dokumente.',
    port: 8007,
    category: 'backend',
    healthEndpoint: '/api/proxy/ingest/health',
    openInBrowser: false,
  },
  {
    name: 'retrieval',
    label: 'RAG / Search',
    description: 'Such- und RAG-Service mit harter SACRED-403-Grenze.',
    port: 8006,
    category: 'backend',
    healthEndpoint: '/api/proxy/retrieval/health',
    openInBrowser: false,
  },
  {
    name: 'model-routing',
    label: 'Model Routing',
    description: 'Deterministisches Routing zwischen lokalen und externen Modellen.',
    port: 8009,
    category: 'backend',
    healthEndpoint: '/api/proxy/model-routing/health',
    openInBrowser: false,
  },
  {
    name: 'analytics',
    label: 'Analytics',
    description: 'Event-Tracking sowie Zonen-, Tages- und Modell-Statistiken.',
    port: 8010,
    category: 'backend',
    healthEndpoint: '/api/proxy/analytics/health',
    openInBrowser: false,
  },
  {
    name: 'image-generation',
    label: 'Image Gen',
    description: 'Bildgenerierung mit Job-Tracking und generated_images.',
    port: 8011,
    category: 'backend',
    healthEndpoint: '/api/proxy/image-generation/health',
    openInBrowser: false,
  },
  {
    name: 'media-processing',
    label: 'Media',
    description: 'Pillow- und Mutagen-basierte Medienverarbeitung mit Fallbacks.',
    port: 8012,
    category: 'backend',
    healthEndpoint: '/api/proxy/media-processing/health',
    openInBrowser: false,
  },
  {
    name: 'music-generation',
    label: 'Music',
    description: 'Asynchrone Musikjobs und generated_tracks-Verwaltung.',
    port: 8013,
    category: 'backend',
    healthEndpoint: '/api/proxy/music-generation/health',
    openInBrowser: false,
  },
  {
    name: 'video-generation',
    label: 'Video',
    description: 'Asynchrone Videogenerierung und generated_videos.',
    port: 8014,
    category: 'backend',
    healthEndpoint: '/api/proxy/video-generation/health',
    openInBrowser: false,
  },
];

export const ALL_DASHBOARD_SERVICES = [...WEB_FRONTEND_SERVICES, ...BACKEND_API_SERVICES];

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

export function getServiceUrl(port: number): string {
  const hostname = typeof window === 'undefined' ? DEFAULT_LAN_HOST : resolveServiceHost(window.location.hostname);
  return `http://${hostname}:${port}`;
}
