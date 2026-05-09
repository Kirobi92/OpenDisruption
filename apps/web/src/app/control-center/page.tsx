'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  ArrowPathIcon,
  ArrowTopRightOnSquareIcon,
  BoltIcon,
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  CloudArrowUpIcon,
  CommandLineIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  QueueListIcon,
  ShieldCheckIcon,
  SparklesIcon,
  Squares2X2Icon,
  WrenchScrewdriverIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { RUNTIME_PROBES, RUNTIME_SURFACES } from '@/lib/runtime-surfaces';

type ServiceStatus = 'online' | 'offline' | 'unknown';

interface ControlEvent {
  timestamp: string;
  event_type: string;
  severity: string;
  message: string;
}

interface ControlTask {
  id: string;
  title: string;
  status: string;
  priority: string;
  agent?: string;
  zone: string;
  last_error?: string | null;
  operator_hint: string;
}

interface ControlStatus {
  supervisorAvailable: boolean;
  autonomousMode: string;
  humanGateZones: string[];
  queueDepth: number;
  pendingTasks: number;
  activeTasks: number;
  completedTasks: number;
  blockedTasks: number;
  deadLetterTasks: number;
  attentionRequired: number;
  lastEventAt?: string | null;
  lastHealthCheckAt?: string | null;
  health: Record<string, string>;
  recentEvents: ControlEvent[];
  attentionTasks: ControlTask[];
  operatorGuidance: string[];
}

interface RecentActivityItem {
  id: string;
  surface: string;
  kind: string;
  actor: string;
  summary: string;
  zone?: string | null;
  created_at: string;
}

interface ActivityResponse {
  items: RecentActivityItem[];
}

interface UploadedFile {
  id: string;
  original_filename: string;
  zone: string;
  created_at: string;
}

interface ServiceProbeResult {
  id: string;
  status: ServiceStatus;
  detail: string;
}

interface RecommendedAction {
  id: string;
  title: string;
  description: string;
  href: string;
  kind: 'primary' | 'warning' | 'ops';
}

function formatRelativeTime(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  const diffMs = Date.now() - date.getTime();
  if (diffMs < 5_000) return 'gerade eben';
  if (diffMs < 60_000) return `vor ${Math.floor(diffMs / 1_000)}s`;
  if (diffMs < 3_600_000) return `vor ${Math.floor(diffMs / 60_000)}min`;
  if (diffMs < 86_400_000) return `vor ${Math.floor(diffMs / 3_600_000)}h`;
  return date.toLocaleDateString('de-DE');
}

function statusClasses(status: ServiceStatus): string {
  if (status === 'online') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200';
  if (status === 'offline') return 'border-red-500/30 bg-red-500/10 text-red-200';
  return 'border-amber-500/30 bg-amber-500/10 text-amber-100';
}

function statusIcon(status: ServiceStatus) {
  if (status === 'online') return <CheckCircleIcon className="h-4 w-4 text-emerald-400" />;
  if (status === 'offline') return <XCircleIcon className="h-4 w-4 text-red-400" />;
  return <ExclamationTriangleIcon className="h-4 w-4 text-amber-400" />;
}

