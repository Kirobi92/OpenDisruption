'use client';

import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import {
  ServerIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

// ─── Types ────────────────────────────────────────────────────────────────────

type ServiceStatus = 'online' | 'offline' | 'unknown';

interface ServiceDetail {
  name: string;
  label: string;
  port: number;
  endpoint: string;
  description: string;
  status: ServiceStatus;
  latencyMs: number | null;
  lastChecked: Date | null;
  responseData: Record<string, unknown> | null;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const SERVICES_CONFIG: Omit<ServiceDetail, 'status' | 'latencyMs' | 'lastChecked' | 'responseData'>[] = [
  {
    name: 'auth',
    label: 'Auth Service',
    port: 8002,
    endpoint: '/api/proxy/auth/health',
    description: 'JWT-Authentifizierung, Zone-Permissions, Audit-Log',
  },
  {
    name: 'api',
    label: 'API Service',
    port: 8003,
    endpoint: '/api/proxy/api/health',
    description: 'Haupt-API, Ollama-Bridge, Conversations & Messages',
  },
  {
    name: 'embeddings',
    label: 'Embeddings',
    port: 8004,
    endpoint: '/api/proxy/embeddings/health',
    description: 'nomic-embed-text dim=768, /embed, /embed/batch, /store',
  },
  {
    name: 'telegram',
    label: 'Telegram Bot',
    port: 8005,
    endpoint: '/api/proxy/telegram/health',
    description: 'Telegram-Bot-Interface für Kirobi',
  },
  {
    name: 'retrieval',
    label: 'Retrieval',
    port: 8006,
    endpoint: '/api/proxy/retrieval/health',
    description: '/search, /rag — SACRED immer 403',
  },
  {
    name: 'ingest',
    label: 'Ingest',
    port: 8007,
    endpoint: '/api/proxy/ingest/health',
    description: 'Text+File-Upload, ingest_jobs Tabelle',
  },
  {
    name: 'model-routing',
    label: 'Model Routing',
    port: 8009,
    endpoint: '/api/proxy/model-routing/health',
    description: 'LLM-Routing zwischen lokalen und externen Modellen',
  },
  {
    name: 'analytics',
    label: 'Analytics',
    port: 8010,
    endpoint: '/api/proxy/analytics/health',
    description: 'Event-Tracking, tägliche/Zonen/Modell-Statistiken',
  },
  {
    name: 'image-generation',
    label: 'Image Generation',
    port: 8011,
    endpoint: '/api/proxy/image-generation/health',
    description: 'Ollama Image Gen, generated_images Tabelle',
  },
  {
    name: 'media-processing',
    label: 'Media Processing',
    port: 8012,
    endpoint: '/api/proxy/media-processing/health',
    description: 'Pillow/mutagen, graceful fallback',
  },
  {
    name: 'music-generation',
    label: 'Music Generation',
    port: 8013,
    endpoint: '/api/proxy/music-generation/health',
    description: 'Async Jobs, generated_tracks Tabelle',
  },
  {
    name: 'video-generation',
    label: 'Video Generation',
    port: 8014,
    endpoint: '/api/proxy/video-generation/health',
    description: 'Async Jobs, generated_videos Tabelle',
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatRelativeTime(date: Date | null): string {
  if (!date) return '—';
  const diffMs = Date.now() - date.getTime();
  if (diffMs < 5_000) return 'gerade eben';
  if (diffMs < 60_000) return `vor ${Math.floor(diffMs / 1000)}s`;
  return `vor ${Math.floor(diffMs / 60_000)}min`;
}

// ─── Components ───────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: ServiceStatus }) {
  const base = 'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium';
  if (status === 'online')
    return (
      <span className={`${base} bg-emerald-500/10 text-emerald-400 border border-emerald-500/20`}>
        <CheckCircleIcon className="w-3.5 h-3.5" />Online
      </span>
    );
  if (status === 'offline')
    return (
      <span className={`${base} bg-red-500/10 text-red-400 border border-red-500/20`}>
        <XCircleIcon className="w-3.5 h-3.5" />Offline
      </span>
    );
  return (
    <span className={`${base} bg-amber-500/10 text-amber-400 border border-amber-500/20`}>
      <ExclamationTriangleIcon className="w-3.5 h-3.5" />Unbekannt
    </span>
  );
}

function ServiceCard({ svc }: { svc: ServiceDetail }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card space-y-3">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className={`p-2 rounded-lg ${
            svc.status === 'online'
              ? 'bg-emerald-500/10'
              : svc.status === 'offline'
              ? 'bg-red-500/10'
              : 'bg-gray-700'
          }`}>
            <ServerIcon className={`w-5 h-5 ${
              svc.status === 'online'
                ? 'text-emerald-400'
                : svc.status === 'offline'
                ? 'text-red-400'
                : 'text-gray-500'
            }`} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white">{svc.label}</p>
            <p className="text-xs text-gray-500 font-mono">:{svc.port}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          {svc.latencyMs !== null && (
            <span className="text-xs text-gray-400 font-mono">{svc.latencyMs}ms</span>
          )}
          <StatusBadge status={svc.status} />
        </div>
      </div>

      <p className="text-xs text-gray-400">{svc.description}</p>

      <div className="flex items-center justify-between text-xs text-gray-600">
        <div className="flex items-center gap-1.5">
          <ClockIcon className="w-3.5 h-3.5" />
          <span>Geprüft {formatRelativeTime(svc.lastChecked)}</span>
        </div>
        {svc.responseData && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-gray-500 hover:text-gray-300 transition-colors"
          >
            {expanded ? 'Details ausblenden' : 'Details anzeigen'}
          </button>
        )}
      </div>

      {expanded && svc.responseData && (
        <pre className="text-xs bg-gray-900 rounded-lg p-3 overflow-x-auto text-gray-300 border border-gray-700">
          {JSON.stringify(svc.responseData, null, 2)}
        </pre>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ServicesPage() {
  const [services, setServices] = useState<ServiceDetail[]>(
    SERVICES_CONFIG.map(s => ({
      ...s,
      status: 'unknown',
      latencyMs: null,
      lastChecked: null,
      responseData: null,
    }))
  );
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const checkAll = useCallback(async () => {
    setRefreshing(true);
    const results = await Promise.all(
      SERVICES_CONFIG.map(async (svc) => {
        const start = Date.now();
        try {
          const res = await axios.get(svc.endpoint, { timeout: 5000 });
          return {
            ...svc,
            status: 'online' as ServiceStatus,
            latencyMs: Date.now() - start,
            lastChecked: new Date(),
            responseData: res.data as Record<string, unknown>,
          };
        } catch {
          return {
            ...svc,
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

  const onlineCount = services.filter(s => s.status === 'online').length;
  const offlineCount = services.filter(s => s.status === 'offline').length;

  return (
    <div className="flex h-screen bg-gray-900 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 bg-gray-800/80 border-r border-gray-700/60 flex flex-col">
        <div className="px-5 py-5 border-b border-gray-700/60">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-kirobi-600 flex items-center justify-center text-white font-bold text-sm">
              K
            </div>
            <div>
              <p className="text-sm font-bold text-white leading-tight">Kirobi</p>
              <p className="text-xs text-gray-500 leading-tight">Admin Dashboard</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          <a href="/" className="nav-item nav-item-inactive w-full flex">
            <ServerIcon className="w-4 h-4" />
            <span>Übersicht</span>
          </a>
          <a href="/services" className="nav-item nav-item-active w-full flex">
            <ServerIcon className="w-4 h-4" />
            <span>Services</span>
          </a>
          <a href="/tasks" className="nav-item nav-item-inactive w-full flex">
            <ServerIcon className="w-4 h-4" />
            <span>Tasks</span>
          </a>
          <a href="/agents" className="nav-item nav-item-inactive w-full flex">
            <ServerIcon className="w-4 h-4" />
            <span>Agents</span>
          </a>
        </nav>
        <div className="px-4 py-4 border-t border-gray-700/60 space-y-2">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <ClockIcon className="w-3.5 h-3.5" />
            <span>Aktualisiert {formatRelativeTime(lastRefresh)}</span>
          </div>
          <button
            onClick={checkAll}
            disabled={refreshing}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs text-gray-400 hover:text-white bg-gray-700/50 hover:bg-gray-700 rounded-lg transition-all disabled:opacity-50"
          >
            <ArrowPathIcon className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Lädt...' : 'Jetzt aktualisieren'}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <header className="sticky top-0 z-10 bg-gray-900/80 backdrop-blur border-b border-gray-700/60 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-base font-semibold text-white">Docker Services</h1>
              <p className="text-xs text-gray-500 mt-0.5">Alle {services.length} Services im Überblick</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-emerald-400 font-mono">{onlineCount} online</span>
              {offlineCount > 0 && (
                <span className="text-xs text-red-400 font-mono">{offlineCount} offline</span>
              )}
            </div>
          </div>
        </header>

        <div className="p-6">
          {/* Progress bar */}
          <div className="card mb-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-700"
                  style={{ width: `${services.length > 0 ? (onlineCount / services.length) * 100 : 0}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-300 w-12 text-right">
                {services.length > 0 ? Math.round((onlineCount / services.length) * 100) : 0}%
              </span>
            </div>
            <p className="text-xs text-gray-500">
              {onlineCount === services.length
                ? '✅ Alle Services laufen einwandfrei'
                : `⚠️ ${offlineCount} Service${offlineCount > 1 ? 's' : ''} nicht erreichbar`}
            </p>
          </div>

          {/* Service grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {services.map(svc => (
              <ServiceCard key={svc.name} svc={svc} />
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
