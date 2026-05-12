'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Brain, Goal, Home, MessageSquare, Sparkles } from 'lucide-react';

const items = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/brain', label: 'Gehirn', icon: Brain },
  { href: '/media', label: 'Medien', icon: Sparkles },
  { href: '/goals', label: 'Ziele', icon: Goal },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-50 border-t border-white/10 bg-void/80 backdrop-blur-xl md:hidden">
      <div className="mx-auto flex h-16 max-w-xl items-center justify-around px-2">
        {items.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;

          return (
            <Link
              key={href}
              href={href}
              className={`flex min-w-14 flex-col items-center justify-center gap-1 rounded-2xl px-3 py-2 text-xs transition ${
                isActive ? 'text-aurora-cyan' : 'text-white/55 hover:text-white'
              }`}
            >
              <Icon className={`h-5 w-5 ${isActive ? 'drop-shadow-[0_0_12px_rgba(94,234,212,0.55)]' : ''}`} />
              <span className="font-medium">{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
