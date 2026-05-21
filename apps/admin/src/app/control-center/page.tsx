'use client'

import { useMemo, useState } from 'react'
import useSWR from 'swr'
import { motion } from 'framer-motion'
import {
  Bot,
  Brain,
  Copy,
  ExternalLink,
  Mic,
  Music4,
  Sparkles,
  Video,
  Wand2,
} from 'lucide-react'
import { ServiceBadge } from '@/components/ui/ServiceBadge'
import { StatCard } from '@/components/ui/StatCard'
import {
  copyText,
  formatRelativeTime,
  type ServiceProbe,
  resolveOpenPath,
  useControlStatus,
  useOllamaProcesses,
  useServiceHealthMatrix,
  withBasePath,
} from '@/lib/api'

type HeartMuLaStatus = {
  available?: boolean
  model_exists?: boolean
  message?: string
  model_path?: string
}

const HERMES_SERVICE_NAMES = ['hermes-runtime', 'hermes-samira-runtime', 'hermes-sineo-runtime']
const EXPERIENCE_SERVICE_NAMES = ['voice-processing', 'image-generation', 'music-generation', 'video-generation', 'media-processing']

const SURFACES = [
  { label: 'Kirobi Admin', href: '/admin', description: 'Operator panel ueber Caddy' },
  { label: 'User Portal', href: '/portal', description: 'Neue Benutzeroberflaeche mit Hermes OS' },
  { label: 'Family PWA', href: '/', description: 'Weboberflaeche fuer Chat, Search und Uploads' },
  { label: 'Dashboard', href: '/dashboard', description: 'Bestehendes Service-Dashboard' },
  { label: 'Voice App', href: '/voice-app/', description: 'Standalone Sprachoberflaeche' },
]

async function fetchHeartMuLa(): Promise<HeartMuLaStatus> {
  const response = await fetch(withBasePath('/api/proxy/music-generation/heartmula/status'), { cache: 'no-store' })
  if (!response.ok) {
    throw new Error('HeartMuLa status unavailable')
  }
  return response.json()
}

function resolveProbeMap(probes: ServiceProbe[]) {
  return new Map(probes.map((probe) => [probe.definition.name, probe]))
}

