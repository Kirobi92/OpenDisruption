'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ElementType } from 'react';
import axios from 'axios';
import {
  ArrowPathIcon,
  ArrowTopRightOnSquareIcon,
  BoltIcon,
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  CircleStackIcon,
  ClockIcon,
  CommandLineIcon,
  CpuChipIcon,
  CubeTransparentIcon,
  ExclamationTriangleIcon,
  FilmIcon,
  HomeIcon,
  MicrophoneIcon,
  MusicalNoteIcon,
  PhotoIcon,
  QueueListIcon,
  ServerIcon,
  ShieldCheckIcon,
  SparklesIcon,
  Squares2X2Icon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import type { DashboardServiceDefinition } from '@/lib/service-catalog';
import {
  AI_AGENT_SERVICES,
  KNOWLEDGE_SERVICES,
  COMMUNICATION_SERVICES,
  GENERATION_SERVICES,
  INFRASTRUCTURE_SERVICES,
  ALL_DASHBOARD_SERVICES,
  getServiceOpenUrl,
  resolveServiceHost,
} from '@/lib/service-catalog';

type ServiceStatus = 'online' | 'offline' | 'unknown';

interface ServiceDetail extends DashboardServiceDefinition {
  status: ServiceStatus;
  latencyMs: number | null;
  lastChecked: Date | null;
}

const SERVICE_ICONS: Record<string, ElementType> = {
  'hermes-runtime': CubeTransparentIcon,
  'openclaw-gateway': CommandLineIcon,
  opencode: CpuChipIcon,
  flowise: SparklesIcon,
  'open-webui': ChatBubbleLeftRightIcon,
  qdrant: CircleStackIcon,
  'vault-graph': Squares2X2Icon,
  'knowledge-graph-3d': Squares2X2Icon,
  embeddings: SparklesIcon,
  retrieval: CircleStackIcon,
  ingest: QueueListIcon,
  web: HomeIcon,
  'voice-app': MicrophoneIcon,
  'telegram-hermes': BoltIcon,
  telegram: ChatBubbleLeftRightIcon,
  'voice-processing': MicrophoneIcon,
  'image-generation': PhotoIcon,
  'music-generation': MusicalNoteIcon,
  'video-generation': FilmIcon,
  'media-processing': PhotoIcon,
  ollama: CommandLineIcon,
  api: ServerIcon,
  auth: ShieldCheckIcon,
  'model-routing': CommandLineIcon,
  analytics: Squares2X2Icon,
  'web-svelte': CpuChipIcon,
};

interface CategoryConfig {
  title: string;
  subtitle: string;
  accent: string;
  headerBg: string;
  iconBg: string;
  badgeBg: string;
  services: DashboardServiceDefinition[];
}

const CATEGORIES: CategoryConfig[] = [
  {
    title: '🤖 KI-Agenten & Orchestrierung',
    subtitle: 'Hermes, OpenClaw, OpenCode, Flowise und Open-WebUI — alle KI-Werkzeuge zentral.',
    accent: 'violet',
    headerBg: 'border-violet-500/20 bg-violet-500/5',
    iconBg: 'bg-violet-500/10 text-violet-400',
    badgeBg: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
    services: AI_AGENT_SERVICES,
  },
  {
    title: '🧠 Wissen & Vektordatenbank',
    subtitle: 'Qdrant, Vault-Graph, Embeddings, Retrieval und Document Ingest.',
    accent: 'cyan',
    headerBg: 'border-cyan-500/20 bg-cyan-500/5',
    iconBg: 'bg-cyan-500/10 text-cyan-400',
    badgeBg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    services: KNOWLEDGE_SERVICES,
  },
  {
    title: '💬 Kommunikation & Sprache',
    subtitle: 'Kirobi-PWA, Voice-Interface, Telegram-Bots und STT/TTS-Processing.',
    accent: 'emerald',
    headerBg: 'border-emerald-500/20 bg-emerald-500/5',
    iconBg: 'bg-emerald-500/10 text-emerald-400',
    badgeBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    services: COMMUNICATION_SERVICES,
  },
  {
    title: '🎨 Medien & Generierung',
    subtitle: 'Bild-, Musik- und Video-Generierung sowie Medienverarbeitung.',
    accent: 'amber',
    headerBg: 'border-amber-500/20 bg-amber-500/5',
    iconBg: 'bg-amber-500/10 text-amber-400',
    badgeBg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    services: GENERATION_SERVICES,
  },
  {
    title: '⚙️ Infrastruktur & APIs',
    subtitle: 'Ollama LLM Host, Main API, Auth, Model-Routing, Analytics und Svelte-Web.',
    accent: 'slate',
    headerBg: 'border-gray-600/30 bg-gray-800/30',
    iconBg: 'bg-gray-700/50 text-gray-400',
    badgeBg: 'bg-gray-700 text-gray-400 border-gray-600',
    services: INFRASTRUCTURE_SERVICES,
  },
];

function formatRelativeTime(date: Date | null): string {
  if (!date) return '—';
  const diffMs = Date.now() - date.getTime();
  if (diffMs < 5_000) return 'gerade eben';
  if (diffMs < 60_000) return `vor ${Math.floor(diffMs / 1000)}s`;
  if (diffMs < 3_600_000) return `vor ${Math.floor(diffMs / 60_000)}min`;
  return `vor ${Math.floor(diffMs / 3_600_000)}h`;
}

function StatusDot({ status }: { status: ServiceStatus }) {
  if (status === 'online') return <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />;
  if (status === 'offline') return <span className="inline-block h-2 w-2 rounded-full bg-red-500" />;
  return <span className="inline-block h-2 w-2 rounded-full bg-amber-500/60 animate-pulse" />;
}

function StatusBadge({ status }: { status: ServiceStatus }) {
  const base = 'inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium';
  if (status === 'online') return <span className={`${base} border-emerald-500/20 bg-emerald-500/10 text-emerald-400`}><CheckCircleIcon className="h-3 w-3" />Online</span>;
  if (status === 'offline') return <span className={`${base} border-red-500/20 bg-red-500/10 text-red-400`}><XCircleIcon className="h-3 w-3" />Offline</span>;
  return <span className={`${base} border-amber-500/20 bg-amber-500/10 text-amber-400`}><ExclamationTriangleIcon className="h-3 w-3" />Prüft…</span>;
}

function ServiceCard({
  service,
  iconBg,
  badgeBg,
  openUrl,
}: {
  service: ServiceDetail;
  iconBg: string;
  badgeBg: string;
  openUrl: string | null;
}) {
  const Icon = SERVICE_ICONS[service.name] ?? ServerIcon;

  return (
    <div
      className={`card space-y-3 transition-all duration-300 ${
        service.status === 'online' ? 'border-gray-700/60' : service.status === 'offline' ? 'border-red-900/30' : 'border-gray-700/40'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className={`flex-shrink-0 rounded-xl p-2 ${service.status === 'online' ? iconBg : 'bg-gray-800 text-gray-500'}`}>
            <Icon className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-sm font-semibold text-white leading-tight">{service.label}</p>
              {service.badge && (
                <span className={`inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${badgeBg}`}>
                  {service.badge}
                </span>
              )}
            </div>
            <p className="mt-0.5 text-xs font-mono text-gray-600">
              {service.caddyPath ? service.caddyPath : `…:${service.port}`}
            </p>
          </div>
        </div>
        <StatusBadge status={service.status} />
      </div>

      <p className="text-xs leading-relaxed text-gray-400">{service.description}</p>

      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 text-xs text-gray-600">
          <span className="flex items-center gap-1">
            <ClockIcon className="h-3 w-3" />
            {formatRelativeTime(service.lastChecked)}
          </span>
          {service.latencyMs !== null && (
            <span className="font-mono text-gray-500">{service.latencyMs}ms</span>
          )}
        </div>
        {service.openInBrowser && openUrl && (
          <a
            href={openUrl}
            target="_blank"
            rel="noreferrer"
            className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all ${
              service.status === 'online'
                ? 'border-kirobi-500/30 bg-kirobi-500/10 text-kirobi-300 hover:border-kirobi-400/40 hover:text-white'
                : 'border-gray-700 bg-gray-800 text-gray-500 hover:text-gray-300'
            }`}
          >
            <ArrowTopRightOnSquareIcon className="h-3.5 w-3.5" />
            Öffnen
          </a>
        )}
      </div>
    </div>
  );
}

