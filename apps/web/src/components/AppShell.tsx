'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode, useEffect, useMemo, useState } from 'react';
import {
  Bars3Icon,
  BoltIcon,
  ChatBubbleLeftRightIcon,
  CircleStackIcon,
  CodeBracketSquareIcon,
  Cog6ToothIcon,
  CommandLineIcon,
  CpuChipIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
  SparklesIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

type ServiceStatus = 'online' | 'offline' | 'unknown';

interface ShellProbe {
  label: string;
  path: string;
  status: ServiceStatus;
}

const PRIMARY_NAV = [
  { href: '/control-center', label: 'Control Center', icon: BoltIcon },
  { href: '/knowledge-base', label: 'Knowledge Base', icon: CircleStackIcon },
  { href: '/agents-hub', label: 'Agents', icon: CpuChipIcon },
  { href: '/workbench', label: 'Workbench', icon: SparklesIcon },
  { href: '/developer-studio', label: 'Developer Studio', icon: CodeBracketSquareIcon },
];

const SECONDARY_NAV = [
  { href: '/chat', label: 'Chat', icon: ChatBubbleLeftRightIcon },
  { href: '/search', label: 'Search', icon: MagnifyingGlassIcon },
  { href: '/upload', label: 'Upload', icon: CommandLineIcon },
  { href: '/status', label: 'Status', icon: ShieldCheckIcon },
  { href: '/settings', label: 'Settings', icon: Cog6ToothIcon },
];

const TITLES: Record<string, { title: string; subtitle: string }> = {
  '/control-center': { title: 'Agentic Control Center', subtitle: 'Zentrale Oberfläche für Status, Wissen, Agenten und Workbenches.' },
  '/knowledge-base': { title: 'Knowledge Base', subtitle: 'Wissensdatenbank, Uploads, Suche und Graph-Einstieg.' },
  '/agents-hub': { title: 'Agents Hub', subtitle: 'Hermes, Opencode, KeyCodi und Orchestrierungsstatus.' },
  '/workbench': { title: 'Workbench', subtitle: 'Eingebettete Admin- und Modelloberflächen.' },
  '/developer-studio': { title: 'Developer Studio', subtitle: 'Lokale Entwicklungswege, VS Code und Repo-Shortcuts.' },
  '/chat': { title: 'Chat', subtitle: 'Lokale Konversationen und Assistenz.' },
  '/search': { title: 'Search', subtitle: 'Zonenbewusste Suche über lokales Wissen.' },
  '/upload': { title: 'Upload', subtitle: 'Neue Inhalte in die Wissensbasis einspeisen.' },
  '/status': { title: 'Status', subtitle: 'Edge-, Remote- und Stack-Zustände.' },
  '/settings': { title: 'Settings', subtitle: 'Persönliche und runtime-nahe Steuerflächen.' },
};

function probeClass(status: ServiceStatus): string {
  if (status === 'online') return 'bg-emerald-500';
  if (status === 'offline') return 'bg-red-500';
  return 'bg-amber-500';
}

function ShellNavItem({
  href,
  label,
  icon: Icon,
  pathname,
  onNavigate,
}: {
  href: string;
  label: string;
  icon: React.ElementType;
  pathname: string;
  onNavigate?: () => void;
}) {
  const active = pathname === href || pathname.startsWith(`${href}/`);
  return (
    <Link
      href={href}
      onClick={onNavigate}
      className={`flex items-center gap-3 rounded-2xl px-3 py-3 text-sm transition ${
        active
          ? 'bg-kirobi-500/15 text-white border border-kirobi-500/30'
          : 'text-gray-400 hover:bg-gray-900/70 hover:text-white border border-transparent'
      }`}
    >
      <Icon className={`h-5 w-5 ${active ? 'text-kirobi-300' : 'text-gray-500'}`} />
      <span className="font-medium">{label}</span>
    </Link>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [probes, setProbes] = useState<ShellProbe[]>([
    { label: 'API', path: '/api/health', status: 'unknown' },
    { label: 'Auth', path: '/api/auth/health', status: 'unknown' },
    { label: 'Telegram', path: '/telegram/health', status: 'unknown' },
  ]);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (pathname === '/') return;
    void Promise.all(
      probes.map(async (probe) => {
        try {
          const response = await fetch(probe.path, { cache: 'no-store' });
          return { ...probe, status: response.ok ? 'online' : 'offline' as ServiceStatus };
        } catch {
          return { ...probe, status: 'offline' as ServiceStatus };
        }
      })
    ).then(setProbes);
  }, [pathname]);

  const current = useMemo(() => {
    const key = Object.keys(TITLES).find((route) => pathname === route || pathname.startsWith(`${route}/`));
    return key ? TITLES[key] : { title: 'Kirobi', subtitle: 'Lokale agentische Oberfläche.' };
  }, [pathname]);

  if (pathname === '/') {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-[#060816] text-white">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.14),transparent_26%),radial-gradient(circle_at_80%_20%,rgba(168,85,247,0.13),transparent_24%),radial-gradient(circle_at_50%_100%,rgba(34,197,94,0.08),transparent_26%)]" />

      <aside className="fixed inset-y-0 left-0 z-40 hidden w-80 border-r border-white/10 bg-gray-950/85 backdrop-blur xl:flex xl:flex-col">
        <div className="border-b border-white/10 px-6 py-6">
          <Link href="/control-center" className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-kirobi-500 to-violet-500 text-lg font-bold text-white shadow-lg shadow-kirobi-950/50">
              K
            </div>
            <div>
              <p className="text-lg font-semibold text-white">OpenDisruption</p>
              <p className="text-sm text-gray-500">Agentic Control Shell</p>
            </div>
          </Link>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto px-5 py-6">
          <section>
            <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-[0.24em] text-gray-500">Core</p>
            <div className="space-y-2">
              {PRIMARY_NAV.map((item) => (
                <ShellNavItem key={item.href} {...item} pathname={pathname} />
              ))}
            </div>
          </section>
          <section>
            <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-[0.24em] text-gray-500">Actions</p>
            <div className="space-y-2">
              {SECONDARY_NAV.map((item) => (
                <ShellNavItem key={item.href} {...item} pathname={pathname} />
              ))}
            </div>
          </section>
          <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-4">
            <p className="text-sm font-semibold text-white">Runtime pulse</p>
            <div className="mt-4 space-y-2">
              {probes.map((probe) => (
                <div key={probe.label} className="flex items-center justify-between rounded-2xl bg-gray-950/70 px-3 py-2">
                  <span className="text-sm text-gray-300">{probe.label}</span>
                  <span className="inline-flex items-center gap-2 text-xs text-gray-400">
                    <span className={`h-2.5 w-2.5 rounded-full ${probeClass(probe.status)}`} />
                    {probe.status}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </aside>

      <div className="relative xl:pl-80">
        <header className="sticky top-0 z-30 border-b border-white/10 bg-[#060816]/80 backdrop-blur">
          <div className="mx-auto flex max-w-[1800px] items-center justify-between gap-4 px-4 py-4 sm:px-6">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setMobileOpen(true)}
                className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-white xl:hidden"
              >
                <Bars3Icon className="h-6 w-6" />
              </button>
              <div>
                <p className="text-lg font-semibold text-white">{current.title}</p>
                <p className="text-sm text-gray-500">{current.subtitle}</p>
              </div>
            </div>
            <div className="hidden items-center gap-2 md:flex">
              {probes.map((probe) => (
                <div key={probe.label} className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-gray-300">
                  <span className={`h-2 w-2 rounded-full ${probeClass(probe.status)}`} />
                  {probe.label}
                </div>
              ))}
            </div>
          </div>
        </header>

        {mobileOpen && (
          <div className="fixed inset-0 z-50 xl:hidden">
            <button
              type="button"
              className="absolute inset-0 bg-black/60"
              onClick={() => setMobileOpen(false)}
            />
            <div className="absolute inset-y-0 left-0 flex w-[88vw] max-w-sm flex-col border-r border-white/10 bg-gray-950 p-5 shadow-2xl">
              <div className="mb-5 flex items-center justify-between">
                <Link href="/control-center" className="text-lg font-semibold text-white">
                  OpenDisruption
                </Link>
                <button
                  type="button"
                  onClick={() => setMobileOpen(false)}
                  className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/5"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
              <div className="space-y-6 overflow-y-auto">
                <section className="space-y-2">
                  {PRIMARY_NAV.map((item) => (
                    <ShellNavItem key={item.href} {...item} pathname={pathname} onNavigate={() => setMobileOpen(false)} />
                  ))}
                </section>
                <section className="space-y-2">
                  {SECONDARY_NAV.map((item) => (
                    <ShellNavItem key={item.href} {...item} pathname={pathname} onNavigate={() => setMobileOpen(false)} />
                  ))}
                </section>
              </div>
            </div>
          </div>
        )}

        <main className="mx-auto max-w-[1800px] px-0 pb-10">
          {children}
        </main>
      </div>
    </div>
  );
}
