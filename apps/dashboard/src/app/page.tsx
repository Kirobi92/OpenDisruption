'use client';

import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import axios from 'axios';
import {
  ServerIcon,
  ChartBarIcon,
  UsersIcon,
  CpuChipIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CircleStackIcon,
  ClipboardDocumentListIcon,
  CommandLineIcon,
  ShieldCheckIcon,
  BoltIcon,
} from '@heroicons/react/24/outline';

type ServiceStatus = 'online' | 'offline' | 'unknown';

type NavSection = 'control' | 'services' | 'analytics' | 'users' | 'system';

interface ServiceHealth {
  name: string;
  label: string;
  endpoint: string;
  status: ServiceStatus;
  latencyMs: number | null;
  lastChecked: Date | null;
}

interface AnalyticsStats {
  eventsToday: number;
  activeUsers: number;
  zoneUsage: Record<string, number>;
  totalConversations: number;
  totalMessages: number;
}

interface OllamaModel {
  name: string;
  size: number;
  modified_at: string;
}

interface SystemInfo {
  ollamaModels: OllamaModel[];
  ollamaStatus: ServiceStatus;
  dbStatus: ServiceStatus;
  qdrantStatus: ServiceStatus;
}

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

interface RecentActivity {
  id: string;
  surface: string;
  kind: string;
  actor: string;
  summary: string;
  zone?: string | null;
  created_at: string;
}

const SERVICES: Pick<ServiceHealth, 'name' | 'label' | 'endpoint'>[] = [
  { name: 'api', label: 'API Service', endpoint: '/api/proxy/api/health' },
  { name: 'auth', label: 'Auth Service', endpoint: '/api/proxy/auth/health' },
  { name: 'embeddings', label: 'Embeddings', endpoint: '/api/proxy/embeddings/health' },
  { name: 'ingest', label: 'Ingest', endpoint: '/api/proxy/ingest/health' },
  { name: 'retrieval', label: 'Retrieval', endpoint: '/api/proxy/retrieval/health' },
  { name: 'model-routing', label: 'Model Routing', endpoint: '/api/proxy/model-routing/health' },
  { name: 'analytics', label: 'Analytics', endpoint: '/api/proxy/analytics/health' },
];

const AUTO_REFRESH_INTERVAL_MS = 30_000;

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function formatRelativeTime(date: Date | null): string {
  if (!date) return '—';
  const diffMs = Date.now() - date.getTime();
  if (diffMs < 5_000) return 'gerade eben';
  if (diffMs < 60_000) return `vor ${Math.floor(diffMs / 1000)}s`;
  if (diffMs < 3_600_000) return `vor ${Math.floor(diffMs / 60_000)}min`;
  return `vor ${Math.floor(diffMs / 3_600_000)}h`;
}

function toServiceStatus(value: string | undefined): ServiceStatus {
  if (value === 'healthy' || value === 'online') return 'online';
  if (value === 'unhealthy' || value === 'offline') return 'offline';
  return 'unknown';
}

function priorityLabel(priority: string): string {
  switch (priority) {
    case 'critical':
      return 'Kritisch';
    case 'high':
      return 'Hoch';
    case 'medium':
      return 'Mittel';
    case 'low':
      return 'Niedrig';
    default:
      return 'Hintergrund';
  }
}

function StatusDot({ status }: { status: ServiceStatus }) {
  if (status === 'online') return <span className="status-dot-green" />;
  if (status === 'offline') return <span className="status-dot-red" />;
  return <span className="status-dot-yellow" />;
}

function StatusBadge({ status }: { status: ServiceStatus }) {
  const base = 'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium';
  if (status === 'online') return <span className={`${base} bg-emerald-500/10 text-emerald-400 border border-emerald-500/20`}><CheckCircleIcon className="w-3.5 h-3.5" />Online</span>;
  if (status === 'offline') return <span className={`${base} bg-red-500/10 text-red-400 border border-red-500/20`}><XCircleIcon className="w-3.5 h-3.5" />Offline</span>;
  return <span className={`${base} bg-amber-500/10 text-amber-400 border border-amber-500/20`}><ExclamationTriangleIcon className="w-3.5 h-3.5" />Unbekannt</span>;
}

