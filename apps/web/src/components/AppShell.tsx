'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode, useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  Bars3Icon, BoltIcon, ChatBubbleLeftRightIcon, CircleStackIcon, CodeBracketSquareIcon,
  Cog6ToothIcon, CommandLineIcon, CpuChipIcon, MagnifyingGlassIcon, ShareIcon, ShieldCheckIcon,
  SparklesIcon, XMarkIcon,
} from '@heroicons/react/24/outline';

type ServiceStatus = 'online' | 'offline' | 'unknown';
interface ShellProbe { label: string; path: string; status: ServiceStatus; }

const PRIMARY_NAV = [
  { href: '/control-center', label: 'Control Center', icon: BoltIcon },
  { href: '/knowledge-base', label: 'Knowledge Base', icon: CircleStackIcon },
  { href: '/knowledge-graph', label: 'Vault Graph', icon: ShareIcon },
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
  '/knowledge-graph': { title: 'Vault Cortex · 3D', subtitle: 'Live-3D-Karte des Obsidian-Vaults — GPU-beschleunigt.' },
  '/agents-hub': { title: 'Agents Hub', subtitle: 'Hermes, Opencode, KeyCodi und Orchestrierungsstatus.' },
  '/workbench': { title: 'Workbench', subtitle: 'Eingebettete Admin- und Modelloberflächen.' },
  '/developer-studio': { title: 'Developer Studio', subtitle: 'Lokale Entwicklungswege, VS Code und Repo-Shortcuts.' },
  '/chat': { title: 'Chat', subtitle: 'Lokale Konversationen und Assistenz.' },
  '/search': { title: 'Search', subtitle: 'Zonenbewusste Suche über lokales Wissen.' },
  '/upload': { title: 'Upload', subtitle: 'Neue Inhalte in die Wissensbasis einspeisen.' },
  '/status': { title: 'Status', subtitle: 'Edge-, Remote- und Stack-Zustände.' },
  '/settings': { title: 'Settings', subtitle: 'Persönliche und runtime-nahe Steuerflächen.' },
};

function probeColor(status: ServiceStatus): string {
  if (status === 'online') return 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.65)]';
  if (status === 'offline') return 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.65)]';
  return 'bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.55)]';
}

