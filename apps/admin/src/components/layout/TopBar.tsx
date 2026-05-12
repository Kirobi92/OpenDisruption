'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { BellRing, Command, HeartPulse, RefreshCw, Search, ShieldCheck, X } from 'lucide-react'
import { NAV_ITEMS, SERVICE_DEFINITIONS, copyText, titleCase, useServiceHealthMatrix } from '@/lib/api'

type CommandTarget = {
  id: string
  title: string
  subtitle: string
  href: string
  external?: boolean
}

function breadcrumbFromPath(pathname: string) {
  const parts = pathname.split('/').filter(Boolean)
  if (!parts.length) return ['Overview']
  return ['Overview', ...parts.map(titleCase)]
}

export function TopBar() {
  const pathname = usePathname()
  const router = useRouter()
  const { data: probes = [] } = useServiceHealthMatrix()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() == 'k') {
        event.preventDefault()
        setOpen(true)
      }
      if (event.key === 'Escape') setOpen(false)
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  useEffect(() => {
    if (!toast) return
    const timeout = window.setTimeout(() => setToast(null), 2400)
    return () => window.clearTimeout(timeout)
  }, [toast])

  const onlineCount = probes.filter((probe) => probe.status === 'online').length
  const totalCount = probes.length
  const healthTone = totalCount === 0 ? 'unknown' : onlineCount === totalCount ? 'online' : onlineCount >= Math.max(1, totalCount * 0.65) ? 'degraded' : 'offline'

  const commandTargets = useMemo<CommandTarget[]>(() => {
    const pages = NAV_ITEMS.map((item) => ({
      id: item.href,
      title: item.label,
      subtitle: item.description,
      href: item.href,
      external: false,
    }))

    const surfaces = SERVICE_DEFINITIONS.filter((service) => service.openPath).map((service) => ({
      id: service.name,
      title: `Open ${service.label}`,
      subtitle: service.description,
      href: service.openPath as string,
      external: true,
    }))

    const normalized = query.trim().toLowerCase()
    return [...pages, ...surfaces].filter((target) => {
      if (!normalized) return true
      return `${target.title} ${target.subtitle}`.toLowerCase().includes(normalized)
    })
  }, [query])

  const copyCommand = async (label: string, command: string) => {
    const success = await copyText(command)
    setToast(success ? `${label} command copied` : command)
  }

  const healthClasses = {
    online: 'bg-emerald-400 shadow-[0_0_18px_rgba(74,222,128,0.65)]',
    degraded: 'bg-amber-400 shadow-[0_0_18px_rgba(251,191,36,0.55)]',
    offline: 'bg-red-400 shadow-[0_0_18px_rgba(248,113,113,0.55)]',
    unknown: 'bg-slate-400 shadow-[0_0_18px_rgba(148,163,184,0.45)]',
  } as const

  return (
    <>
      <header className="sticky top-0 z-20 border-b border-white/5 bg-[#040614]/80 backdrop-blur-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div>
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
              {breadcrumbFromPath(pathname).map((part, index, list) => (
                <span key={`${part}-${index}`} className="flex items-center gap-2">
                  <span>{part}</span>
                  {index < list.length - 1 ? <span className="text-white/20">/</span> : null}
                </span>
              ))}
            </div>
            <h2 className="mt-1 text-lg font-semibold text-white">{NAV_ITEMS.find((item) => item.href === pathname)?.label ?? titleCase(pathname.replace('/', '') || 'overview')}</h2>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 transition hover:border-cyan-400/25 hover:text-white"
            >
              <Search className="h-4 w-4" />
              <span className="hidden sm:inline">Search surfaces</span>
              <span className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-black/20 px-2 py-1 text-[11px] text-[var(--text-muted)]">
                <Command className="h-3 w-3" />K
              </span>
            </button>

            <div className="hidden items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 md:flex">
              <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${healthClasses[healthTone]}`}>
                <span className={`absolute inset-0 rounded-full ${healthClasses[healthTone]} animate-ping opacity-35`} />
              </span>
              <span>{onlineCount}/{totalCount || 0} services live</span>
            </div>

            <button
              type="button"
              onClick={() => copyCommand('Restart Hermes', 'docker compose restart supervisor hermes-runtime')}
              className="inline-flex items-center gap-2 rounded-2xl border border-fuchsia-400/20 bg-fuchsia-400/10 px-3 py-2 text-xs font-medium text-fuchsia-200 transition hover:border-fuchsia-300/30"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Restart hermes
            </button>
            <button
              type="button"
              onClick={() => copyCommand('Clear sessions', 'docker compose exec postgres psql -U kirobi -d kirobi -c "DELETE FROM sessions;"')}
              className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-cyan-400/25"
            >
              <BellRing className="h-3.5 w-3.5" />
              Clear sessions
            </button>
            <button
              type="button"
              onClick={() => copyCommand('Trigger backup', 'bash infra/scripts/backup.sh --dry-run')}
              className="inline-flex items-center gap-2 rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs font-medium text-cyan-200 transition hover:border-cyan-300/35"
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              Trigger backup
            </button>
          </div>
        </div>
        {toast ? (
          <div className="border-t border-white/5 px-4 py-2 text-xs text-cyan-200 sm:px-6 lg:px-8">{toast}</div>
        ) : null}
      </header>

      {open ? (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 px-4 py-12 backdrop-blur-sm">
          <div className="glass-raised w-full max-w-2xl rounded-3xl border border-white/10 p-4">
            <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              <Search className="h-4 w-4 text-[var(--text-secondary)]" />
              <input
                autoFocus
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search pages or openable surfaces"
                className="w-full bg-transparent text-sm text-white placeholder:text-[var(--text-muted)] focus:outline-none"
              />
              <button type="button" onClick={() => setOpen(false)} className="rounded-xl border border-white/10 p-2 text-slate-300 transition hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-4 max-h-[60vh] space-y-2 overflow-y-auto pr-1">
              {commandTargets.map((target) => (
                <button
                  key={target.id}
                  type="button"
                  onClick={() => {
                    if (target.external) {
                      window.open(target.href, '_blank', 'noopener,noreferrer')
                    } else {
                      router.push(target.href)
                    }
                    setOpen(false)
                    setQuery('')
                  }}
                  className="w-full rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-3 text-left transition hover:border-cyan-400/20 hover:bg-cyan-400/5"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-white">{target.title}</p>
                      <p className="mt-1 text-xs text-[var(--text-secondary)]">{target.subtitle}</p>
                    </div>
                    {target.external ? <HeartPulse className="h-4 w-4 text-fuchsia-300" /> : <Command className="h-4 w-4 text-cyan-300" />}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </>
  )
}
