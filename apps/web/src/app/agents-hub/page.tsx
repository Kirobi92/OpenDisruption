'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  ArrowUpRightIcon,
  BoltIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface ControlStatus {
  activeTasks: number;
  pendingTasks: number;
  blockedTasks: number;
  deadLetterTasks: number;
  operatorGuidance: string[];
}

interface AgentOption {
  id: string;
  label: string;
  description: string;
  category?: string;
  default_model?: string;
}

interface RuntimeOptions {
  available_models: string[];
  default_model: string;
  current_defaults: Record<string, string>;
  agent_options: AgentOption[];
}

const CATEGORY_ACCENT: Record<string, string> = {
  core: 'from-violet-500/25 to-sky-500/10 border-violet-400/30',
  orchestrator: 'from-amber-500/25 to-orange-500/10 border-amber-400/30',
  coding: 'from-emerald-500/25 to-cyan-500/10 border-emerald-400/30',
  research: 'from-fuchsia-500/25 to-pink-500/10 border-fuchsia-400/30',
  ops: 'from-rose-500/25 to-red-500/10 border-rose-400/30',
  design: 'from-blue-500/25 to-indigo-500/10 border-blue-400/30',
  docs: 'from-teal-500/25 to-emerald-500/10 border-teal-400/30',
  review: 'from-yellow-500/25 to-amber-500/10 border-yellow-400/30',
  security: 'from-red-500/25 to-orange-500/10 border-red-400/30',
  testing: 'from-cyan-500/25 to-blue-500/10 border-cyan-400/30',
};

const AGENT_SURFACES = [
  {
    title: 'Hermes',
    subtitle: 'Reasoning / Telegram / lokale Analyse',
    description: 'Hermes ist dein primärer Denk- und Analysepfad. Hier laufen Reasoning, lokale Antworten und Telegram-nahe Agentik zusammen.',
    href: '/dashboard/agents',
    accent: 'from-violet-500/20 to-sky-500/10',
  },
  {
    title: 'Opencode',
    subtitle: 'Governed coding workbench',
    description: 'Opencode bleibt Workbench und nicht Policy-Quelle. Von hier springst du in die Workbench und die repo-eigenen Orchestrierungsdokumente.',
    href: '/workbench?surface=open-webui',
    accent: 'from-emerald-500/20 to-cyan-500/10',
  },
  {
    title: 'KeyCodi',
    subtitle: 'Master-Code-Orchestrator',
    description: 'Repo-eigene Coding-Orchestrierung über sichere Handoffs. Operator-Signale und Aufgabenlage bleiben lokal sichtbar.',
    href: '/dashboard/tasks',
    accent: 'from-amber-500/20 to-orange-500/10',
  },
];

