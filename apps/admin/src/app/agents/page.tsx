'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Bot, Cpu, ShieldAlert, Sparkles } from 'lucide-react'
import { AgentCard } from '@/components/agents/AgentCard'
import { StatCard } from '@/components/ui/StatCard'
import {
  AGENT_PROFILES,
  ServiceState,
  copyText,
  useControlStatus,
  useDashboardActivity,
  useServiceHealthMatrix,
} from '@/lib/api'

const STORAGE_KEY = 'kirobi-admin-agent-state'

export default function AgentsPage() {
  const router = useRouter()
  const { data: probes = [] } = useServiceHealthMatrix()
  const { data: control } = useControlStatus()
  const { data: activity = [] } = useDashboardActivity(16)
  const [activeMap, setActiveMap] = useState<Record<string, boolean>>({})
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (saved) {
      setActiveMap(JSON.parse(saved) as Record<string, boolean>)
      return
    }
    setActiveMap(Object.fromEntries(AGENT_PROFILES.map((agent) => [agent.id, agent.defaultActive])))
  }, [])

  useEffect(() => {
    if (Object.keys(activeMap).length) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(activeMap))
    }
  }, [activeMap])

  useEffect(() => {
    if (!toast) return
    const timeout = window.setTimeout(() => setToast(null), 2200)
    return () => window.clearTimeout(timeout)
  }, [toast])

  const probeMap = new Map(probes.map((probe) => [probe.definition.name, probe.status]))
  const activeCount = AGENT_PROFILES.filter((agent) => activeMap[agent.id] ?? agent.defaultActive).length
  const onlineRuntimeCount = AGENT_PROFILES.filter((agent) => (probeMap.get(agent.runtimeService ?? 'supervisor') ?? 'unknown') === 'online').length

  const resolveLastActive = (name: string) => {
    return activity.find((item) => item.summary.toLowerCase().includes(name.toLowerCase()) || item.actor.toLowerCase().includes(name.toLowerCase()))?.created_at ?? control?.lastEventAt
  }

  const attentionAgents = useMemo(() => new Set((control?.attentionTasks ?? []).map((task) => task.agent).filter(Boolean)), [control])

  const handleAction = async (action: 'chat' | 'configure', agent: (typeof AGENT_PROFILES)[number]) => {
    if (action === 'configure') {
      router.push('/settings')
      return
    }

    const command = `Open ${agent.name} via ${agent.runtimeService === 'nutzi' ? 'Nutzi UI' : 'Open WebUI / Hermes'}`
    const copied = await copyText(command)
    setToast(copied ? `${agent.name} handoff copied` : command)
  }

  return (
    <div className="space-y-6">
      <section className="panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Agent fleet</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">Hermes agent control</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--text-secondary)]">
          Hardcoded personas with live runtime state, last known activity and local active/inactive toggles until a dedicated agents endpoint lands.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Bot} title="Managed agents" value={AGENT_PROFILES.length} subtitle="Architect → Nutzi" accent="magenta" />
        <StatCard icon={Cpu} title="Active toggles" value={activeCount} subtitle="Persisted in local storage" accent="cyan" />
        <StatCard icon={Sparkles} title="Online runtimes" value={onlineRuntimeCount} subtitle="Supervisor + dedicated services" accent="violet" />
        <StatCard icon={ShieldAlert} title="Attention tasks" value={control?.attentionRequired ?? 0} subtitle="Human-gated or blocked" accent="gold" />
      </section>

      {toast ? <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200">{toast}</div> : null}

      <section className="grid gap-4 xl:grid-cols-2">
        {AGENT_PROFILES.map((agent) => {
          const runtimeStatus = (probeMap.get(agent.runtimeService ?? 'supervisor') ?? 'unknown') as ServiceState
          const active = activeMap[agent.id] ?? agent.defaultActive
          return (
            <div key={agent.id} className={attentionAgents.has(agent.id) ? 'ring-1 ring-amber-400/30 rounded-[1.4rem]' : undefined}>
              <AgentCard
                agent={agent}
                runtimeStatus={runtimeStatus}
                lastActive={resolveLastActive(agent.name)}
                active={active}
                onToggle={(next) => setActiveMap((current) => ({ ...current, [agent.id]: next }))}
                onAction={handleAction}
              />
            </div>
          )
        })}
      </section>
    </div>
  )
}
