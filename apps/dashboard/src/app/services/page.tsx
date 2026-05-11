'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ElementType } from 'react';
import axios from 'axios';
import {
  ArrowPathIcon,
  ArrowTopRightOnSquareIcon,
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  CircleStackIcon,
  ClockIcon,
  CommandLineIcon,
  CubeTransparentIcon,
  ExclamationTriangleIcon,
  HomeIcon,
  MicrophoneIcon,
  PhotoIcon,
  QueueListIcon,
  ServerIcon,
  SparklesIcon,
  Squares2X2Icon,
  SwatchIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import type { DashboardServiceDefinition } from '@/lib/service-catalog';
import {
  ALL_DASHBOARD_SERVICES,
  getServiceUrl,
  resolveServiceHost,
} from '@/lib/service-catalog';

type ServiceStatus = 'online' | 'offline' | 'unknown';

interface ServiceDetail extends DashboardServiceDefinition {
  status: ServiceStatus;
  latencyMs: number | null;
  lastChecked: Date | null;
  responseData: Record<string, unknown> | null;
}

const SERVICE_ICONS: Record<string, ElementType> = {
  'open-webui': ChatBubbleLeftRightIcon,
  flowise: SparklesIcon,
  web: HomeIcon,
  dashboard: Squares2X2Icon,
  'voice-app': MicrophoneIcon,
  'web-svelte': SwatchIcon,
  ollama: CommandLineIcon,
  qdrant: CircleStackIcon,
  'hermes-runtime': CubeTransparentIcon,
  'openclaw-gateway': QueueListIcon,
  auth: CheckCircleIcon,
  api: ServerIcon,
  'voice-processing': MicrophoneIcon,
  embeddings: SparklesIcon,
  telegram: ChatBubbleLeftRightIcon,
  ingest: QueueListIcon,
  retrieval: CircleStackIcon,
  'model-routing': CommandLineIcon,
  analytics: Squares2X2Icon,
  'image-generation': PhotoIcon,
  'media-processing': SwatchIcon,
  'music-generation': SparklesIcon,
  'video-generation': PhotoIcon,
};

function formatRelativeTime(date: Date | null): string {
  if (!date) return '—';
  const diffMs = Date.now() - date.getTime();
  if (diffMs < 5_000) return 'gerade eben';
  if (diffMs < 60_000) return `vor ${Math.floor(diffMs / 1000)}s`;
  if (diffMs < 3_600_000) return `vor ${Math.floor(diffMs / 60_000)}min`;
  return `vor ${Math.floor(diffMs / 3_600_000)}h`;
}

function StatusBadge({ status }: { status: ServiceStatus }) {
  const base = 'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium';
  if (status === 'online') {
    return (
      <span className={`${base} border-emerald-500/20 bg-emerald-500/10 text-emerald-400`}>
        <CheckCircleIcon className="h-3.5 w-3.5" />
        Online
      </span>
    );
  }
  if (status === 'offline') {
    return (
      <span className={`${base} border-red-500/20 bg-red-500/10 text-red-400`}>
        <XCircleIcon className="h-3.5 w-3.5" />
        Offline
      </span>
    );
  }
  return (
    <span className={`${base} border-amber-500/20 bg-amber-500/10 text-amber-400`}>
      <ExclamationTriangleIcon className="h-3.5 w-3.5" />
      Unbekannt
    </span>
  );
}

function ServiceCard({ service, canOpen }: { service: ServiceDetail; canOpen: boolean }) {
  const Icon = SERVICE_ICONS[service.name] ?? ServerIcon;
  const openUrl = canOpen && service.openInBrowser ? getServiceUrl(service.port) : null;

  return (
    <div className="card space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-center gap-3">
          <div
            className={`rounded-xl p-2.5 ${
              service.status === 'online'
                ? 'bg-emerald-500/10 text-emerald-400'
                : service.status === 'offline'
                  ? 'bg-red-500/10 text-red-400'
                  : 'bg-gray-700 text-gray-400'
            }`}
          >
            <Icon className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-white">{service.label}</p>
            <p className="mt-0.5 text-xs font-mono text-gray-500">:{service.port}</p>
          </div>
        </div>
        <StatusBadge status={service.status} />
      </div>

      <p className="text-sm leading-relaxed text-gray-400">{service.description}</p>

      <div className="grid grid-cols-2 gap-3 text-xs text-gray-500">
        <div className="rounded-xl border border-gray-700/60 bg-gray-900/60 px-3 py-2">
          <p className="uppercase tracking-wider text-gray-600">Latenz</p>
          <p className="mt-1 font-mono text-gray-300">{service.latencyMs !== null ? `${service.latencyMs}ms` : '—'}</p>
        </div>
        <div className="rounded-xl border border-gray-700/60 bg-gray-900/60 px-3 py-2">
          <p className="uppercase tracking-wider text-gray-600">Geprüft</p>
          <p className="mt-1 text-gray-300">{formatRelativeTime(service.lastChecked)}</p>
        </div>
      </div>

      <div className="flex items-center justify-between gap-3">
        <p className="truncate text-xs font-mono text-gray-600">{service.healthEndpoint}</p>
        {service.openInBrowser && (
          <a
            href={openUrl ?? undefined}
            target="_blank"
            rel="noreferrer"
            aria-disabled={!openUrl}
            className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium transition-all ${
              openUrl
                ? 'border-kirobi-500/30 bg-kirobi-500/10 text-kirobi-300 hover:border-kirobi-400/40 hover:text-white'
                : 'cursor-not-allowed border-gray-700 bg-gray-800 text-gray-600'
            }`}
          >
            <ArrowTopRightOnSquareIcon className="h-4 w-4" />
            Öffnen
          </a>
        )}
      </div>
    </div>
  );
}

function ServiceSection({
  title,
  subtitle,
  services,
  canOpen,
}: {
  title: string;
  subtitle: string;
  services: ServiceDetail[];
  canOpen: boolean;
}) {
  return (
    <section className="space-y-4">
      <div className="flex items-end justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
        </div>
        <span className="rounded-full border border-gray-700/60 bg-gray-900/60 px-3 py-1 text-xs font-mono text-gray-400">
          {services.length} Services
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {services.map((service) => (
          <ServiceCard key={service.name} service={service} canOpen={canOpen} />
        ))}
      </div>
    </section>
  );
}

export default function ServicesPage() {
  const [services, setServices] = useState<ServiceDetail[]>(
    ALL_DASHBOARD_SERVICES.map((service) => ({
      ...service,
      status: 'unknown',
      latencyMs: null,
      lastChecked: null,
      responseData: null,
    }))
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
          const response = await axios.get(service.healthEndpoint, { timeout: 5000 });
          const responseData =
            response.data && typeof response.data === 'object'
              ? (response.data as Record<string, unknown>)
              : response.data !== undefined
                ? { preview: String(response.data).slice(0, 400) }
                : null;

          return {
            ...service,
            status: 'online' as ServiceStatus,
            latencyMs: Date.now() - startedAt,
            lastChecked: new Date(),
            responseData,
          };
        } catch {
          return {
            ...service,
            status: 'offline' as ServiceStatus,
            latencyMs: null,
            lastChecked: new Date(),
            responseData: null,
          };
        }
      })
    );

    setServices(results);
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

  const onlineCount = services.filter((service) => service.status === 'online').length;
  const offlineCount = services.filter((service) => service.status === 'offline').length;
  const webServices = useMemo(() => services.filter((service) => service.category === 'web'), [services]);
  const backendServices = useMemo(() => services.filter((service) => service.category === 'backend'), [services]);
  const progress = services.length > 0 ? Math.round((onlineCount / services.length) * 100) : 0;

  return (
    <>
      <header className="sticky top-0 z-10 border-b border-gray-700/60 bg-gray-900/80 px-6 py-4 backdrop-blur">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-base font-semibold text-white">Services</h1>
            <p className="mt-0.5 text-xs text-gray-500">Zentraler Überblick über alle 23 lokalen Frontends, APIs und Operator-Oberflächen.</p>
          </div>
          <div className="flex items-center gap-3 flex-wrap justify-end">
            {resolvedHost && (
              <span className="text-xs text-gray-500">
                Öffnen via <span className="font-mono text-gray-300">{resolvedHost}</span>
              </span>
            )}
            <div className="inline-flex items-center gap-2 rounded-full border border-gray-700/60 bg-gray-900/70 px-3 py-1.5 text-xs font-mono text-gray-400">
              <span className="text-emerald-400">{onlineCount} online</span>
              {offlineCount > 0 && <span className="text-red-400">· {offlineCount} offline</span>}
            </div>
            <button
              onClick={checkAll}
              disabled={refreshing}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-xs font-medium text-gray-300 transition-all hover:border-gray-600 hover:text-white disabled:opacity-50"
            >
              <ArrowPathIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Lädt...' : 'Jetzt aktualisieren'}
            </button>
          </div>
        </div>
      </header>

      <div className="space-y-6 p-6">
        <div className="card space-y-3">
          <div className="flex items-center gap-3">
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-700">
              <div className="h-full rounded-full bg-emerald-500 transition-all duration-700" style={{ width: `${progress}%` }} />
            </div>
            <span className="w-12 text-right text-sm font-medium text-gray-300">{progress}%</span>
          </div>
          <div className="flex items-center justify-between gap-4 flex-wrap text-sm text-gray-500">
            <span>
              {onlineCount === services.length
                ? '✅ Alle Services laufen einwandfrei'
                : `⚠️ ${offlineCount} Service${offlineCount === 1 ? '' : 's'} nicht erreichbar`}
            </span>
            <span className="inline-flex items-center gap-1.5 text-xs">
              <ClockIcon className="h-3.5 w-3.5" />
              Aktualisiert {formatRelativeTime(lastRefresh)}
            </span>
          </div>
        </div>

        <ServiceSection
          title="Web-Frontends"
          subtitle="Direkte Operator- und Nutzeroberflächen mit Öffnen-Links auf die aktuelle LAN-/Tailscale-Adresse."
          services={webServices}
          canOpen={Boolean(resolvedHost)}
        />

        <ServiceSection
          title="Backend-Services"
          subtitle="Health-Checks über den Dashboard-Proxy für alle API- und Verarbeitungsdienste."
          services={backendServices}
          canOpen={Boolean(resolvedHost)}
        />
      </div>
    </>
  );
}
