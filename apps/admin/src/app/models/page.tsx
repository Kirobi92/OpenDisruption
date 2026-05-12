'use client'

import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { useSWRConfig } from 'swr'
import { BrainCircuit, Cpu, Layers3, PlayCircle, StopCircle } from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard'
import { ServiceBadge } from '@/components/ui/ServiceBadge'
import { formatBytes, formatRelativeTime, titleCase, useModelRouting, useOllamaProcesses, useOllamaTags } from '@/lib/api'

export default function ModelsPage() {
  const { mutate } = useSWRConfig()
  const { data: tags = [] } = useOllamaTags()
  const { data: running = [] } = useOllamaProcesses()
  const { data: routing } = useModelRouting()
  const [pendingModel, setPendingModel] = useState<string | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    if (!toast) return
    const timeout = window.setTimeout(() => setToast(null), 2200)
    return () => window.clearTimeout(timeout)
  }, [toast])

  const loadedSet = new Set(running.map((model) => model.name))
  const routingRules = Object.entries(routing?.routing_table ?? {})
  const primaryModelsAvailable = routingRules.filter(([, rule]) => tags.some((model) => model.name === rule.primary)).length

  const handleModelAction = async (modelName: string, action: 'start' | 'stop') => {
    setPendingModel(modelName)
    try {
      await axios.post(
        '/api/proxy/ollama/api/generate',
        {
          model: modelName,
          prompt: ' ',
          stream: false,
          keep_alive: action === 'start' ? '15m' : 0,
        },
        { timeout: 15000 },
      )
      await Promise.all([mutate('ollama-processes'), mutate('ollama-tags')])
      setToast(action === 'start' ? `${modelName} warmed` : `${modelName} unloaded`)
    } catch (error) {
      setToast(error instanceof Error ? error.message : `Action failed for ${modelName}`)
    } finally {
      setPendingModel(null)
    }
  }

  const installedFamilies = useMemo(() => new Set(tags.map((model) => model.details?.family).filter(Boolean)).size, [tags])

  return (
    <div className="space-y-6">
      <section className="panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Model runtime</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">Ollama models & routing</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--text-secondary)]">
          Installed Ollama models, loaded runtime processes and the active primary/fallback matrix from the model-routing service.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={BrainCircuit} title="Installed" value={tags.length} subtitle="/api/tags" accent="magenta" />
        <StatCard icon={Cpu} title="Loaded now" value={running.length} subtitle="/api/ps" accent="cyan" />
        <StatCard icon={Layers3} title="Routing rules" value={routingRules.length} subtitle={`${primaryModelsAvailable} primaries ready`} accent="violet" />
        <StatCard icon={BrainCircuit} title="Families" value={installedFamilies} subtitle="Model families detected" accent="gold" />
      </section>

      {toast ? <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200">{toast}</div> : null}

      <section className="grid gap-6 xl:grid-cols-[0.8fr,1.2fr]">
        <div className="panel p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Routing config</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Primary & fallback map</h2>
            </div>
            <ServiceBadge status={routing ? 'online' : 'unknown'} compact />
          </div>
          <div className="mt-5 space-y-3">
            {routingRules.map(([taskType, rule]) => {
              const primaryReady = tags.some((model) => model.name === rule.primary)
              const fallbackReady = tags.some((model) => model.name === rule.fallback)
              return (
                <div key={taskType} className="rounded-2xl border border-white/5 bg-white/[0.03] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-white">{titleCase(taskType)}</p>
                      <p className="mt-1 text-xs text-[var(--text-secondary)]">{rule.description}</p>
                    </div>
                    <ServiceBadge status={primaryReady ? 'online' : fallbackReady ? 'degraded' : 'offline'} compact />
                  </div>
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
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
              )
            })}
          </div>
        </div>

        <div className="panel overflow-hidden p-0">
          <div className="border-b border-white/5 px-6 py-5">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Installed models</p>
            <h2 className="mt-2 text-xl font-semibold text-white">Start / stop runtime cache</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-white/[0.03] text-[11px] uppercase tracking-[0.2em] text-[var(--text-muted)]">
                <tr>
                  <th className="px-6 py-3">Model</th>
                  <th className="px-6 py-3">Family</th>
                  <th className="px-6 py-3">Package</th>
                  <th className="px-6 py-3">Context</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Updated</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {tags.map((model) => {
                  const isLoaded = loadedSet.has(model.name)
                  const runningModel = running.find((entry) => entry.name === model.name)
                  return (
                    <tr key={model.name} className="border-t border-white/5">
                      <td className="px-6 py-4 align-top">
                        <p className="font-medium text-white">{model.name}</p>
                        <p className="mt-1 text-xs text-[var(--text-secondary)]">{model.details?.quantization_level ?? 'dynamic quant'}</p>
                      </td>
                      <td className="px-6 py-4 align-top text-[var(--text-secondary)]">{model.details?.family ?? model.details?.families?.[0] ?? 'unknown'}</td>
                      <td className="px-6 py-4 align-top text-[var(--text-secondary)]">{formatBytes(model.size)}</td>
                      <td className="px-6 py-4 align-top text-[var(--text-secondary)]">{runningModel?.details?.parameter_size ?? model.details?.parameter_size ?? 'n/a'}</td>
                      <td className="px-6 py-4 align-top"><ServiceBadge status={isLoaded ? 'online' : 'degraded'} compact /></td>
                      <td className="px-6 py-4 align-top text-[var(--text-secondary)]">{formatRelativeTime(model.modified_at)}</td>
                      <td className="px-6 py-4 align-top">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleModelAction(model.name, 'start')}
                            disabled={pendingModel === model.name}
                            className="inline-flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs font-medium text-cyan-200 transition hover:border-cyan-300/35 disabled:opacity-50"
                          >
                            <PlayCircle className="h-3.5 w-3.5" />
                            Warm
                          </button>
                          <button
                            type="button"
                            onClick={() => handleModelAction(model.name, 'stop')}
                            disabled={pendingModel === model.name}
                            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-fuchsia-300/30 disabled:opacity-50"
                          >
                            <StopCircle className="h-3.5 w-3.5" />
                            Unload
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  )
}
