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

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/');
      return;
    }
    void axios.get<ControlStatus>('/api/control/status', {
      headers: { Authorization: `Bearer ${token}` },
    }).then((response) => setControl(response.data));
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
            Hermes, Opencode, KeyCodi und die Operator-Signale bekommen hier eine eigene Bühne statt irgendwo in verstreuten Tools zu verschwinden.
          </p>
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
