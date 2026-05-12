'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import type { LucideIcon } from 'lucide-react'
import {
  Bot,
  BrainCircuit,
  ChartSpline,
  ChevronLeft,
  ChevronRight,
  Database,
  LayoutDashboard,
  ServerCog,
  Settings2,
  ShieldCheck,
  Users,
} from 'lucide-react'
import { NAV_ITEMS, formatRelativeTime, useControlStatus } from '@/lib/api'

const STORAGE_KEY = 'kirobi-admin-sidebar'

const ICONS: Record<string, LucideIcon> = {
  '/': LayoutDashboard,
  '/agents': Bot,
  '/models': BrainCircuit,
  '/knowledge': Database,
  '/services': ServerCog,
  '/analytics': ChartSpline,
  '/users': Users,
  '/settings': Settings2,
}

function isActive(pathname: string, href: string) {
  if (href === '/') return pathname === '/'
  return pathname.startsWith(href)
}

export function Sidebar() {
  const pathname = usePathname()
  const { data: control } = useControlStatus()
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    setCollapsed(saved === 'collapsed')
  }, [])

  const footerText = useMemo(() => {
    if (!control) return 'Uptime wird synchronisiert'
    return `Last heartbeat ${formatRelativeTime(control.lastHealthCheckAt ?? control.lastEventAt)}`
  }, [control])

  const toggle = () => {
    const next = !collapsed
    setCollapsed(next)
    window.localStorage.setItem(STORAGE_KEY, next ? 'collapsed' : 'expanded')
  }

  return (
    <>
      <aside
        className={`glass-raised sticky top-0 hidden h-screen flex-col border-r border-white/5 px-3 py-4 transition-all duration-300 lg:flex ${collapsed ? 'w-24' : 'w-80'}`}
      >
        <div className="mb-6 flex items-center justify-between gap-3 px-2">
          <div className={`min-w-0 transition-all ${collapsed ? 'opacity-0' : 'opacity-100'}`}>
            <p className="text-[11px] uppercase tracking-[0.35em] text-[var(--text-muted)]">Local-first control</p>
            <h1 className="mt-1 truncate text-lg font-semibold tracking-[0.08em] text-gradient-aurora">KIROBI ADMIN</h1>
          </div>
          <button
            type="button"
            onClick={toggle}
            className="rounded-2xl border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:border-cyan-400/30 hover:text-white"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        <nav className="flex-1 space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const Icon = ICONS[item.href]
            const active = isActive(pathname, item.href)

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-3 rounded-2xl border px-3 py-3 transition-all ${
                  active
                    ? 'border-cyan-400/20 bg-cyan-400/10 text-cyan-200 shadow-glow-cyan'
                    : 'border-transparent text-slate-300 hover:border-white/10 hover:bg-white/5 hover:text-white'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
                  <Icon className="h-4 w-4" />
                </span>
                {!collapsed ? (
                  <span className="min-w-0">
                    <span className="block text-sm font-medium">{item.label}</span>
                    <span className="mt-0.5 block truncate text-xs text-[var(--text-muted)]">{item.description}</span>
                  </span>
                ) : null}
              </Link>
            )
          })}
        </nav>

        <div className="mt-6 rounded-2xl border border-white/5 bg-white/[0.03] p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-400/15 bg-cyan-400/10 text-cyan-200 shadow-card">
              <ShieldCheck className="h-5 w-5" />
            </div>
            {!collapsed ? (
              <div className="min-w-0">
                <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Version</p>
                <p className="mt-1 text-sm font-medium text-white">v1.0.0 · Admin</p>
                <p className="mt-1 text-xs text-[var(--text-secondary)]">{footerText}</p>
              </div>
            ) : null}
          </div>
        </div>
      </aside>

      <nav className="glass fixed inset-x-4 bottom-4 z-30 rounded-2xl border border-white/10 px-3 py-2 lg:hidden">
        <div className="flex items-center justify-between gap-2">
          {NAV_ITEMS.map((item) => {
            const Icon = ICONS[item.href]
            const active = isActive(pathname, item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-1 flex-col items-center justify-center rounded-xl px-2 py-2 text-[11px] ${
                  active ? 'bg-cyan-400/10 text-cyan-200' : 'text-slate-300'
                }`}
              >
                <Icon className="mb-1 h-4 w-4" />
                {item.label}
              </Link>
            )
          })}
        </div>
      </nav>
    </>
  )
}
