'use client'

import { Activity, Bot, Brain, Database, Layers3, Server, ShieldCheck, Sparkles } from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard'
import { ServiceBadge } from '@/components/ui/ServiceBadge'
import {
  AGENT_PROFILES,
  formatNumber,
  formatRelativeTime,
  titleCase,
  ServiceProbe,
  useAnalyticsStats,
  useControlStatus,
  useDashboardActivity,
  useOllamaProcesses,
  useOllamaTags,
  useServiceHealthMatrix,
} from '@/lib/api'

const HIGHLIGHTED_SERVICES = ['api', 'auth', 'analytics', 'ollama', 'model-routing', 'qdrant', 'supervisor', 'retrieval']

export default function OverviewPage() {
  const { data: probes = [] } = useServiceHealthMatrix()
  const { data: analytics } = useAnalyticsStats()
  const { data: control } = useControlStatus()
  const { data: activity = [] } = useDashboardActivity(8)
  const { data: models = [] } = useOllamaTags()
  const { data: loadedModels = [] } = useOllamaProcesses()

  const probeMap = new Map(probes.map((probe) => [probe.definition.name, probe]))
  const highlighted = HIGHLIGHTED_SERVICES.map((name) => probeMap.get(name)).filter(Boolean) as ServiceProbe[]
  const onlineCount = probes.filter((probe) => probe.status === 'online').length
  const degradedCount = probes.filter((probe) => probe.status === 'degraded').length

  return (
    <div className="space-y-6">
      <section className="panel grid-background overflow-hidden p-6">
        <div className="grid gap-6 xl:grid-cols-[1.45fr,0.85fr]">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-[var(--text-muted)]">Operator overview</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-white">System dashboard for OpenDisruption control</h1>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--text-secondary)]">
              Live control surface for service health, queue pressure, model availability and the current agent constellation on <span className="text-cyan-200">kirobi-net</span>.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1.5 text-sm text-cyan-200">
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-cyan-300 shadow-glow-cyan">
                  <span className="absolute inset-0 rounded-full bg-cyan-300/70 animate-ping" />
                </span>
                {onlineCount}/{probes.length || 0} surfaces online
              </div>
              <div className="inline-flex items-center gap-2 rounded-full border border-fuchsia-400/20 bg-fuchsia-400/10 px-3 py-1.5 text-sm text-fuchsia-200">
                <Bot className="h-4 w-4" />
                {AGENT_PROFILES.length} managed agents
              </div>
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-slate-200">
                <Activity className="h-4 w-4" />
                {control?.autonomousMode ?? 'local-only-deterministic'}
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-white/5 bg-black/20 p-5">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Operator guidance</p>
            <div className="mt-4 space-y-3">
              {(control?.operatorGuidance ?? ['Loading local operator guidance…']).slice(0, 4).map((item) => (
                <div key={item} className="rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-3 text-sm text-[var(--text-secondary)]">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Server} title="Online services" value={onlineCount} change={`${degradedCount} degraded`} accent="cyan" />
        <StatCard icon={Activity} title="Events today" value={analytics?.eventsToday ?? 0} subtitle="Analytics /stats" accent="magenta" />
        <StatCard icon={Layers3} title="Queue depth" value={control?.queueDepth ?? 0} subtitle={`${control?.attentionRequired ?? 0} need attention`} accent="gold" />
        <StatCard icon={Brain} title="Installed models" value={models.length} subtitle={`${loadedModels.length} currently loaded`} accent="violet" />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.25fr,0.75fr]">
        <div className="panel p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Core health grid</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Critical services</h2>
            </div>
            <div className="text-sm text-[var(--text-secondary)]">Auto-refresh 15s</div>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {highlighted.map((probe) => (
              <div key={probe.definition.name} className="rounded-2xl border border-white/5 bg-white/[0.03] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-white">{probe.definition.label}</p>
                    <p className="mt-1 text-xs text-[var(--text-secondary)]">{probe.summary}</p>
                  </div>
                  <ServiceBadge status={probe.status} compact />
                </div>
                <div className="mt-4 flex items-center justify-between text-xs text-[var(--text-muted)]">
                  <span>{probe.latencyMs ? `${probe.latencyMs} ms` : '—'}</span>
                  <span>{formatRelativeTime(probe.checkedAt)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Model live state</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Loaded runtimes</h2>
            </div>
            <Sparkles className="h-5 w-5 text-fuchsia-300" />
          </div>
          <div className="mt-5 space-y-3">
            {(loadedModels.length ? loadedModels : models.slice(0, 4)).map((model) => (
              <div key={model.name} className="rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-white">{model.name}</p>
                    <p className="mt-1 text-xs text-[var(--text-secondary)]">
                      {'size_vram' in model ? `${formatNumber(Math.round((model.size_vram ?? 0) / (1024 * 1024)))} MB VRAM` : `${formatNumber(Math.round((model.size ?? 0) / (1024 * 1024)))} MB package`}
                    </p>
                  </div>
                  <ServiceBadge status={loadedModels.some((entry) => entry.name === model.name) ? 'online' : 'degraded'} compact />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
        <div className="panel p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Recent events</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Supervisor & activity feed</h2>
            </div>
            <Database className="h-5 w-5 text-violet-300" />
          </div>
          <div className="mt-5 space-y-3">
            {(control?.recentEvents.length ? control.recentEvents.map((event) => ({ id: `${event.timestamp}-${event.event_type}`, title: event.event_type, message: event.message, time: event.timestamp })) : activity.map((item) => ({ id: item.id, title: item.surface, message: item.summary, time: item.created_at }))).slice(0, 6).map((entry) => (
              <div key={entry.id} className="rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-white">{titleCase(entry.title)}</p>
                  <span className="text-xs text-[var(--text-muted)]">{formatRelativeTime(entry.time)}</span>
                </div>
                <p className="mt-2 text-sm text-[var(--text-secondary)]">{entry.message}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="panel p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Agent constellation</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Active agents</h2>
            </div>
            <ShieldCheck className="h-5 w-5 text-cyan-300" />
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {AGENT_PROFILES.map((agent) => {
              const runtimeStatus = probeMap.get(agent.runtimeService ?? 'supervisor')?.status ?? 'unknown'
              const lastActive = activity.find((item) => item.summary.toLowerCase().includes(agent.name.toLowerCase()) || item.actor.toLowerCase().includes(agent.name.toLowerCase()))?.created_at ?? control?.lastEventAt
              return (
                <div key={agent.id} className="rounded-2xl border border-white/5 bg-white/[0.03] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-xl">{agent.emoji}</div>
                      <div>
                        <p className="text-sm font-medium text-white">{agent.name}</p>
                        <p className="mt-1 text-xs text-[var(--text-secondary)]">{agent.model}</p>
                      </div>
                    </div>
                    <ServiceBadge status={runtimeStatus} compact />
                  </div>
                  <p className="mt-3 text-sm text-[var(--text-secondary)]">{agent.persona}</p>
                  <p className="mt-3 text-xs text-[var(--text-muted)]">Last activity {formatRelativeTime(lastActive)}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>
    </div>
  )
}
