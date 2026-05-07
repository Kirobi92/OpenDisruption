'use client';

import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import {
  ClipboardDocumentListIcon,
  ArrowPathIcon,
  ClockIcon,
  ServerIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

// ─── Types ────────────────────────────────────────────────────────────────────

type TaskStatus = 'pending' | 'in_progress' | 'done' | 'failed' | string;
type TaskPriority = 'high' | 'medium' | 'low' | string;

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
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatRelativeTime(date: Date | null): string {
  if (!date) return '—';
  const diffMs = Date.now() - date.getTime();
  if (diffMs < 5_000) return 'gerade eben';
  if (diffMs < 60_000) return `vor ${Math.floor(diffMs / 1000)}s`;
  return `vor ${Math.floor(diffMs / 60_000)}min`;
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

// ─── Components ───────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: TaskStatus }) {
  const base = 'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium';
  switch (status) {
    case 'done':
      return <span className={`${base} bg-emerald-500/10 text-emerald-400 border border-emerald-500/20`}><CheckCircleIcon className="w-3 h-3" />Erledigt</span>;
    case 'in_progress':
      return <span className={`${base} bg-kirobi-500/10 text-kirobi-400 border border-kirobi-500/20`}><ArrowPathIcon className="w-3 h-3 animate-spin" />In Arbeit</span>;
    case 'failed':
      return <span className={`${base} bg-red-500/10 text-red-400 border border-red-500/20`}><XCircleIcon className="w-3 h-3" />Fehlgeschlagen</span>;
    default:
      return <span className={`${base} bg-amber-500/10 text-amber-400 border border-amber-500/20`}><ExclamationTriangleIcon className="w-3 h-3" />Ausstehend</span>;
  }
}

function PriorityBadge({ priority }: { priority: TaskPriority }) {
  const base = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium';
  switch (priority) {
    case 'high':
      return <span className={`${base} bg-red-500/10 text-red-400`}>🔴 Hoch</span>;
    case 'medium':
      return <span className={`${base} bg-amber-500/10 text-amber-400`}>🟡 Mittel</span>;
    default:
      return <span className={`${base} bg-gray-700 text-gray-400`}>⚪ Niedrig</span>;
  }
}

function TaskCard({ task }: { task: Task }) {
  return (
    <div className="card space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-white leading-snug">{task.title}</p>
          {task.description && (
            <p className="text-xs text-gray-400 mt-1 line-clamp-2">{task.description}</p>
          )}
        </div>
        <StatusBadge status={task.status} />
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <PriorityBadge priority={task.priority} />
        {task.agent && (
          <span className="text-xs text-gray-500 font-mono bg-gray-700/50 px-2 py-0.5 rounded">
            @{task.agent}
          </span>
        )}
        {task.zone && (
          <span className="text-xs text-gray-500 bg-gray-700/50 px-2 py-0.5 rounded">
            {task.zone}
          </span>
        )}
      </div>

      <div className="flex items-center gap-4 text-xs text-gray-600">
        {task.created_at && <span>Erstellt {formatDate(task.created_at)}</span>}
        {task.updated_at && <span>Aktualisiert {formatDate(task.updated_at)}</span>}
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [filter, setFilter] = useState<'all' | TaskStatus>('all');

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
  }, [loadTasks]);

  const filtered = filter === 'all' ? tasks : tasks.filter(t => t.status === filter);
  const counts = {
    all: tasks.length,
    pending: tasks.filter(t => t.status === 'pending').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    done: tasks.filter(t => t.status === 'done').length,
    failed: tasks.filter(t => t.status === 'failed').length,
  };

  return (
    <div className="flex h-screen bg-gray-900 overflow-hidden">
      {/* Sidebar */}
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
          <a href="/" className="nav-item nav-item-inactive w-full flex"><ServerIcon className="w-4 h-4" /><span>Übersicht</span></a>
          <a href="/services" className="nav-item nav-item-inactive w-full flex"><ServerIcon className="w-4 h-4" /><span>Services</span></a>
          <a href="/tasks" className="nav-item nav-item-active w-full flex"><ClipboardDocumentListIcon className="w-4 h-4" /><span>Tasks</span></a>
          <a href="/agents" className="nav-item nav-item-inactive w-full flex"><ServerIcon className="w-4 h-4" /><span>Agents</span></a>
        </nav>
        <div className="px-4 py-4 border-t border-gray-700/60 space-y-2">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <ClockIcon className="w-3.5 h-3.5" />
            <span>Aktualisiert {formatRelativeTime(lastRefresh)}</span>
          </div>
          <button
            onClick={loadTasks}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs text-gray-400 hover:text-white bg-gray-700/50 hover:bg-gray-700 rounded-lg transition-all disabled:opacity-50"
          >
            <ArrowPathIcon className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Lädt...' : 'Aktualisieren'}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <header className="sticky top-0 z-10 bg-gray-900/80 backdrop-blur border-b border-gray-700/60 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-base font-semibold text-white">Backlog Tasks</h1>
              <p className="text-xs text-gray-500 mt-0.5">kirobi_core Aufgaben-Backlog</p>
            </div>
            <span className="text-xs text-gray-400 font-mono">{tasks.length} Tasks gesamt</span>
          </div>
        </header>

        <div className="p-6 space-y-6">
          {/* Filter tabs */}
          <div className="flex gap-2 flex-wrap">
            {(['all', 'pending', 'in_progress', 'done', 'failed'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  filter === f
                    ? 'bg-kirobi-600/20 text-kirobi-400 border border-kirobi-600/30'
                    : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600'
                }`}
              >
                {f === 'all' ? 'Alle' : f === 'in_progress' ? 'In Arbeit' : f === 'done' ? 'Erledigt' : f === 'failed' ? 'Fehlgeschlagen' : 'Ausstehend'}
                <span className="ml-1.5 text-gray-500">{counts[f] ?? 0}</span>
              </button>
            ))}
          </div>

          {/* Error */}
          {error && (
            <div className="card border-red-500/30 bg-red-500/5">
              <div className="flex items-center gap-3">
                <ExclamationTriangleIcon className="w-5 h-5 text-red-400 flex-shrink-0" />
                <p className="text-sm text-red-300">{error}</p>
              </div>
            </div>
          )}

          {/* Loading skeleton */}
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

          {/* Empty state */}
          {!loading && !error && filtered.length === 0 && (
            <div className="card text-center py-12">
              <ClipboardDocumentListIcon className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400 text-sm">Keine Tasks gefunden</p>
              <p className="text-gray-600 text-xs mt-1">
                {filter !== 'all' ? 'Versuche einen anderen Filter' : 'Der API-Service liefert keine Tasks'}
              </p>
            </div>
          )}

          {/* Task list */}
          {!loading && filtered.length > 0 && (
            <div className="space-y-3">
              {filtered.map(task => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