function TaskStatusBadge({ status }: { status: string }) {
  const base = 'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium';
  switch (status) {
    case 'completed':
      return <span className={`${base} bg-emerald-500/10 text-emerald-400 border border-emerald-500/20`}><CheckCircleIcon className="w-3 h-3" />Erledigt</span>;
    case 'in_progress':
      return <span className={`${base} bg-kirobi-500/10 text-kirobi-400 border border-kirobi-500/20`}><ArrowPathIcon className="w-3 h-3 animate-spin" />In Arbeit</span>;
    case 'blocked':
      return <span className={`${base} bg-amber-500/10 text-amber-400 border border-amber-500/20`}><ShieldCheckIcon className="w-3 h-3" />Blockiert</span>;
    case 'dead_letter':
      return <span className={`${base} bg-red-500/10 text-red-400 border border-red-500/20`}><XCircleIcon className="w-3 h-3" />Dead-Letter</span>;
    default:
      return <span className={`${base} bg-gray-700 text-gray-300 border border-gray-600`}><ClockIcon className="w-3 h-3" />Ausstehend</span>;
  }
}

function StatCard({
  label,
  value,
  icon: Icon,
  color = 'kirobi',
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color?: 'kirobi' | 'emerald' | 'violet' | 'amber' | 'red';
}) {
  const colorMap: Record<string, string> = {
    kirobi: 'text-kirobi-400 bg-kirobi-500/10',
    emerald: 'text-emerald-400 bg-emerald-500/10',
    violet: 'text-violet-400 bg-violet-500/10',
    amber: 'text-amber-400 bg-amber-500/10',
    red: 'text-red-400 bg-red-500/10',
  };
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-xl ${colorMap[color]}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
        <p className="text-2xl font-bold text-white mt-0.5">{value}</p>
      </div>
    </div>
  );
}