export default function AgentsHubPage() {
  const router = useRouter();
  const [control, setControl] = useState<ControlStatus | null>(null);
  const [runtime, setRuntime] = useState<RuntimeOptions | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/');
      return;
    }
    void axios.get<ControlStatus>('/api/control/status', {
      headers: { Authorization: `Bearer ${token}` },
    }).then((response) => setControl(response.data));
    void axios.get<RuntimeOptions>('/api/chat/runtime/options', {
      headers: { Authorization: `Bearer ${token}` },
    }).then((response) => setRuntime(response.data)).catch(() => setRuntime(null));
  }, [router]);

  return (
    <div className="min-h-[calc(100vh-80px)] px-4 py-6 sm:px-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <section className="rounded-[2rem] border border-white/10 bg-gradient-to-br from-gray-950 via-slate-900 to-gray-950 p-6">
          <span className="inline-flex items-center gap-2 rounded-full border border-violet-400/20 bg-violet-400/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-violet-200">
            <CpuChipIcon className="h-4 w-4" />
            Agents Hub
          </span>
          <h1 className="mt-4 text-3xl font-bold text-white">Agenten sichtbar, nicht versteckt.</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-gray-400">
            Alle lokalen Agenten und Ollama-Modelle laufen auf deiner RTX 3090. Wähle einen Agenten — er bringt sein passendes Modell mit.
          </p>
          {runtime && (
            <div className="mt-4 flex flex-wrap gap-2">
              {runtime.available_models.map((m) => (
                <span
                  key={m}
                  className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-200"
                >
                  <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
                  {m}
                </span>
              ))}
              <span className="inline-flex items-center gap-1.5 rounded-full border border-violet-400/30 bg-violet-500/10 px-3 py-1 text-xs text-violet-200">
                Default: {runtime.default_model}
              </span>
            </div>
          )}
        </section>

        {/* Volle Agent-Matrix */}
        <section>
          <h2 className="mb-3 text-xs font-mono uppercase tracking-[0.3em] text-violet-300">
            Lokale Agenten ({runtime?.agent_options.length ?? 0})
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {(runtime?.agent_options ?? []).map((agent) => {
              const accent = CATEGORY_ACCENT[agent.category ?? 'core'] ?? CATEGORY_ACCENT.core;
              return (
                <Link
                  key={agent.id}
                  href={`/chat?agent=${agent.id}`}
                  className={`group rounded-2xl border bg-gradient-to-br ${accent} p-4 transition hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(139,92,246,0.25)]`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.22em] text-white/60">{agent.category ?? 'core'}</p>
                      <p className="mt-2 text-lg font-semibold text-white">{agent.label}</p>
                    </div>
                    <ArrowUpRightIcon className="h-4 w-4 text-white/60 transition group-hover:text-white" />
                  </div>
                  <p className="mt-2 line-clamp-2 text-xs leading-5 text-white/75">{agent.description}</p>
                  {agent.default_model && (
                    <div className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-black/30 px-2 py-0.5 text-[10px] font-mono text-emerald-300">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" />
                      {agent.default_model}
                    </div>
                  )}
                </Link>
              );
            })}
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_360px]">
          <div className="grid gap-4 lg:grid-cols-3">
            {AGENT_SURFACES.map((surface) => (
              <Link
                key={surface.title}
                href={surface.href}
                className={`rounded-[2rem] border border-white/10 bg-gradient-to-br ${surface.accent} p-5 transition hover:border-white/20`}
              >
                <p className="text-xs uppercase tracking-[0.24em] text-gray-400">{surface.subtitle}</p>
                <p className="mt-3 text-xl font-semibold text-white">{surface.title}</p>
                <p className="mt-3 text-sm leading-6 text-gray-300">{surface.description}</p>
                <ArrowUpRightIcon className="mt-6 h-5 w-5 text-white/80" />
              </Link>
            ))}
          </div>

          <aside className="space-y-4 rounded-[2rem] border border-white/10 bg-gray-950/70 p-5">
            <div>
              <p className="text-sm font-semibold text-white">Runtime pulse</p>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Active</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{control?.activeTasks ?? 0}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Pending</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{control?.pendingTasks ?? 0}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Blocked</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{control?.blockedTasks ?? 0}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Dead letter</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{control?.deadLetterTasks ?? 0}</p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center gap-2">
                <ShieldCheckIcon className="h-5 w-5 text-amber-300" />
                <p className="text-sm font-semibold text-white">Operator guidance</p>
              </div>
              <div className="mt-3 space-y-2 text-sm text-gray-400">
                {(control?.operatorGuidance ?? []).slice(0, 3).map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </div>
            </div>

            <div className="grid gap-3">
              <Link href="/dashboard/agents" className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-kirobi-500/30">
                <div className="flex items-center gap-2">
                  <SparklesIcon className="h-5 w-5 text-violet-300" />
                  <p className="text-sm font-semibold text-white">Volle Agent Registry</p>
                </div>
              </Link>
              <Link href="/dashboard/tasks" className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-kirobi-500/30">
                <div className="flex items-center gap-2">
                  <BoltIcon className="h-5 w-5 text-kirobi-300" />
                  <p className="text-sm font-semibold text-white">Task-Orchestrierung</p>
                </div>
              </Link>
            </div>
          </aside>
        </section>
      </div>
    </div>
  );
}
