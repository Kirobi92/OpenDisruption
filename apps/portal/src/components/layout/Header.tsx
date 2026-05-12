'use client';

import Link from 'next/link';
import { Mic, UserRound } from 'lucide-react';

import { useAuth } from '@/lib/auth';

export function Header({ title }: { title: string }) {
  const { user } = useAuth();
  const initials = user?.displayName?.slice(0, 2).toUpperCase() ?? 'KI';

  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b border-white/10 bg-void/75 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 md:px-6">
        <Link
          href="/"
          className="bg-gradient-to-r from-kirobi-300 via-aurora-cyan to-aurora-violet bg-clip-text text-lg font-black tracking-[0.28em] text-transparent"
        >
          KIROBI
        </Link>

        <div className="absolute left-1/2 -translate-x-1/2 text-sm font-semibold text-white/90">{title}</div>

        <div className="flex items-center gap-2">
          <Link
            href="/voice"
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-white/80 transition hover:border-aurora-cyan/40 hover:text-aurora-cyan"
            aria-label="Sprachmodus öffnen"
          >
            <Mic className="h-4 w-4" />
          </Link>
          <Link
            href="/profile"
            className="inline-flex h-10 w-10 items-center justify-center overflow-hidden rounded-full border border-white/10 bg-gradient-to-br from-kirobi-500 to-aurora-violet text-xs font-semibold text-white shadow-glow-cyan"
            aria-label="Profil öffnen"
          >
            {user ? initials : <UserRound className="h-4 w-4" />}
          </Link>
        </div>
      </div>
    </header>
  );
}