function ShellNavItem({
  href, label, icon: Icon, pathname, onNavigate,
}: {
  href: string; label: string; icon: React.ElementType;
  pathname: string; onNavigate?: () => void;
}) {
  const active = pathname === href || pathname.startsWith(`${href}/`);
  return (
    <Link
      href={href}
      onClick={onNavigate}
      className={[
        'group relative flex items-center gap-3 rounded-2xl border px-3 py-2.5 text-sm font-medium transition-all duration-300 ease-spring',
        active
          ? 'border-aurora-cyan/30 bg-gradient-to-r from-aurora-cyan/15 via-aurora-violet/10 to-transparent text-white shadow-[0_0_24px_rgba(94,234,212,0.12)]'
          : 'border-transparent text-[color:var(--text-secondary)] hover:border-[color:var(--border-soft)] hover:bg-white/[0.03] hover:text-white',
      ].join(' ')}
    >
      {active && (
        <span className="absolute left-0 top-1/2 h-6 w-[3px] -translate-y-1/2 rounded-full bg-gradient-to-b from-aurora-cyan to-aurora-violet shadow-[0_0_12px_rgba(94,234,212,0.7)]" aria-hidden />
      )}
      <Icon className={`h-5 w-5 transition-colors ${active ? 'text-aurora-cyan' : 'text-[color:var(--text-muted)] group-hover:text-[color:var(--text-secondary)]'}`} />
      <span>{label}</span>
    </Link>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const reduced = useReducedMotion();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [probes, setProbes] = useState<ShellProbe[]>([
    { label: 'API', path: '/api/health', status: 'unknown' },
    { label: 'Auth', path: '/api/auth/health', status: 'unknown' },
    { label: 'Telegram', path: '/telegram/health', status: 'unknown' },
  ]);

  useEffect(() => { setMobileOpen(false); }, [pathname]);

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
  }, [pathname]); // eslint-disable-line react-hooks/exhaustive-deps

  const current = useMemo(() => {
    const key = Object.keys(TITLES).find((route) => pathname === route || pathname.startsWith(`${route}/`));
    return key ? TITLES[key] : { title: 'Kirobi', subtitle: 'Lokale agentische Oberfläche.' };
  }, [pathname]);

  if (pathname === '/' || pathname === '/knowledge-graph-3d') return <>{children}</>;

  return (
    <div className="relative min-h-screen text-[color:var(--text-primary)]">
      <div className="ambient-field" aria-hidden="true" />

      {/* Sidebar (desktop) */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-80 flex-col border-r border-[color:var(--border-soft)] bg-[color:var(--bg-deep)]/80 backdrop-blur-2xl xl:flex">
        <div className="border-b border-[color:var(--border-soft)] px-6 py-6">
          <Link href="/control-center" className="group flex items-center gap-4">
            <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl glass-raised transition-transform duration-300 ease-spring group-hover:scale-105">
              <span className="text-lg font-bold text-gradient-aurora">K</span>
              {!reduced && (
                <span className="pointer-events-none absolute -inset-1 rounded-2xl bg-gradient-to-br from-aurora-cyan/30 to-aurora-magenta/30 opacity-0 blur-xl transition-opacity duration-500 group-hover:opacity-100" />
              )}
            </div>
            <div>
              <p className="text-base font-semibold text-white">OpenDisruption</p>
              <p className="text-xs uppercase tracking-[0.22em] text-[color:var(--text-muted)]">Agentic Control Shell</p>
            </div>
          </Link>
        </div>

        <div className="flex-1 space-y-7 overflow-y-auto px-5 py-6">
          <NavSection title="Core" items={PRIMARY_NAV} pathname={pathname} />
          <NavSection title="Actions" items={SECONDARY_NAV} pathname={pathname} />

          <section className="rounded-3xl border border-[color:var(--border-soft)] bg-white/[0.025] p-4 backdrop-blur-xl">
            <p className="flex items-center gap-2 text-sm font-semibold text-white">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-aurora-cyan animate-breathe" />
              Runtime Pulse
            </p>
            <div className="mt-4 space-y-2">
              {probes.map((probe) => (
                <div key={probe.label}
                     className="flex items-center justify-between rounded-2xl bg-[color:var(--bg-void)]/60 px-3 py-2 transition-colors hover:bg-[color:var(--bg-void)]/90">
                  <span className="text-sm text-[color:var(--text-secondary)]">{probe.label}</span>
                  <span className="inline-flex items-center gap-2 text-xs text-[color:var(--text-muted)]">
                    <span className={`h-2 w-2 rounded-full ${probeColor(probe.status)}`} />
                    {probe.status}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </aside>

      <div className="relative xl:pl-80 flex flex-col h-screen">
        <header className="sticky top-0 z-30 border-b border-[color:var(--border-soft)] bg-[color:var(--bg-void)]/75 backdrop-blur-2xl">
          <div className="mx-auto flex max-w-[1800px] items-center justify-between gap-4 px-4 py-4 sm:px-6">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setMobileOpen(true)}
                className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-[color:var(--border-soft)] bg-white/5 text-white transition-colors hover:bg-white/10 xl:hidden"
                aria-label="Navigation öffnen"
              >
                <Bars3Icon className="h-6 w-6" />
              </button>
              <div>
                <p className="text-lg font-semibold text-white tracking-display">{current.title}</p>
                <p className="text-sm text-[color:var(--text-muted)]">{current.subtitle}</p>
              </div>
            </div>
            <div className="hidden items-center gap-2 md:flex">
              {probes.map((probe) => (
                <div key={probe.label}
                     className="inline-flex items-center gap-2 rounded-full border border-[color:var(--border-soft)] bg-white/[0.03] px-3 py-1.5 text-xs text-[color:var(--text-secondary)] backdrop-blur-md">
                  <span className={`h-2 w-2 rounded-full ${probeColor(probe.status)}`} />
                  {probe.label}
                </div>
              ))}
            </div>
          </div>
        </header>

        <AnimatePresence>
          {mobileOpen && (
            <div className="fixed inset-0 z-50 xl:hidden">
              <motion.button
                type="button"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                onClick={() => setMobileOpen(false)}
                aria-label="Navigation schließen"
              />
              <motion.div
                initial={reduced ? { opacity: 0 } : { x: -320, opacity: 0.6 }}
                animate={{ x: 0, opacity: 1 }}
                exit={reduced ? { opacity: 0 } : { x: -320, opacity: 0 }}
                transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
                className="absolute inset-y-0 left-0 flex w-[88vw] max-w-sm flex-col border-r border-[color:var(--border-soft)] bg-[color:var(--bg-deep)] p-5 shadow-2xl"
              >
                <div className="mb-5 flex items-center justify-between">
                  <Link href="/control-center" className="text-lg font-semibold text-gradient-aurora">
                    OpenDisruption
                  </Link>
                  <button
                    type="button"
                    onClick={() => setMobileOpen(false)}
                    className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-[color:var(--border-soft)] bg-white/5"
                    aria-label="Schließen"
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
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        <main className="relative mx-auto w-full max-w-[1800px] px-0 pb-10 flex-1 min-h-0 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

function NavSection({
  title, items, pathname,
}: {
  title: string;
  items: Array<{ href: string; label: string; icon: React.ElementType }>;
  pathname: string;
}) {
  return (
    <section>
      <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.28em] text-[color:var(--text-muted)]">
        {title}
      </p>
      <div className="space-y-1.5">
        {items.map((item) => (
          <ShellNavItem key={item.href} {...item} pathname={pathname} />
        ))}
      </div>
    </section>
  );
}
