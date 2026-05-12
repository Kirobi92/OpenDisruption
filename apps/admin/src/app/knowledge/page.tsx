'use client'

import { Database, FolderSync, LockKeyhole, RefreshCcw } from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard'
import { ServiceBadge } from '@/components/ui/ServiceBadge'
import { ServiceState, copyText, formatBytes, formatNumber, useKnowledgeCollections, useServiceHealthMatrix } from '@/lib/api'
import { useEffect, useMemo, useState } from 'react'

export default function KnowledgePage() {
  const { data: collections = [] } = useKnowledgeCollections()
  const { data: probes = [] } = useServiceHealthMatrix()
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    if (!toast) return
    const timeout = window.setTimeout(() => setToast(null), 2200)
    return () => window.clearTimeout(timeout)
  }, [toast])

  const totalPoints = collections.reduce((sum, collection) => sum + collection.pointsCount, 0)
  const totalStorage = collections.reduce((sum, collection) => sum + collection.estimatedDiskBytes, 0)
  const readyCollections = collections.filter((collection) => collection.present).length
  const qdrantStatus = probes.find((probe) => probe.definition.name === 'qdrant')?.status ?? 'unknown'
  const retrievalStatus = probes.find((probe) => probe.definition.name === 'retrieval')?.status ?? 'unknown'
  const embeddingsStatus = probes.find((probe) => probe.definition.name === 'embeddings')?.status ?? 'unknown'

  const vaultStatus = useMemo(() => {
    if (readyCollections === collections.length && qdrantStatus === 'online') return 'online'
    if (readyCollections >= Math.max(1, collections.length - 2)) return 'degraded'
    return 'offline'
  }, [collections.length, qdrantStatus, readyCollections])

  return (
    <div className="space-y-6">
      <section className="panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Knowledge plane</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">Qdrant collections & vault state</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--text-secondary)]">
          Canonical OpenDisruption collections with live points, estimated vector disk usage and safe re-index commands for local execution.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Database} title="Collections present" value={readyCollections} subtitle={`of ${collections.length}`} accent="violet" />
        <StatCard icon={FolderSync} title="Indexed vectors" value={totalPoints} subtitle="Qdrant points" accent="cyan" />
        <StatCard icon={LockKeyhole} title="Est. storage" value={formatBytes(totalStorage)} subtitle="vector payload estimate" accent="gold" />
        <StatCard icon={Database} title="Vault status" value={vaultStatus.toUpperCase()} subtitle="Qdrant + retrieval + embeddings" accent="magenta" />
      </section>

      {toast ? <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200">{toast}</div> : null}

      <section className="grid gap-6 xl:grid-cols-[0.82fr,1.18fr]">
        <div className="panel p-6">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Vault services</p>
          <h2 className="mt-2 text-xl font-semibold text-white">Pipeline readiness</h2>
          <div className="mt-5 space-y-3">
            {[
              { label: 'Qdrant', status: qdrantStatus, description: 'Vector store and collection metadata' },
              { label: 'Embeddings', status: embeddingsStatus, description: 'Embedding generation and write path' },
              { label: 'Retrieval', status: retrievalStatus, description: 'Search and RAG access layer' },
              { label: 'Vault sync', status: vaultStatus, description: 'Canonical collections presence across users and zones' },
            ].map((item) => (
              <div key={item.label} className="rounded-2xl border border-white/5 bg-white/[0.03] p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-white">{item.label}</p>
                    <p className="mt-1 text-xs text-[var(--text-secondary)]">{item.description}</p>
                  </div>
                  <ServiceBadge status={item.status as ServiceState} compact />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel overflow-hidden p-0">
          <div className="border-b border-white/5 px-6 py-5">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Collection inventory</p>
            <h2 className="mt-2 text-xl font-semibold text-white">Required vault collections</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-white/[0.03] text-[11px] uppercase tracking-[0.2em] text-[var(--text-muted)]">
                <tr>
                  <th className="px-6 py-3">Collection</th>
                  <th className="px-6 py-3">Zone</th>
                  <th className="px-6 py-3">Vectors</th>
                  <th className="px-6 py-3">Disk size</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {collections.map((collection) => (
                  <tr key={collection.name} className="border-t border-white/5">
                    <td className="px-6 py-4 align-top">
                      <p className="font-medium text-white">{collection.name}</p>
                      <p className="mt-1 text-xs text-[var(--text-secondary)]">{collection.description}</p>
                    </td>
                    <td className="px-6 py-4 align-top text-[var(--text-secondary)]">{collection.zone}</td>
                    <td className="px-6 py-4 align-top text-[var(--text-secondary)]">
                      {formatNumber(collection.pointsCount)}
                      <span className="mt-1 block text-xs text-[var(--text-muted)]">{collection.vectorSize ? `${collection.vectorSize} dim` : 'n/a'}</span>
                    </td>
                    <td className="px-6 py-4 align-top text-[var(--text-secondary)]">
                      {formatBytes(collection.estimatedDiskBytes)}
                      <span className="mt-1 block text-xs text-[var(--text-muted)]">{collection.payloadSchemaCount} schema fields</span>
                    </td>
                    <td className="px-6 py-4 align-top"><ServiceBadge status={collection.status} compact /></td>
                    <td className="px-6 py-4 align-top text-right">
                      <button
                        type="button"
                        onClick={async () => setToast((await copyText(collection.reindexCommand)) ? `${collection.name} re-index command copied` : collection.reindexCommand)}
                        className="inline-flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs font-medium text-cyan-200 transition hover:border-cyan-300/35"
                      >
                        <RefreshCcw className="h-3.5 w-3.5" />
                        Re-index
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  )
}
