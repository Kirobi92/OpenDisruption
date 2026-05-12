'use client'

import { motion } from 'framer-motion'
import { MessageSquare, Power, Settings2 } from 'lucide-react'
import { AgentProfile, formatRelativeTime, ServiceState } from '@/lib/api'
import { ServiceBadge } from '@/components/ui/ServiceBadge'

export function AgentCard({
  agent,
  runtimeStatus,
  lastActive,
  active,
  onToggle,
  onAction,
}: {
  agent: AgentProfile
  runtimeStatus: ServiceState
  lastActive?: string | null
  active: boolean
  onToggle: (next: boolean) => void
  onAction: (action: 'chat' | 'configure', agent: AgentProfile) => void
}) {
  return (
    <motion.div whileHover={{ y: -2 }} className="panel p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-2xl shadow-card">
            <span>{agent.emoji}</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-white">{agent.name}</h3>
              <ServiceBadge status={runtimeStatus} compact />
            </div>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">{agent.model}</p>
            <p className="mt-2 max-w-xl text-sm text-[var(--text-secondary)]">{agent.persona}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => onToggle(!active)}
          className={`inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-medium transition ${
            active
              ? 'border-cyan-400/30 bg-cyan-400/10 text-cyan-200'
              : 'border-white/10 bg-white/5 text-slate-300'
          }`}
        >
          <Power className="h-3.5 w-3.5" />
          {active ? 'Active' : 'Inactive'}
        </button>
      </div>

      <p className="mt-4 text-sm text-[var(--text-secondary)]">{agent.description}</p>

      <div className="mt-4 flex flex-wrap gap-2">
        {agent.skills.map((skill) => (
          <span key={skill} className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-300">
            {skill}
          </span>
        ))}
      </div>

      <div className="mt-5 flex items-center justify-between gap-3 border-t border-white/5 pt-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--text-muted)]">Last active</p>
          <p className="mt-1 text-sm text-white">{formatRelativeTime(lastActive)}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onAction('chat', agent)}
            className="inline-flex items-center gap-2 rounded-xl border border-fuchsia-400/20 bg-fuchsia-400/10 px-3 py-2 text-xs font-medium text-fuchsia-200 transition hover:border-fuchsia-300/35"
          >
            <MessageSquare className="h-3.5 w-3.5" />
            Chat
          </button>
          <button
            type="button"
            onClick={() => onAction('configure', agent)}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-cyan-400/30"
          >
            <Settings2 className="h-3.5 w-3.5" />
            Configure
          </button>
        </div>
      </div>
    </motion.div>
  )
}