function ServicesPanel({ services }: { services: ServiceHealth[] }) {
  const onlineCount = services.filter((s) => s.status === 'online').length;
  const total = services.length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Service-Status</h2>
        <span className="text-sm text-gray-400">
          <span className={onlineCount === total ? 'text-emerald-400' : 'text-amber-400'}>{onlineCount}/{total}</span> online
        </span>
      </div>
      <div className="card">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
            <div className="h-full bg-emerald-500 rounded-full transition-all duration-700" style={{ width: `${total > 0 ? (onlineCount / total) * 100 : 0}%` }} />
          </div>
          <span className="text-sm font-medium text-gray-300 w-12 text-right">{total > 0 ? Math.round((onlineCount / total) * 100) : 0}%</span>
        </div>
        <p className="text-xs text-gray-500">{onlineCount === total ? '✅ Alle Services laufen einwandfrei' : `⚠️ ${total - onlineCount} Service${total - onlineCount > 1 ? 's' : ''} nicht erreichbar`}</p>
      </div>
      <div className="grid gap-3">
        {services.map((svc) => (
          <div key={svc.name} className="card flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 min-w-0">
              <StatusDot status={svc.status} />
              <div className="min-w-0">
                <p className="text-sm font-medium text-white truncate">{svc.label}</p>
                <p className="text-xs text-gray-500 font-mono truncate">{svc.endpoint}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              {svc.latencyMs !== null && <span className="text-xs text-gray-400 font-mono">{svc.latencyMs}ms</span>}
              <StatusBadge status={svc.status} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AnalyticsPanel({ stats, loading }: { stats: AnalyticsStats | null; loading: boolean }) {
  if (loading || !stats) {
    return (
      <div className="space-y-6">
        <h2 className="text-lg font-semibold text-white">Analytics</h2>
        <div className="grid grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse"><div className="h-16 bg-gray-700 rounded-lg" /></div>
          ))}
        </div>
      </div>
    );
  }

  const zoneEntries = Object.entries(stats.zoneUsage).sort((a, b) => b[1] - a[1]);
  const totalZoneEvents = zoneEntries.reduce((sum, [, v]) => sum + v, 0);
  const zoneColors: Record<string, string> = {
    WORKSPACE: 'bg-kirobi-500',
    FAMILY_PRIVATE: 'bg-violet-500',
    PUBLIC: 'bg-emerald-500',
    SACRED: 'bg-amber-500',
    QUARANTINE: 'bg-red-500',
  };

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-white">Analytics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <StatCard label="Events heute" value={stats.eventsToday} icon={ChartBarIcon} color="kirobi" />
        <StatCard label="Aktive User" value={stats.activeUsers} icon={UsersIcon} color="emerald" />
        <StatCard label="Gespräche gesamt" value={stats.totalConversations} icon={CommandLineIcon} color="violet" />
        <StatCard label="Nachrichten gesamt" value={stats.totalMessages} icon={CircleStackIcon} color="amber" />
      </div>
      {zoneEntries.length > 0 && (
        <div className="card space-y-4">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Zonen-Nutzung</h3>
          <div className="space-y-3">
            {zoneEntries.map(([zone, count]) => {
              const pct = totalZoneEvents > 0 ? Math.round((count / totalZoneEvents) * 100) : 0;
              return (
                <div key={zone}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400 font-mono">{zone}</span>
                    <span className="text-gray-400">{count} ({pct}%)</span>
                  </div>
                  <div className="bg-gray-700 rounded-full h-1.5 overflow-hidden">
                    <div className={`h-full ${(zoneColors[zone] ?? 'bg-gray-500')} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function UsersPanel() {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-white">Benutzer</h2>
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <ShieldCheckIcon className="w-5 h-5 text-kirobi-400" />
          <h3 className="text-sm font-semibold text-gray-300">Familie Darusi</h3>
        </div>
        <div className="space-y-3">
          {[
            { name: 'Sven', role: 'admin', avatar: '👨‍💻' },
            { name: 'Samira', role: 'family', avatar: '👩' },
            { name: 'Sineo', role: 'family', avatar: '🧒' },
          ].map((user) => (
            <div key={user.name} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-0">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{user.avatar}</span>
                <div>
                  <p className="text-sm font-medium text-white">{user.name}</p>
                  <p className="text-xs text-gray-500 capitalize">{user.role}</p>
                </div>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${user.role === 'admin' ? 'bg-kirobi-500/20 text-kirobi-400 border border-kirobi-500/30' : 'bg-gray-700 text-gray-400 border border-gray-600'}`}>{user.role}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-600 mt-4">🔒 Benutzerverwaltung erfolgt über den Auth-Service</p>
      </div>
    </div>
  );
}

function ActivityPanel({ items, loading }: { items: RecentActivity[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="card animate-pulse">
        <div className="h-24 bg-gray-700 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Letzte Produktaktivität</h3>
        <span className="text-xs text-gray-500">Auth · Upload · Chat</span>
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-gray-500">Noch keine jüngsten Aktivitäten im MVP sichtbar.</p>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.id} className="flex items-start justify-between gap-4 border-b border-gray-700/50 pb-3 last:border-0 last:pb-0">
              <div className="min-w-0">
                <p className="text-sm font-medium text-white">{item.summary}</p>
                <p className="mt-1 text-xs text-gray-500">
                  {item.actor} · {item.surface}
                  {item.zone ? ` · ${item.zone}` : ''}
                </p>
              </div>
              <span className="shrink-0 text-xs text-gray-500">
                {new Date(item.created_at).toLocaleString('de-DE', {
                  day: '2-digit',
                  month: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SystemPanel({ info, loading }: { info: SystemInfo | null; loading: boolean }) {
  if (loading || !info) {
    return (
      <div className="space-y-6">
        <h2 className="text-lg font-semibold text-white">System</h2>
        <div className="card animate-pulse"><div className="h-32 bg-gray-700 rounded-lg" /></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-white">System</h2>
      <div className="card space-y-3">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Infrastruktur</h3>
        {[
          { label: 'Ollama (LLM)', status: info.ollamaStatus, icon: CpuChipIcon },
          { label: 'PostgreSQL', status: info.dbStatus, icon: CircleStackIcon },
          { label: 'Qdrant', status: info.qdrantStatus, icon: CircleStackIcon },
        ].map(({ label, status, icon: Icon }) => (
          <div key={label} className="flex items-center justify-between py-2 border-b border-gray-700/50 last:border-0">
            <div className="flex items-center gap-3"><Icon className="w-4 h-4 text-gray-500" /><span className="text-sm text-gray-300">{label}</span></div>
            <StatusBadge status={status} />
          </div>
        ))}
      </div>
      <div className="card space-y-3">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Ollama-Modelle <span className="ml-2 text-xs font-normal text-gray-500 normal-case">({info.ollamaModels.length} geladen)</span></h3>
        {info.ollamaModels.length === 0 ? (
          <p className="text-sm text-gray-500 italic">Keine Modelle gefunden oder Ollama offline</p>
        ) : (
          <div className="space-y-2">
            {info.ollamaModels.map((model) => (
              <div key={model.name} className="flex items-center justify-between py-2 border-b border-gray-700/50 last:border-0">
                <div className="min-w-0">
                  <p className="text-sm font-mono text-gray-200 truncate">{model.name}</p>
                  <p className="text-xs text-gray-500">{new Date(model.modified_at).toLocaleDateString('de-DE')}</p>
                </div>
                <span className="text-xs text-gray-400 font-mono flex-shrink-0 ml-3">{formatBytes(model.size)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ControlPanel({ control, loading }: { control: ControlStatus | null; loading: boolean }) {
  if (loading || !control) {
    return (
      <div className="space-y-6">
        <h2 className="text-lg font-semibold text-white">Operator Control</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse"><div className="h-20 bg-gray-700 rounded-lg" /></div>
          ))}
        </div>
      </div>
    );
  }

  const healthEntries = Object.entries(control.health);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-lg font-semibold text-white">Operator Control</h2>
          <p className="text-sm text-gray-400 mt-1">Lokale Sicht auf Supervisor, Human-Gates und autonome Ausführung.</p>
        </div>
        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${control.attentionRequired > 0 ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'}`}>
          <ShieldCheckIcon className="w-4 h-4" />
          {control.attentionRequired > 0 ? `${control.attentionRequired} Task(s) brauchen Operator-Input` : 'Keine offenen Human-Gates'}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard label="Queue Depth" value={control.queueDepth} icon={ClipboardDocumentListIcon} color="kirobi" />
        <StatCard label="Aktiv lokal" value={control.activeTasks} icon={BoltIcon} color="emerald" />
        <StatCard label="Human-Gates" value={control.blockedTasks} icon={ShieldCheckIcon} color="amber" />
        <StatCard label="Dead-Letter" value={control.deadLetterTasks} icon={XCircleIcon} color="red" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <div className="card space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Vertrauens-Signale</h3>
              <span className="text-xs text-gray-500 font-mono">{control.autonomousMode}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="rounded-xl border border-gray-700 bg-gray-900/60 p-4">
                <p className="text-xs text-gray-500 uppercase tracking-wider">Autonomie</p>
                <p className="text-sm text-white mt-2">Deterministisch, lokal, read-only sichtbar</p>
              </div>
              <div className="rounded-xl border border-gray-700 bg-gray-900/60 p-4">
                <p className="text-xs text-gray-500 uppercase tracking-wider">Human Gate</p>
                <p className="text-sm text-white mt-2">{control.humanGateZones.join(' · ')}</p>
              </div>
              <div className="rounded-xl border border-gray-700 bg-gray-900/60 p-4">
                <p className="text-xs text-gray-500 uppercase tracking-wider">Letzter Check</p>
                <p className="text-sm text-white mt-2">{formatRelativeTime(control.lastHealthCheckAt ? new Date(control.lastHealthCheckAt) : null)}</p>
              </div>
            </div>
            <div className="space-y-2">
              {control.operatorGuidance.map((item) => (
                <div key={item} className="flex items-start gap-2 text-sm text-gray-300">
                  <ShieldCheckIcon className="w-4 h-4 text-kirobi-400 mt-0.5 flex-shrink-0" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Aufmerksamkeit nötig</h3>
              <span className="text-xs text-gray-500 font-mono">{control.attentionTasks.length} Einträge</span>
            </div>
            {control.attentionTasks.length === 0 ? (
              <p className="text-sm text-gray-500">Keine offenen Kontroll- oder Triage-Signale.</p>
            ) : (
              <div className="space-y-3">
                {control.attentionTasks.map((task) => (
                  <div key={task.id} className="rounded-xl border border-gray-700 bg-gray-900/60 p-4 space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{task.title}</p>
                        <p className="text-xs text-gray-500 mt-1 font-mono">{task.id}</p>
                      </div>
                      <TaskStatusBadge status={task.status} />
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs text-gray-400">
                      <span className="px-2 py-0.5 rounded bg-gray-700/60">{priorityLabel(task.priority)}</span>
                      <span className="px-2 py-0.5 rounded bg-gray-700/60">{task.zone}</span>
                      {task.agent && <span className="px-2 py-0.5 rounded bg-gray-700/60">@{task.agent}</span>}
                    </div>
                    <p className="text-sm text-gray-300">{task.operator_hint}</p>
                    {task.last_error && <p className="text-xs text-amber-300 bg-amber-500/5 border border-amber-500/10 rounded-lg px-3 py-2">{task.last_error}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="card space-y-4">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Supervisor Health</h3>
            {!control.supervisorAvailable ? (
              <p className="text-sm text-gray-500">Supervisor-Tabellen fehlen noch oder der Stack wurde noch nicht initialisiert.</p>
            ) : healthEntries.length === 0 ? (
              <p className="text-sm text-gray-500">Noch kein Health-Event vorhanden.</p>
            ) : (
              healthEntries.map(([name, value]) => (
                <div key={name} className="flex items-center justify-between gap-3 py-2 border-b border-gray-700/50 last:border-0">
                  <span className="text-sm text-gray-300 capitalize">{name}</span>
                  <StatusBadge status={toServiceStatus(value)} />
                </div>
              ))
            )}
          </div>

          <div className="card space-y-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Letzte Events</h3>
              <span className="text-xs text-gray-500">{formatRelativeTime(control.lastEventAt ? new Date(control.lastEventAt) : null)}</span>
            </div>
            {control.recentEvents.length === 0 ? (
              <p className="text-sm text-gray-500">Noch keine Supervisor-Events verfügbar.</p>
            ) : (
              <div className="space-y-3">
                {control.recentEvents.map((event) => {
                  const tone = event.severity === 'warning' ? 'text-amber-400' : event.severity === 'error' || event.severity === 'critical' ? 'text-red-400' : 'text-kirobi-400';
                  return (
                    <div key={`${event.timestamp}-${event.event_type}-${event.message}`} className="border-l-2 border-gray-700 pl-3">
                      <p className={`text-xs font-medium uppercase tracking-wider ${tone}`}>{event.event_type}</p>
                      <p className="text-sm text-gray-300 mt-1">{event.message}</p>
                      <p className="text-xs text-gray-500 mt-1">{new Date(event.timestamp).toLocaleString('de-DE')}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const [activeSection, setActiveSection] = useState<NavSection>('control');
  const [services, setServices] = useState<ServiceHealth[]>(SERVICES.map((s) => ({ ...s, status: 'unknown', latencyMs: null, lastChecked: null })));
  const [analyticsStats, setAnalyticsStats] = useState<AnalyticsStats | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [controlStatus, setControlStatus] = useState<ControlStatus | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [systemLoading, setSystemLoading] = useState(false);
  const [controlLoading, setControlLoading] = useState(false);
  const [activityLoading, setActivityLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);

  const checkServiceHealth = useCallback(async (svc: Pick<ServiceHealth, 'name' | 'label' | 'endpoint'>): Promise<ServiceHealth> => {
    const start = Date.now();
    try {
      await axios.get(svc.endpoint, { timeout: 5000 });
      return { ...svc, status: 'online', latencyMs: Date.now() - start, lastChecked: new Date() };
    } catch {
      return { ...svc, status: 'offline', latencyMs: null, lastChecked: new Date() };
    }
  }, []);

  const refreshServices = useCallback(async () => {
    const results = await Promise.all(SERVICES.map(checkServiceHealth));
    setServices(results);
  }, [checkServiceHealth]);

  const refreshAnalytics = useCallback(async () => {
    setAnalyticsLoading(true);
    try {
      const statsRes = await axios.get('/api/proxy/analytics/stats', { timeout: 5000 });
      const data = statsRes.data as Partial<AnalyticsStats>;
      setAnalyticsStats({
        eventsToday: data.eventsToday ?? 0,
        activeUsers: data.activeUsers ?? 0,
        zoneUsage: data.zoneUsage ?? {},
        totalConversations: data.totalConversations ?? 0,
        totalMessages: data.totalMessages ?? 0,
      });
    } finally {
      setAnalyticsLoading(false);
    }
  }, []);

  const refreshSystem = useCallback(async () => {
    setSystemLoading(true);
    try {
      const [ollamaRes, dbRes, qdrantRes] = await Promise.allSettled([
        axios.get('/api/proxy/ollama/api/tags', { timeout: 5000 }),
        axios.get('/api/proxy/api/health/db', { timeout: 5000 }),
        axios.get('/api/proxy/api/health/qdrant', { timeout: 5000 }),
      ]);

      const ollamaModels: OllamaModel[] = ollamaRes.status === 'fulfilled' ? ((ollamaRes.value.data as { models?: OllamaModel[] }).models ?? []) : [];
      setSystemInfo({
        ollamaModels,
        ollamaStatus: ollamaRes.status === 'fulfilled' ? 'online' : 'offline',
        dbStatus: dbRes.status === 'fulfilled' ? 'online' : 'offline',
        qdrantStatus: qdrantRes.status === 'fulfilled' ? 'online' : 'offline',
      });
    } finally {
      setSystemLoading(false);
    }
  }, []);

  const refreshControl = useCallback(async () => {
    setControlLoading(true);
    try {
      const res = await axios.get('/api/proxy/api/control/status', { timeout: 5000 });
      setControlStatus(res.data as ControlStatus);
    } finally {
      setControlLoading(false);
    }
  }, []);

  const refreshActivity = useCallback(async () => {
    setActivityLoading(true);
    try {
      const res = await axios.get('/api/proxy/api/dashboard/activity?limit=8', { timeout: 5000 });
      const payload = res.data as { items?: RecentActivity[] };
      setRecentActivity(payload.items ?? []);
    } catch {
      // Keep the previous activity snapshot on transient errors.
    } finally {
      setActivityLoading(false);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([refreshControl(), refreshServices(), refreshAnalytics(), refreshSystem(), refreshActivity()]);
    setLastRefresh(new Date());
    setRefreshing(false);
  }, [refreshControl, refreshServices, refreshAnalytics, refreshSystem, refreshActivity]);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, AUTO_REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refreshAll]);

  useEffect(() => {
    const sectionParam = searchParams.get('section');
    if (
      sectionParam === 'control' ||
      sectionParam === 'services' ||
      sectionParam === 'analytics' ||
      sectionParam === 'users' ||
      sectionParam === 'system'
    ) {
      setActiveSection(sectionParam);
    }
  }, [searchParams]);

  const navItems: { id: NavSection; label: string; icon: React.ElementType }[] = [
    { id: 'control', label: 'Kontrolle', icon: ShieldCheckIcon },
    { id: 'services', label: 'Services', icon: ServerIcon },
    { id: 'analytics', label: 'Analytics', icon: ChartBarIcon },
    { id: 'users', label: 'Benutzer', icon: UsersIcon },
    { id: 'system', label: 'System', icon: CpuChipIcon },
  ];

  const onlineCount = services.filter((s) => s.status === 'online').length;
  const allOnline = onlineCount === services.length;
  const topBadgeTone = controlStatus?.attentionRequired ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : allOnline ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20';
  const topBadgeText = controlStatus?.attentionRequired
    ? `${controlStatus.attentionRequired} Operator-Hinweise`
    : allOnline
    ? 'Alle Systeme OK'
    : `${services.length - onlineCount} Problem${services.length - onlineCount > 1 ? 'e' : ''}`;

  return (
    <div className="flex h-screen bg-gray-900 overflow-hidden">
      <aside className="w-60 flex-shrink-0 bg-gray-800/80 border-r border-gray-700/60 flex flex-col">
        <div className="px-5 py-5 border-b border-gray-700/60">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-kirobi-600 flex items-center justify-center text-white font-bold text-sm">K</div>
            <div>
              <p className="text-sm font-bold text-white leading-tight">Kirobi</p>
              <p className="text-xs text-gray-500 leading-tight">Admin Dashboard</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => setActiveSection(id)} className={`nav-item w-full ${activeSection === id ? 'nav-item-active' : 'nav-item-inactive'}`}>
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{label}</span>
              {id === 'control' && controlStatus && (
                <span className={`ml-auto text-xs font-mono px-1.5 py-0.5 rounded ${controlStatus.attentionRequired > 0 ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'}`}>{controlStatus.attentionRequired}</span>
              )}
              {id === 'services' && (
                <span className={`ml-auto text-xs font-mono px-1.5 py-0.5 rounded ${allOnline ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>{onlineCount}/{services.length}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="px-4 py-4 border-t border-gray-700/60 space-y-2">
          <div className="flex items-center gap-2 text-xs text-gray-500"><ClockIcon className="w-3.5 h-3.5" /><span>Aktualisiert {formatRelativeTime(lastRefresh)}</span></div>
          <button onClick={refreshAll} disabled={refreshing} className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs text-gray-400 hover:text-white bg-gray-700/50 hover:bg-gray-700 rounded-lg transition-all disabled:opacity-50">
            <ArrowPathIcon className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Lädt...' : 'Jetzt aktualisieren'}
          </button>
          <p className="text-xs text-gray-600 text-center">Auto-Refresh alle 30s</p>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <header className="sticky top-0 z-10 bg-gray-900/80 backdrop-blur border-b border-gray-700/60 px-6 py-4">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-base font-semibold text-white capitalize">{navItems.find((n) => n.id === activeSection)?.label}</h1>
              <p className="text-xs text-gray-500 mt-0.5">OpenDisruption · lokal, transparent, operator-controlled</p>
            </div>
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${topBadgeTone}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${controlStatus?.attentionRequired ? 'bg-amber-400' : allOnline ? 'bg-emerald-400' : 'bg-red-400'}`} />
              {topBadgeText}
            </div>
          </div>
        </header>

        <div className="p-6 max-w-6xl">
          {activeSection === 'control' && (
            <div className="space-y-6">
              <ControlPanel control={controlStatus} loading={controlLoading} />
              <ActivityPanel items={recentActivity} loading={activityLoading} />
            </div>
          )}
          {activeSection === 'services' && <ServicesPanel services={services} />}
          {activeSection === 'analytics' && (
            <div className="space-y-6">
              <AnalyticsPanel stats={analyticsStats} loading={analyticsLoading} />
              <ActivityPanel items={recentActivity} loading={activityLoading} />
            </div>
          )}
          {activeSection === 'users' && <UsersPanel />}
          {activeSection === 'system' && <SystemPanel info={systemInfo} loading={systemLoading} />}
        </div>
      </main>
    </div>
  );
}
