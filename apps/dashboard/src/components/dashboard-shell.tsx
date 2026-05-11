'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ClipboardDocumentListIcon,
  Cog6ToothIcon,
  CpuChipIcon,
  HomeIcon,
  ServerIcon,
} from '@heroicons/react/24/outline';

const NAV_ITEMS = [
  { href: '/', label: 'Übersicht', icon: HomeIcon },
  { href: '/services', label: 'Services', icon: ServerIcon },
  { href: '/config', label: 'Config', icon: Cog6ToothIcon },
  { href: '/agents', label: 'Agenten', icon: CpuChipIcon },
  { href: '/tasks', label: 'Tasks', icon: ClipboardDocumentListIcon },
] as const;

function isActivePath(pathname: string, href: string): boolean {
  if (href === '/') return pathname === '/';
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="relative z-10 flex min-h-screen bg-gray-900/40">
      <aside className="hidden w-64 flex-shrink-0 border-r border-gray-700/60 bg-gray-800/80 md:sticky md:top-0 md:flex md:h-screen md:flex-col">
        <div className="border-b border-gray-700/60 px-5 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-kirobi-600 text-sm font-bold text-white">
              K
            </div>
            <div>
              <p className="text-sm font-bold leading-tight text-white">Kirobi</p>
              <p className="text-xs leading-tight text-gray-500">Admin Dashboard</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = isActivePath(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                className={`nav-item w-full ${active ? 'nav-item-active' : 'nav-item-inactive'}`}
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-gray-700/60 px-4 py-4">
          <p className="text-xs text-gray-500">Zentrales Control Center für lokale Dienste, Agenten und Operator-Workflows.</p>
        </div>
      </aside>

      <main className="min-w-0 flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
