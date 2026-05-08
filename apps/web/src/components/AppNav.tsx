'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ChatBubbleLeftRightIcon,
  CloudArrowUpIcon,
  MagnifyingGlassIcon,
  Cog6ToothIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

const NAV_ITEMS = [
  { href: '/chat', label: 'Chat', icon: ChatBubbleLeftRightIcon },
  { href: '/search', label: 'Suche', icon: MagnifyingGlassIcon },
  { href: '/knowledge-graph', label: 'Graph', icon: SparklesIcon },
  { href: '/upload', label: 'Upload', icon: CloudArrowUpIcon },
  { href: '/settings', label: 'Einstellungen', icon: Cog6ToothIcon },
];

/**
 * AppNav — Bottom-Navigation für mobile Geräte, Top-Bar für Desktop.
 * Wird nur angezeigt, wenn der User eingeloggt ist (kein Token → kein Nav).
 */
export default function AppNav() {
  const pathname = usePathname();

  // Kein Nav auf der Login-Seite
  if (pathname === '/') return null;

  return (
    <>
      {/* Desktop Top-Bar */}
      <nav className="hidden md:flex items-center justify-between bg-gray-800 border-b border-gray-700 px-6 py-3">
        <Link href="/chat" className="text-lg font-bold text-white hover:text-kirobi-400 transition-colors">
          Kirobi
        </Link>
        <div className="flex items-center space-x-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? 'bg-kirobi-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Mobile Bottom-Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-gray-800 border-t border-gray-700 safe-area-inset-bottom">
        <div className="flex items-center justify-around px-2 py-2">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex flex-col items-center space-y-1 px-3 py-2 rounded-lg transition-colors min-w-0 ${
                  active ? 'text-kirobi-400' : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                <Icon className={`w-6 h-6 ${active ? 'text-kirobi-400' : ''}`} />
                <span className="text-xs truncate">{label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
