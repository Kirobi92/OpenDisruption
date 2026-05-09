'use client';

import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import axios from 'axios';
import {
  ClipboardDocumentListIcon,
  ArrowPathIcon,
  ClockIcon,
  ServerIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'blocked' | 'dead_letter' | 'failed' | 'done' | string;
type TaskPriority = 'critical' | 'high' | 'medium' | 'low' | 'background' | string;

interface Task {
  id: string | number;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  created_at?: string;
  updated_at?: string;
  agent?: string;
  zone?: string;
  last_error?: string | null;
  operator_hint?: string;
}

const AUTO_REFRESH_MS = 30_000;

function normalizeStatus(status: TaskStatus): string {
  return status === 'done' ? 'completed' : status;
}

function formatRelativeTime(date: Date | null): string {
  if (!date) return '—';
  const diffMs = Date.now() - date.getTime();
  if (diffMs < 5_000) return 'gerade eben';
  if (diffMs < 60_000) return `vor ${Math.floor(diffMs / 1000)}s`;
  if (diffMs < 3_600_000) return `vor ${Math.floor(diffMs / 60_000)}min`;
  return `vor ${Math.floor(diffMs / 3_600_000)}h`;
}

function formatDate(iso?: string): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function statusLabel(status: string): string {
  switch (status) {
    case 'completed':
      return 'Erledigt';
    case 'blocked':
      return 'Blockiert';
    case 'dead_letter':
      return 'Dead-Letter';
    case 'in_progress':
      return 'In Arbeit';
    case 'failed':
      return 'Fehlgeschlagen';
    default:
      return 'Ausstehend';
  }
}

function StatusBadge({ status }: { status: TaskStatus }) {
  const normalized = normalizeStatus(status);
  const base = 'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium';
  switch (normalized) {
    case 'completed':
      return <span className={`${base} bg-emerald-500/10 text-emerald-400 border border-emerald-500/20`}><CheckCircleIcon className="w-3 h-3" />Erledigt</span>;
    case 'in_progress':
      return <span className={`${base} bg-kirobi-500/10 text-kirobi-400 border border-kirobi-500/20`}><ArrowPathIcon className="w-3 h-3 animate-spin" />In Arbeit</span>;
    case 'blocked':
      return <span className={`${base} bg-amber-500/10 text-amber-400 border border-amber-500/20`}><ShieldCheckIcon className="w-3 h-3" />Blockiert</span>;
    case 'dead_letter':
    case 'failed':
      return <span className={`${base} bg-red-500/10 text-red-400 border border-red-500/20`}><XCircleIcon className="w-3 h-3" />{normalized === 'dead_letter' ? 'Dead-Letter' : 'Fehlgeschlagen'}</span>;
    default:
      return <span className={`${base} bg-gray-700 text-gray-300 border border-gray-600`}><ClockIcon className="w-3 h-3" />Ausstehend</span>;
  }
}

function PriorityBadge({ priority }: { priority: TaskPriority }) {
  const base = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium';
  switch (priority) {
    case 'critical':
      return <span className={`${base} bg-red-500/10 text-red-300`}>🚨 Kritisch</span>;
    case 'high':
      return <span className={`${base} bg-red-500/10 text-red-400`}>🔴 Hoch</span>;
    case 'medium':
      return <span className={`${base} bg-amber-500/10 text-amber-400`}>🟡 Mittel</span>;
    case 'background':
      return <span className={`${base} bg-gray-800 text-gray-500`}>🌙 Hintergrund</span>;
    default:
      return <span className={`${base} bg-gray-700 text-gray-400`}>⚪ Niedrig</span>;
  }
}

function SummaryCard({ label, value, tone }: { label: string; value: number; tone: 'kirobi' | 'amber' | 'red' | 'emerald' }) {
  const toneClasses = {
    kirobi: 'bg-kirobi-500/10 text-kirobi-400 border-kirobi-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    red: 'bg-red-500/10 text-red-400 border-red-500/20',
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  };
  return (
    <div className={`card border ${toneClasses[tone]}`}>
      <p className="text-xs uppercase tracking-wider text-gray-500">{label}</p>
      <p className="text-2xl font-bold mt-2">{value}</p>
    </div>
  );
}

function TaskCard({ task }: { task: Task }) {
  const normalized = normalizeStatus(task.status);

  return (
    <div className="card space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-white leading-snug">{task.title}</p>
          {task.description && <p className="text-xs text-gray-400 mt-1 line-clamp-3">{task.description}</p>}
        </div>
        <StatusBadge status={normalized} />
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <PriorityBadge priority={task.priority} />
        {task.agent && <span className="text-xs text-gray-500 font-mono bg-gray-700/50 px-2 py-0.5 rounded">@{task.agent}</span>}
        {task.zone && <span className="text-xs text-gray-500 bg-gray-700/50 px-2 py-0.5 rounded">{task.zone}</span>}
      </div>

      {task.operator_hint && <p className="text-sm text-gray-300">{task.operator_hint}</p>}
      {task.last_error && <p className="text-xs text-amber-300 bg-amber-500/5 border border-amber-500/10 rounded-lg px-3 py-2">{task.last_error}</p>}

      <div className="flex items-center gap-4 text-xs text-gray-600 flex-wrap">
        {task.created_at && <span>Erstellt {formatDate(task.created_at)}</span>}
        {task.updated_at && <span>Aktualisiert {formatDate(task.updated_at)}</span>}
        <span>Status: {statusLabel(normalized)}</span>
      </div>
    </div>
  );
}

export default function TasksPage() {
  const searchParams = useSearchParams();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [filter, setFilter] = useState<'all' | 'pending' | 'in_progress' | 'completed' | 'blocked' | 'dead_letter'>('all');

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get('/api/proxy/api/tasks?limit=50', { timeout: 8000 });
      const data = res.data as { tasks?: Task[] } | Task[];
      const taskList = Array.isArray(data) ? data : (data.tasks ?? []);
      setTasks(taskList);
    } catch {
      setError('Tasks konnten nicht geladen werden. Ist der API-Service erreichbar?');
      setTasks([]);
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  }, []);

  useEffect(() => {
    loadTasks();
    const interval = setInterval(loadTasks, AUTO_REFRESH_MS);
    return () => clearInterval(interval);
  }, [loadTasks]);

  useEffect(() => {
    const filterParam = searchParams.get('filter');
    if (
      filterParam === 'all' ||
      filterParam === 'pending' ||
      filterParam === 'in_progress' ||
      filterParam === 'completed' ||
      filterParam === 'blocked' ||
      filterParam === 'dead_letter'
    ) {
      setFilter(filterParam);
    }
  }, [searchParams]);

  const normalizedTasks = tasks.map((task) => ({ ...task, status: normalizeStatus(task.status) }));
  const filtered = filter === 'all' ? normalizedTasks : normalizedTasks.filter((t) => t.status === filter);
  const counts = {
    all: normalizedTasks.length,
    pending: normalizedTasks.filter((t) => t.status === 'pending').length,
    in_progress: normalizedTasks.filter((t) => t.status === 'in_progress').length,
    completed: normalizedTasks.filter((t) => t.status === 'completed').length,
    blocked: normalizedTasks.filter((t) => t.status === 'blocked').length,
    dead_letter: normalizedTasks.filter((t) => t.status === 'dead_letter' || t.status === 'failed').length,
  };

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
          <a href="/" className="nav-item nav-item-inactive w-full flex"><ShieldCheckIcon className="w-4 h-4" /><span>Kontrolle</span></a>
          <a href="/services" className="nav-item nav-item-inactive w-full flex"><ServerIcon className="w-4 h-4" /><span>Services</span></a>
          <a href="/tasks" className="nav-item nav-item-active w-full flex"><ClipboardDocumentListIcon className="w-4 h-4" /><span>Tasks</span></a>
          <a href="/agents" className="nav-item nav-item-inactive w-full flex"><ServerIcon className="w-4 h-4" /><span>Agents</span></a>
        </nav>
        <div className="px-4 py-4 border-t border-gray-700/60 space-y-2">
          <div className="flex items-center gap-2 text-xs text-gray-500"><ClockIcon className="w-3.5 h-3.5" /><span>Aktualisiert {formatRelativeTime(lastRefresh)}</span></div>
          <button onClick={loadTasks} disabled={loading} className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs text-gray-400 hover:text-white bg-gray-700/50 hover:bg-gray-700 rounded-lg transition-all disabled:opacity-50">
            <ArrowPathIcon className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Lädt...' : 'Aktualisieren'}
          </button>
          <p className="text-xs text-gray-600 text-center">Auto-Refresh alle 30s</p>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <header className="sticky top-0 z-10 bg-gray-900/80 backdrop-blur border-b border-gray-700/60 px-6 py-4">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-base font-semibold text-white">Supervisor Tasks</h1>
              <p className="text-xs text-gray-500 mt-0.5">Lokale Queue, Human-Gates und Dead-Letter im Blick</p>
            </div>
            <span className={`text-xs font-medium px-3 py-1.5 rounded-full border ${counts.blocked + counts.dead_letter > 0 ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'}`}>{counts.blocked + counts.dead_letter > 0 ? `${counts.blocked + counts.dead_letter} Task(s) brauchen Triage` : 'Keine offenen Triage-Fälle'}</span>
          </div>
        </header>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <SummaryCard label="Pending" value={counts.pending} tone="kirobi" />
            <SummaryCard label="In Arbeit" value={counts.in_progress} tone="emerald" />
            <SummaryCard label="Blockiert" value={counts.blocked} tone="amber" />
            <SummaryCard label="Dead-Letter" value={counts.dead_letter} tone="red" />
          </div>

          <div className="flex gap-2 flex-wrap">
            {(['all', 'pending', 'in_progress', 'completed', 'blocked', 'dead_letter'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filter === f ? 'bg-kirobi-600/20 text-kirobi-400 border border-kirobi-600/30' : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600'}`}
              >
                {f === 'all' ? 'Alle' : f === 'in_progress' ? 'In Arbeit' : f === 'completed' ? 'Erledigt' : f === 'blocked' ? 'Blockiert' : f === 'dead_letter' ? 'Dead-Letter' : 'Ausstehend'}
                <span className="ml-1.5 text-gray-500">{counts[f] ?? 0}</span>
              </button>
            ))}
          </div>

          {error && (
            <div className="card border-red-500/30 bg-red-500/5">
              <div className="flex items-center gap-3">
                <ExclamationTriangleIcon className="w-5 h-5 text-red-400 flex-shrink-0" />
                <p className="text-sm text-red-300">{error}</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="card animate-pulse">
                  <div className="h-4 bg-gray-700 rounded w-3/4 mb-2" />
                  <div className="h-3 bg-gray-700 rounded w-1/2" />
                </div>
              ))}
            </div>
          )}

          {!loading && !error && filtered.length === 0 && (
            <div className="card text-center py-12">
              <ClipboardDocumentListIcon className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400 text-sm">Keine Tasks gefunden</p>
              <p className="text-gray-600 text-xs mt-1">{filter !== 'all' ? 'Versuche einen anderen Filter' : 'Der API-Service liefert keine Supervisor-Tasks'}</p>
            </div>
          )}

          {!loading && filtered.length > 0 && (
            <div className="space-y-3">
              {filtered.map((task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