export default function ControlCenterPage() {
  const router = useRouter();
  const [control, setControl] = useState<ControlStatus | null>(null);
  const [activity, setActivity] = useState<RecentActivityItem[]>([]);
  const [uploads, setUploads] = useState<UploadedFile[]>([]);
  const [probes, setProbes] = useState<Record<string, ServiceProbeResult>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const getAxios = () =>
    axios.create({
      baseURL: '/api',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token') ?? ''}`,
      },
    });

  const refresh = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/');
      return;
    }

    setRefreshing(true);
    setError('');

    try {
      const api = getAxios();
      const [controlRes, activityRes, uploadsRes, probeResults] = await Promise.all([
        api.get<ControlStatus>('/control/status'),
        api.get<ActivityResponse>('/dashboard/activity?limit=6'),
        api.get<UploadedFile[]>('/uploads'),
        Promise.all(
          RUNTIME_PROBES.map(async (probe) => {
            try {
              const response = await fetch(probe.path, { cache: 'no-store' });
              return {
                id: probe.id,
                status: response.ok ? 'online' : 'offline',
                detail: `HTTP ${response.status}`,
              } satisfies ServiceProbeResult;
            } catch (probeError: unknown) {
              return {
                id: probe.id,
                status: 'offline',
                detail: probeError instanceof Error ? probeError.message : 'unreachable',
              } satisfies ServiceProbeResult;
            }
          })
        ),
      ]);

      setControl(controlRes.data);
      setActivity(activityRes.data.items ?? []);
      setUploads(uploadsRes.data ?? []);
      setProbes(
        Object.fromEntries(probeResults.map((result) => [result.id, result]))
      );
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        router.push('/');
        return;
      }
      setError(
        axios.isAxiosError(err)
          ? err.response?.data?.detail ?? 'Control Center konnte nicht geladen werden.'
          : 'Control Center konnte nicht geladen werden.'
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => {
      void refresh();
    }, 30_000);
    return () => window.clearInterval(interval);
  }, []);

  const recommendations = useMemo<RecommendedAction[]>(() => {
    const actions: RecommendedAction[] = [];
    const offlineCount = Object.values(probes).filter((probe) => probe.status === 'offline').length;

    if (offlineCount > 0) {
      actions.push({
        id: 'check-services',
        title: 'Service-Störung prüfen',
        description: `${offlineCount} Oberfläche${offlineCount > 1 ? 'n' : ''} reagiert gerade nicht sauber. Öffne die Service Matrix für Health und Gegenmaßnahmen.`,
        href: '/dashboard/services',
        kind: 'warning',
      });
    }

    if ((control?.blockedTasks ?? 0) > 0 || (control?.deadLetterTasks ?? 0) > 0) {
      actions.push({
        id: 'triage-tasks',
        title: 'Operator-Triage öffnen',
        description: 'Es gibt blockierte oder festgelaufene Supervisor-Aufgaben. Springe direkt in die Task-Triage.',
        href: '/dashboard/tasks?filter=attention',
        kind: 'warning',
      });
    }

    if (uploads.length === 0) {
      actions.push({
        id: 'seed-knowledge',
        title: 'Wissen einspeisen',
        description: 'Das System wirkt klüger, wenn erstes lokales Material vorhanden ist. Starte mit einer Datei oder Schnellnotiz.',
        href: '/upload?zone=WORKSPACE&mode=text',
        kind: 'primary',
      });
    } else {
      actions.push({
        id: 'query-memory',
        title: 'Letztes Wissen weiterverwenden',
        description: 'Es liegen bereits lokale Uploads vor. Durchsuche sie direkt oder starte daraus einen neuen Chat.',
        href: '/search?zone=WORKSPACE',
        kind: 'primary',
      });
    }

    if ((control?.activeTasks ?? 0) > 0 || (control?.pendingTasks ?? 0) > 0) {
      actions.push({
        id: 'watch-runtime',
        title: 'Autonome Laufzeit beobachten',
        description: 'Supervisor-Aktivität läuft bereits. Öffne die Ops-Sicht, statt blind neue Arbeit zu starten.',
        href: '/dashboard/',
        kind: 'ops',
      });
    } else {
      actions.push({
        id: 'start-chat',
        title: 'Intelligente Session starten',
        description: 'Starte aus dem Command Center direkt in Chat, Suche oder Workbench – mit voller Laufzeitübersicht im Rücken.',
        href: '/chat?new=1',
        kind: 'ops',
      });
    }

    return actions.slice(0, 4);
  }, [control, probes, uploads.length]);

  const healthSummary = useMemo(() => {
    const online = Object.values(probes).filter((probe) => probe.status === 'online').length;
    const total = RUNTIME_PROBES.length;
    return { online, total };
  }, [probes]);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 pb-24 pt-6 md:px-6 md:pb-10">
        <section className="overflow-hidden rounded-3xl border border-kirobi-500/20 bg-gradient-to-br from-kirobi-600/20 via-gray-900 to-gray-950 p-6 shadow-2xl shadow-kirobi-950/40">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl space-y-3">
              <span className="inline-flex w-fit items-center gap-2 rounded-full border border-kirobi-500/30 bg-kirobi-500/10 px-3 py-1 text-xs font-medium text-kirobi-100">
                <SparklesIcon className="h-4 w-4" />
                Agentic Control Center
              </span>
              <div>
                <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
                  Eine Oberfläche, die mitdenkt.
                </h1>
                <p className="mt-3 text-sm leading-6 text-gray-300 md:text-base">
                  Status, Agenten, Wissen, Uploads und Workbenches laufen hier zusammen.
                  Statt toter Listen bekommst du nächste sinnvolle Schritte, aktuelle Signale
                  und direkte Sprünge in die richtige Oberfläche.
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => void refresh()}
                disabled={refreshing}
                className="inline-flex items-center gap-2 rounded-xl border border-gray-700 bg-gray-900/80 px-4 py-2.5 text-sm font-medium text-gray-100 transition hover:border-kirobi-500/40 hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <ArrowPathIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? 'Aktualisiert…' : 'Live aktualisieren'}
              </button>
              <Link
                href="/dashboard/"
                className="inline-flex items-center gap-2 rounded-xl bg-kirobi-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-kirobi-500"
              >
                <CommandLineIcon className="h-4 w-4" />
                Ops öffnen
              </Link>
            </div>
          </div>
        </section>

        {error && (
          <section className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </section>
        )}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-gray-800 bg-gray-900/80 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-gray-500">Surfaces online</p>
            <div className="mt-3 flex items-end justify-between">
              <div>
                <p className="text-3xl font-bold">{healthSummary.online}/{healthSummary.total}</p>
                <p className="mt-1 text-sm text-gray-400">API, Auth, Telegram und Voice</p>
              </div>
              <Squares2X2Icon className="h-8 w-8 text-kirobi-400" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-800 bg-gray-900/80 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-gray-500">Knowledge ready</p>
            <div className="mt-3 flex items-end justify-between">
              <div>
                <p className="text-3xl font-bold">{uploads.length}</p>
                <p className="mt-1 text-sm text-gray-400">lokale Uploads im MVP-Pfad</p>
              </div>
              <CloudArrowUpIcon className="h-8 w-8 text-emerald-400" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-800 bg-gray-900/80 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-gray-500">Supervisor flow</p>
            <div className="mt-3 flex items-end justify-between">
              <div>
                <p className="text-3xl font-bold">{control?.activeTasks ?? 0}/{control?.queueDepth ?? 0}</p>
                <p className="mt-1 text-sm text-gray-400">aktiv vs. Warteschlange</p>
              </div>
              <CpuChipIcon className="h-8 w-8 text-violet-400" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-800 bg-gray-900/80 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-gray-500">Human gates</p>
            <div className="mt-3 flex items-end justify-between">
              <div>
                <p className="text-3xl font-bold">{control?.humanGateZones.length ?? 0}</p>
                <p className="mt-1 text-sm text-gray-400">geschützte Zonen bleiben fail-closed</p>
              </div>
              <ShieldCheckIcon className="h-8 w-8 text-amber-400" />
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-3xl border border-gray-800 bg-gray-900/80 p-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">Nächste beste Aktionen</h2>
                <p className="mt-1 text-sm text-gray-400">
                  Kontextabhängige Vorschläge aus Runtime, Uploads und Operator-Signalen.
                </p>
              </div>
              <BoltIcon className="h-6 w-6 text-kirobi-400" />
            </div>
            <div className="mt-5 grid gap-3">
              {recommendations.map((action) => (
                <Link
                  key={action.id}
                  href={action.href}
                  className={`rounded-2xl border p-4 transition hover:border-kirobi-500/40 hover:bg-gray-800 ${
                    action.kind === 'warning'
                      ? 'border-amber-500/30 bg-amber-500/10'
                      : action.kind === 'primary'
                      ? 'border-kirobi-500/30 bg-kirobi-500/10'
                      : 'border-gray-700 bg-gray-800/60'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-white">{action.title}</p>
                      <p className="mt-1 text-sm text-gray-300">{action.description}</p>
                    </div>
                    <ArrowTopRightOnSquareIcon className="mt-0.5 h-4 w-4 flex-shrink-0 text-gray-400" />
                  </div>
                </Link>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-gray-800 bg-gray-900/80 p-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">Agentic Briefing</h2>
                <p className="mt-1 text-sm text-gray-400">
                  Verdichteter Zustand statt roher Telemetrie.
                </p>
              </div>
              <SparklesIcon className="h-6 w-6 text-violet-400" />
            </div>
            <div className="mt-5 space-y-3 text-sm text-gray-300">
              <div className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-gray-500">Autonomie-Modus</p>
                <p className="mt-2 font-medium text-white">{control?.autonomousMode ?? 'local-only-deterministic'}</p>
                <p className="mt-2 text-gray-400">
                  Letztes Supervisor-Signal: {formatRelativeTime(control?.lastEventAt)}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-gray-500">Systemeinschätzung</p>
                <ul className="mt-2 space-y-2">
                  {(control?.operatorGuidance ?? []).slice(0, 3).map((item) => (
                    <li key={item} className="flex gap-2">
                      <span className="mt-0.5 text-kirobi-400">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-3xl border border-gray-800 bg-gray-900/80 p-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">Operator queue</h2>
                <p className="mt-1 text-sm text-gray-400">
                  Dinge, die echte Aufmerksamkeit brauchen.
                </p>
              </div>
              <QueueListIcon className="h-6 w-6 text-amber-400" />
            </div>
            <div className="mt-5 space-y-3">
              {(control?.attentionTasks ?? []).map((task) => (
                <div key={task.id} className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-white">{task.title}</p>
                      <p className="mt-1 text-xs text-gray-500">
                        {task.agent ? `@${task.agent}` : 'system'} · {task.zone}
                      </p>
                    </div>
                    <span className="rounded-full border border-amber-500/20 bg-amber-500/10 px-2 py-0.5 text-[11px] uppercase tracking-wide text-amber-200">
                      {task.status}
                    </span>
                  </div>
                  <p className="mt-3 text-sm text-gray-300">{task.operator_hint}</p>
                  {task.last_error && (
                    <p className="mt-2 rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs text-red-200">
                      {task.last_error}
                    </p>
                  )}
                </div>
              ))}
              {(!control || control.attentionTasks.length === 0) && (
                <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-4 text-sm text-emerald-100">
                  Keine akuten blockierten oder festgefahrenen Operator-Tasks sichtbar.
                </div>
              )}
            </div>
          </div>

          <div className="rounded-3xl border border-gray-800 bg-gray-900/80 p-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">Runtime gates</h2>
                <p className="mt-1 text-sm text-gray-400">
                  Die Leitplanken, die die Intelligenz zuverlässig machen.
                </p>
              </div>
              <ShieldCheckIcon className="h-6 w-6 text-violet-400" />
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              {(control?.humanGateZones ?? []).map((zone) => (
                <div key={zone} className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-gray-500">Gate zone</p>
                  <p className="mt-2 text-lg font-semibold text-white">{zone}</p>
                  <p className="mt-2 text-sm text-gray-400">Fail-closed, human-gated und lokal kontrolliert.</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-3xl border border-gray-800 bg-gray-900/80 p-5">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">Service- und Workbench-Hub</h2>
              <p className="mt-1 text-sm text-gray-400">
                Native Flows, Operator-Surfaces und Fremd-Workbenches in einem Raster.
              </p>
            </div>
            <WrenchScrewdriverIcon className="h-6 w-6 text-kirobi-400" />
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {RUNTIME_SURFACES.map((card) => {
              const probe = card.kind === 'native' ? probes.api ?? { status: 'unknown', detail: 'wird geladen' } : null;
              return (
                <Link
                  key={card.id}
                  href={card.path}
                  className="group rounded-2xl border border-gray-800 bg-gray-950/60 p-4 transition hover:border-kirobi-500/40 hover:bg-gray-900"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="inline-flex rounded-full border border-gray-700 bg-gray-900 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-gray-300">
                        {card.badge}
                      </span>
                      <h3 className="mt-3 text-lg font-semibold text-white group-hover:text-kirobi-200">
                        {card.label}
                      </h3>
                    </div>
                    <ArrowTopRightOnSquareIcon className="h-4 w-4 flex-shrink-0 text-gray-500 transition group-hover:text-kirobi-300" />
                  </div>
                  <p className="mt-3 text-sm leading-6 text-gray-400">{card.summary}</p>
                  <p className="mt-2 text-xs text-gray-500">{card.guard}</p>
                  {probe && (
                    <div className={`mt-4 inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs ${statusClasses(probe.status)}`}>
                      {statusIcon(probe.status)}
                      <span>{probe.detail}</span>
                    </div>
                  )}
                </Link>
              );
            })}
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <div className="rounded-3xl border border-gray-800 bg-gray-900/80 p-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">Live-Signale</h2>
                <p className="mt-1 text-sm text-gray-400">
                  Die letzten Bewegungen aus Auth, Uploads und Chat.
                </p>
              </div>
              <QueueListIcon className="h-6 w-6 text-emerald-400" />
            </div>
            <div className="mt-5 space-y-3">
              {(activity.length > 0 ? activity : control?.recentEvents?.map((event, index) => ({
                id: `${event.event_type}-${index}`,
                surface: 'supervisor',
                kind: event.event_type,
                actor: 'system',
                summary: event.message,
                zone: null,
                created_at: event.timestamp,
              })))?.map((item) => (
                <div key={item.id} className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-gray-800 px-2 py-0.5 text-[11px] uppercase tracking-wide text-gray-300">
                        {item.surface}
                      </span>
                      {item.zone && (
                        <span className="rounded-full border border-kirobi-500/20 bg-kirobi-500/10 px-2 py-0.5 text-[11px] text-kirobi-100">
                          {item.zone}
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-500">{formatRelativeTime(item.created_at)}</span>
                  </div>
                  <p className="mt-3 text-sm font-medium text-white">{item.summary}</p>
                  <p className="mt-1 text-xs text-gray-500">
                    {item.actor} · {item.kind}
                  </p>
                </div>
              ))}
              {!loading && activity.length === 0 && !control?.recentEvents?.length && (
                <div className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4 text-sm text-gray-400">
                  Noch keine Live-Signale sichtbar.
                </div>
              )}
            </div>
          </div>

          <div className="rounded-3xl border border-gray-800 bg-gray-900/80 p-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">Quick lanes</h2>
                <p className="mt-1 text-sm text-gray-400">
                  Häufige Flows ohne Umwege.
                </p>
              </div>
              <ChatBubbleLeftRightIcon className="h-6 w-6 text-kirobi-400" />
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <Link href="/chat?new=1" className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4 transition hover:border-kirobi-500/40">
                <ChatBubbleLeftRightIcon className="h-5 w-5 text-kirobi-300" />
                <p className="mt-3 text-sm font-semibold text-white">Neue Session</p>
                <p className="mt-1 text-sm text-gray-400">Starte sofort einen neuen lokalen Dialog.</p>
              </Link>
              <Link href="/search?zone=WORKSPACE" className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4 transition hover:border-kirobi-500/40">
                <MagnifyingGlassIcon className="h-5 w-5 text-emerald-300" />
                <p className="mt-3 text-sm font-semibold text-white">Knowledge finden</p>
                <p className="mt-1 text-sm text-gray-400">Suche direkt in Workspace-Inhalten und Uploads.</p>
              </Link>
              <Link href="/upload?zone=WORKSPACE&mode=text" className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4 transition hover:border-kirobi-500/40">
                <CloudArrowUpIcon className="h-5 w-5 text-violet-300" />
                <p className="mt-3 text-sm font-semibold text-white">Schnellnotiz speichern</p>
                <p className="mt-1 text-sm text-gray-400">Von unterwegs Ideen in den lokalen Wissenspfad schieben.</p>
              </Link>
              <Link href="/dashboard/services" className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4 transition hover:border-kirobi-500/40">
                <CommandLineIcon className="h-5 w-5 text-amber-300" />
                <p className="mt-3 text-sm font-semibold text-white">Runtime prüfen</p>
                <p className="mt-1 text-sm text-gray-400">Wenn etwas hakt, direkt in Service-Matrix und Health.</p>
              </Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
