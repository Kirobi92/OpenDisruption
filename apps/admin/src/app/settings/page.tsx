'use client'

import { useEffect, useMemo, useState } from 'react'
import { HardDriveDownload, Info, MessageSquareLock, Sparkles } from 'lucide-react'
import { copyText, useControlStatus, useModelRouting, useServiceHealthMatrix } from '@/lib/api'

export default function SettingsPage() {
  const { data: routing } = useModelRouting()
  const { data: control } = useControlStatus()
  const { data: probes = [] } = useServiceHealthMatrix()
  const [environment, setEnvironment] = useState<{ platform: string; language: string; origin: string }>({
    platform: 'server',
    language: 'de-DE',
    origin: 'local',
  })
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    setEnvironment({
      platform: navigator.platform,
      language: navigator.language,
      origin: window.location.origin,
    })
  }, [])

  useEffect(() => {
    if (!toast) return
    const timeout = window.setTimeout(() => setToast(null), 2200)
    return () => window.clearTimeout(timeout)
  }, [toast])

  const telegramStatus = probes.find((probe) => probe.definition.name === 'telegram')?.status ?? 'unknown'
  const healthyServices = probes.filter((probe) => probe.status === 'online').length
  const routingRules = Object.entries(routing?.routing_table ?? {})

  const settingCards = useMemo(
    () => [
      {
        title: 'Telegram bot status',
        value: telegramStatus,
        description: 'Zone-gated local bridge. Phase 5 remains gated until Phase 4 is green.',
        command: 'docker compose restart telegram',
        icon: MessageSquareLock,
      },
      {
        title: 'Memory provider',
        value: 'Qdrant + Postgres',
        description: 'Filesystem remains source of truth; indices stay rebuildable.',
        command: 'python3 infra/scripts/init-qdrant.py --dry-run',
        icon: Sparkles,
      },
      {
        title: 'Backup config',
        value: 'Dry-run first',
        description: 'infra/scripts/backup.sh captures canon, experiences, extracts, sacred, .env, Postgres and Qdrant.',
        command: 'bash infra/scripts/backup.sh --dry-run',
        icon: HardDriveDownload,
      },
      {
        title: 'Environment info',
        value: environment.platform,
        description: `${environment.language} · ${environment.origin} · ${healthyServices}/${probes.length || 0} services online`,
        command: 'python -m kirobi_core status --json',
        icon: Info,
      },
    ],
    [environment, healthyServices, probes.length, telegramStatus],
  )

  return (
    <div className="space-y-6">
      <section className="panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Settings</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">System configuration snapshot</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--text-secondary)]">
          Local defaults for models, Telegram, memory, backups and runtime environment. This surface stays read-only and emits safe command helpers.
        </p>
      </section>

      {toast ? <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200">{toast}</div> : null}

      <section className="grid gap-4 xl:grid-cols-2">
        {settingCards.map((card) => {
          const Icon = card.icon
          return (
            <div key={card.title} className="panel p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-cyan-200">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-white">{card.title}</p>
                    <p className="mt-1 text-sm text-[var(--text-secondary)]">{card.value}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={async () => setToast((await copyText(card.command)) ? `${card.title} command copied` : card.command)}
                  className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs font-medium text-cyan-200 transition hover:border-cyan-300/35"
                >
                  Copy command
                </button>
              </div>
              <p className="mt-4 text-sm leading-7 text-[var(--text-secondary)]">{card.description}</p>
            </div>
          )
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr,1fr]">
        <div className="panel p-6">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Default models</p>
          <h2 className="mt-2 text-xl font-semibold text-white">Routing defaults</h2>
          <div className="mt-5 space-y-3">
            {routingRules.map(([taskType, rule]) => (
              <div key={taskType} className="rounded-2xl border border-white/5 bg-white/[0.03] p-4">
                <p className="text-sm font-medium text-white">{taskType}</p>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <div className="rounded-2xl border border-cyan-400/15 bg-cyan-400/10 px-3 py-2 text-sm text-cyan-100">
                    <p className="text-[11px] uppercase tracking-[0.2em] text-cyan-300/80">Primary</p>
                    <p className="mt-1">{rule.primary}</p>
                  </div>
                  <div className="rounded-2xl border border-fuchsia-400/15 bg-fuchsia-400/10 px-3 py-2 text-sm text-fuchsia-100">
                    <p className="text-[11px] uppercase tracking-[0.2em] text-fuchsia-300/80">Fallback</p>
                    <p className="mt-1">{rule.fallback}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel p-6">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Runtime guards</p>
          <h2 className="mt-2 text-xl font-semibold text-white">Operational defaults</h2>
          <div className="mt-5 space-y-3">
            {[
              `Autonomous mode: ${control?.autonomousMode ?? 'local-only-deterministic'}`,
              `Human gates: ${(control?.humanGateZones ?? ['FAMILY_PRIVATE', 'QUARANTINE', 'SACRED']).join(', ')}`,
              'Network: kirobi-net with Docker DNS and same-origin proxy routes.',
              'Admin port: 3005 with standalone output and local-only glass UI.',
            ].map((line) => (
              <div key={line} className="rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-3 text-sm text-[var(--text-secondary)]">
                {line}
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