export default function ControlCenterPage() {
  const { data: probes = [] } = useServiceHealthMatrix()
  const { data: control } = useControlStatus()
  const { data: loadedModels = [] } = useOllamaProcesses()
  const { data: heartmula } = useSWR('admin-heartmula-status', fetchHeartMuLa, { refreshInterval: 15000 })
  const [toast, setToast] = useState<string | null>(null)

  const probeMap = useMemo(() => resolveProbeMap(probes), [probes])
  const hermesFleet = HERMES_SERVICE_NAMES.map((name) => probeMap.get(name)).filter(Boolean) as ServiceProbe[]
  const experienceStack = EXPERIENCE_SERVICE_NAMES.map((name) => probeMap.get(name)).filter(Boolean) as ServiceProbe[]
  const hermesOnline = hermesFleet.filter((probe) => probe.status === 'online').length
  const experienceOnline = experienceStack.filter((probe) => probe.status === 'online').length

  const handleCopy = async (value: string, label: string) => {
    const copied = await copyText(value)
    setToast(copied ? `${label} kopiert` : value)
    window.setTimeout(() => setToast(null), 2200)
  }

  return (
    <div className="space-y-6">
      <section className="panel grid-background overflow-hidden p-6">
        <div className="grid gap-6 xl:grid-cols-[1.25fr,0.75fr]">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-[var(--text-muted)]">OpenDisruption v0.1 operator surface</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-white">Hermes, Voicebox und Generative AI im selben Control Center</h1>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--text-secondary)]">
              Dieses Panel verbindet die drei persoenlichen Hermes-Instanzen mit Voice Processing, HeartMuLa sowie Bild-, Musik- und Video-Generierung ueber die bestehenden lokalen Services und Frontends.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <a href="/portal/os" className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-sm text-cyan-200">
                <ExternalLink className="h-4 w-4" />
                Portal Hermes OS
              </a>
              <a href="/dashboard/demo" className="inline-flex items-center gap-2 rounded-full border border-fuchsia-400/20 bg-fuchsia-400/10 px-4 py-2 text-sm text-fuchsia-200">
                <Sparkles className="h-4 w-4" />
                Demo Control View
              </a>
            </div>
          </div>

          <div className="rounded-3xl border border-white/5 bg-black/20 p-5">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Live operator notes</p>
            <div className="mt-4 space-y-3">
              <div className="rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-3 text-sm text-[var(--text-secondary)]">
                Hermes Fleet: {hermesOnline}/{hermesFleet.length} online
              </div>
              <div className="rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-3 text-sm text-[var(--text-secondary)]">
                Creative Stack: {experienceOnline}/{experienceStack.length} online
              </div>
              <div className="rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-3 text-sm text-[var(--text-secondary)]">
                HeartMuLa: {heartmula?.available ? 'bereit' : heartmula?.message ?? 'Status wird synchronisiert'}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Bot} title="Hermes runtimes" value={hermesOnline} subtitle={`${hermesFleet.length} persoenliche Instanzen`} accent="magenta" />
        <StatCard icon={Mic} title="Voice & media stack" value={experienceOnline} subtitle={`${experienceStack.length} Services im Control Center`} accent="cyan" />
        <StatCard icon={Brain} title="Loaded models" value={loadedModels.length} subtitle="Ollama VRAM usage live" accent="violet" />
        <StatCard icon={Sparkles} title="Attention tasks" value={control?.attentionRequired ?? 0} subtitle="Operator handoff / blocked items" accent="gold" />
      </section>

      {toast ? <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200">{toast}</div> : null}

      <section className="panel p-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Hermes fleet</p>
            <h2 className="mt-2 text-2xl font-semibold text-white">Persoenliche Hermes-Instanzen</h2>
          </div>
          <div className="text-sm text-[var(--text-secondary)]">Health + direkter Runtime-Zugang</div>
        </div>
        <div className="mt-5 grid gap-4 xl:grid-cols-3">
          {hermesFleet.map((probe) => (
            <motion.div key={probe.definition.name} whileHover={{ y: -2 }} className="rounded-3xl border border-white/5 bg-white/[0.03] p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-lg font-semibold text-white">{probe.definition.label}</p>
                  <p className="mt-2 text-sm leading-7 text-[var(--text-secondary)]">{probe.definition.description}</p>
                </div>
                <ServiceBadge status={probe.status} compact />
              </div>
              <div className="mt-4 text-xs text-[var(--text-muted)]">
                {probe.summary} · {formatRelativeTime(probe.checkedAt)}
              </div>
              <div className="mt-5 flex flex-wrap gap-2">
                {probe.definition.openPath ? (
                  <a href={resolveOpenPath(probe.definition.openPath)} className="inline-flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs font-medium text-cyan-200">
                    <ExternalLink className="h-3.5 w-3.5" />
                    Open
                  </a>
                ) : null}
                <button
                  type="button"
                  onClick={() => void handleCopy(probe.definition.restartCommand, probe.definition.label)}
                  className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200"
                >
                  <Copy className="h-3.5 w-3.5" />
                  Restart
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="panel p-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Voice + generative stack</p>
            <h2 className="mt-2 text-2xl font-semibold text-white">Heartmula, Voicebox und Medienservices</h2>
          </div>
          <div className="text-sm text-[var(--text-secondary)]">Lokal auf GPU / Operator health view</div>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {experienceStack.map((probe) => {
            const icon =
              probe.definition.name === 'voice-processing' ? Mic :
              probe.definition.name === 'image-generation' ? Wand2 :
              probe.definition.name === 'music-generation' ? Music4 :
              probe.definition.name === 'video-generation' ? Video :
              Sparkles

            const Icon = icon
            return (
              <motion.div key={probe.definition.name} whileHover={{ y: -2 }} className="rounded-3xl border border-white/5 bg-white/[0.03] p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-cyan-200">
                    <Icon className="h-5 w-5" />
                  </div>
                  <ServiceBadge status={probe.status} compact />
                </div>
                <p className="mt-4 text-lg font-semibold text-white">{probe.definition.label}</p>
                <p className="mt-2 text-sm leading-7 text-[var(--text-secondary)]">{probe.definition.description}</p>
                {probe.definition.name === 'music-generation' ? (
                  <div className="mt-4 rounded-2xl border border-white/5 bg-black/20 px-4 py-3 text-xs text-[var(--text-secondary)]">
                    HeartMuLa: {heartmula?.available ? 'verfuegbar' : heartmula?.message ?? 'wird geprueft'}
                  </div>
                ) : null}
                <div className="mt-4 flex flex-wrap gap-2">
                  {probe.definition.openPath ? (
                    <a href={resolveOpenPath(probe.definition.openPath)} className="inline-flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs font-medium text-cyan-200">
                      <ExternalLink className="h-3.5 w-3.5" />
                      Open
                    </a>
                  ) : null}
                  <button
                    type="button"
                    onClick={() => void handleCopy(probe.definition.restartCommand, probe.definition.label)}
                    className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200"
                  >
                    <Copy className="h-3.5 w-3.5" />
                    Restart
                  </button>
                </div>
              </motion.div>
            )
          })}
        </div>
      </section>

      <section className="panel p-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Frontend surfaces</p>
            <h2 className="mt-2 text-2xl font-semibold text-white">Admin, Portal und weitere lokale UIs</h2>
          </div>
          <div className="text-sm text-[var(--text-secondary)]">Caddy / Tailscale entry points</div>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {SURFACES.map((surface) => (
            <a key={surface.href} href={surface.href} className="rounded-3xl border border-white/5 bg-white/[0.03] p-5 transition hover:border-cyan-400/20 hover:bg-white/[0.05]">
              <p className="text-lg font-semibold text-white">{surface.label}</p>
              <p className="mt-2 text-sm leading-7 text-[var(--text-secondary)]">{surface.description}</p>
              <div className="mt-4 inline-flex items-center gap-2 text-sm text-cyan-200">
                Oeffnen
                <ExternalLink className="h-4 w-4" />
              </div>
            </a>
          ))}
        </div>
      </section>
    </div>
  )
}