function CategorySection({
  config,
  services,
}: {
  config: CategoryConfig;
  services: Map<string, ServiceDetail>;
}) {
  const details = config.services.map(
    (s) => services.get(s.name) ?? { ...s, status: 'unknown' as ServiceStatus, latencyMs: null, lastChecked: null }
  );
  const online = details.filter((s) => s.status === 'online').length;
  const total = details.length;

  return (
    <section className="space-y-4">
      <div className={`rounded-2xl border px-5 py-4 ${config.headerBg}`}>
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-sm font-semibold text-white">{config.title}</h2>
            <p className="mt-0.5 text-xs text-gray-400">{config.subtitle}</p>
          </div>
          <span className="text-xs font-mono text-gray-400">
            <span className={online === total ? 'text-emerald-400' : 'text-amber-400'}>{online}</span>
            <span className="text-gray-600">/{total} online</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {details.map((service) => (
          <ServiceCard
            key={service.name}
            service={service}
            iconBg={config.iconBg}
            badgeBg={config.badgeBg}
            openUrl={getServiceOpenUrl(service)}
          />
        ))}
      </div>
    </section>
  );
}

export default function ServicesPage() {
  const [serviceMap, setServiceMap] = useState<Map<string, ServiceDetail>>(
    () => new Map(ALL_DASHBOARD_SERVICES.map((s) => [s.name, { ...s, status: 'unknown', latencyMs: null, lastChecked: null }]))
  );
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [resolvedHost, setResolvedHost] = useState<string | null>(null);

  const checkAll = useCallback(async () => {
    setRefreshing(true);
    const results = await Promise.all(
      ALL_DASHBOARD_SERVICES.map(async (service) => {
        const startedAt = Date.now();
        try {
          const response = await axios.get(service.healthEndpoint, { timeout: 6000 });
          const ok = response.status >= 200 && response.status < 400;
          return [service.name, {
            ...service,
            status: ok ? 'online' as ServiceStatus : 'offline' as ServiceStatus,
            latencyMs: Date.now() - startedAt,
            lastChecked: new Date(),
          }] as const;
        } catch {
          return [service.name, {
            ...service,
            status: 'offline' as ServiceStatus,
            latencyMs: null,
            lastChecked: new Date(),
          }] as const;
        }
      })
    );
    setServiceMap(new Map(results as Array<[string, ServiceDetail]>));
    setLastRefresh(new Date());
    setRefreshing(false);
  }, []);

  useEffect(() => {
    checkAll();
    const interval = setInterval(checkAll, 30_000);
    return () => clearInterval(interval);
  }, [checkAll]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setResolvedHost(resolveServiceHost(window.location.hostname));
    }
  }, []);

  const allServices = useMemo(() => Array.from(serviceMap.values()), [serviceMap]);
  const onlineCount = allServices.filter((s) => s.status === 'online').length;
  const offlineCount = allServices.filter((s) => s.status === 'offline').length;
  const progress = allServices.length > 0 ? Math.round((onlineCount / allServices.length) * 100) : 0;

  return (
    <>
      <header className="sticky top-0 z-10 border-b border-gray-700/60 bg-gray-900/80 px-6 py-4 backdrop-blur">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-base font-semibold text-white">Services</h1>
            <p className="mt-0.5 text-xs text-gray-500">
              Alle {allServices.length} OpenDisruption-Services in 5 Kategorien.
              {resolvedHost && (
                <> Öffnen via <span className="font-mono text-gray-400">{resolvedHost}</span></>
              )}
            </p>
          </div>
          <div className="flex items-center gap-3 flex-wrap justify-end">
            <div className="inline-flex items-center gap-2 rounded-full border border-gray-700/60 bg-gray-900/70 px-3 py-1.5 text-xs font-mono text-gray-400">
              <StatusDot status="online" />
              <span className="text-emerald-400">{onlineCount}</span>
              {offlineCount > 0 && <><span className="text-gray-600">·</span><StatusDot status="offline" /><span className="text-red-400">{offlineCount}</span></>}
            </div>
            <button
              onClick={checkAll}
              disabled={refreshing}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-xs font-medium text-gray-300 transition-all hover:border-gray-600 hover:text-white disabled:opacity-50"
            >
              <ArrowPathIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Lädt…' : 'Aktualisieren'}
            </button>
          </div>
        </div>

        <div className="mt-3 flex items-center gap-3">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-kirobi-500 transition-all duration-700"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-xs font-mono text-gray-500">{progress}%</span>
          <span className="text-xs text-gray-600">
            {lastRefresh ? formatRelativeTime(lastRefresh) : 'Noch nicht geprüft'}
          </span>
        </div>
      </header>

      <div className="space-y-8 p-6">
        {CATEGORIES.map((cat) => (
          <CategorySection key={cat.title} config={cat} services={serviceMap} />
        ))}
      </div>
    </>
  );
}
