'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { ExternalLink, RotateCcw, Search } from 'lucide-react'
import { ServiceBadge } from '@/components/ui/ServiceBadge'
import { copyText, formatDuration, formatRelativeTime, useControlStatus, useServiceHealthMatrix } from '@/lib/api'

export default function ServicesPage() {
  const { data: probes = [] } = useServiceHealthMatrix()
  const { data: control } = useControlStatus()
  const [query, setQuery] = useState('')
  const [selectedService, setSelectedService] = useState<string>('api')
  const [toast, setToast] = useState<string | null>(null)
  const [now, setNow] = useState(Date.now())
  const seenOnline = useRef<Record<string, number>>({})

  useEffect(() => {
    const interval = window.setInterval(() => setNow(Date.now()), 30000)
    return () => window.clearInterval(interval)
  }, [])

  useEffect(() => {
    for (const probe of probes) {
      if (probe.status === 'online' && !seenOnline.current[probe.definition.name]) {
        seenOnline.current[probe.definition.name] = Date.now()
      }
      if (probe.status !== 'online') {
        delete seenOnline.current[probe.definition.name]
      }
    }
  }, [probes])

  useEffect(() => {
    if (!toast) return
    const timeout = window.setTimeout(() => setToast(null), 2400)
    return () => window.clearTimeout(timeout)
  }, [toast])

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return probes
    return probes.filter((probe) => `${probe.definition.label} ${probe.definition.description} ${probe.definition.category}`.toLowerCase().includes(needle))
  }, [probes, query])

  const selected = filtered.find((probe) => probe.definition.name === selectedService) ?? filtered[0] ?? probes[0]

  return (
    <div className="space-y-6">
      <section className="panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Service matrix</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">All 20+ docker services</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--text-secondary)]">
          Read-only live health table with latency, session uptime approximation, restart command helpers and raw health payload inspection.
        </p>
      </section>

      {toast ? <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200">{toast}</div> : null}

      <section className="grid gap-6 xl:grid-cols-[1.35fr,0.65fr]">
        <div className="panel overflow-hidden p-0">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 px-6 py-5">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Health table</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Service health, latency & uptime</h2>
            </div>
            <label className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200">
              <Search className="h-4 w-4 text-[var(--text-muted)]" />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search services" className="bg-transparent focus:outline-none" />
            </label>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-white/[0.03] text-[11px] uppercase tracking-[0.2em] text-[var(--text-muted)]">
                <tr>
                  <th className="px-6 py-3">Service</th>
                  <th className="px-6 py-3">Category</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Latency</th>
                  <th className="px-6 py-3">Uptime</th>
                  <th className="px-6 py-3">Last check</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((probe) => {
                  const uptime = seenOnline.current[probe.definition.name] ? formatDuration(now - seenOnline.current[probe.definition.name]) : '—'
                  return (
                    <tr
                      key={probe.definition.name}
                      className={`border-t border-white/5 transition ${selected?.definition.name === probe.definition.name ? 'bg-cyan-400/5' : ''}`}
                    >
                      <td className="px-6 py-4 align-top">
                        <button type="button" onClick={() => setSelectedService(probe.definition.name)} className="text-left">
                          <p className="font-medium text-white">{probe.definition.label}</p>
                          <p className="mt-1 text-xs text-[var(--text-secondary)]">{probe.definition.description}</p>
                        </button>
                      </td>
                      <td className="px-6 py-4 align-top text-[var(--text-secondary)]">{probe.definition.category}</td>
                      <td className="px-6 py-4 align-top"><ServiceBadge status={probe.status} compact /></td>
                      <td className="px-6 py-4 align-top text-[var(--text-secondary)]">{probe.latencyMs ? `${probe.latencyMs} ms` : '—'}</td>
                      <td className="px-6 py-4 align-top text-[var(--text-secondary)]">{uptime}</td>
                      <td className="px-6 py-4 align-top text-[var(--text-secondary)]">{formatRelativeTime(probe.checkedAt)}</td>
                      <td className="px-6 py-4 align-top">
                        <div className="flex justify-end gap-2">
                          {probe.definition.openPath ? (
                            <button
                              type="button"
                              onClick={() => window.open(probe.definition.openPath, '_blank', 'noopener,noreferrer')}
                              className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-cyan-400/25"
                            >
                              <ExternalLink className="h-3.5 w-3.5" />
                              Open
                            </button>
                          ) : null}
                          <button
                            type="button"
                            onClick={async () => setToast((await copyText(probe.definition.restartCommand)) ? `${probe.definition.label} restart copied` : probe.definition.restartCommand)}
                            className="inline-flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs font-medium text-cyan-200 transition hover:border-cyan-300/35"
                          >
                            <RotateCcw className="h-3.5 w-3.5" />
                            Restart
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

        <div className="space-y-6">
          <div className="panel p-6">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Payload viewer</p>
            <h2 className="mt-2 text-xl font-semibold text-white">{selected?.definition.label ?? 'Service details'}</h2>
            <p className="mt-2 text-sm text-[var(--text-secondary)]">{selected?.summary ?? 'Select a service from the table to inspect its latest payload.'}</p>
            <div className="mt-4 rounded-2xl border border-white/5 bg-black/30 p-4">
              <pre className="max-h-[22rem] overflow-auto text-xs leading-6 text-slate-200">{JSON.stringify(selected?.payload ?? {}, null, 2)}</pre>
            </div>
          </div>

          <div className="panel p-6">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Recent operator logs</p>
            <h2 className="mt-2 text-xl font-semibold text-white">Supervisor events</h2>
            <div className="mt-5 space-y-3">
              {(control?.recentEvents ?? []).slice(0, 6).map((event) => (
                <div key={`${event.timestamp}-${event.event_type}`} className="rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-white">{event.event_type}</p>
                    <span className="text-xs text-[var(--text-muted)]">{formatRelativeTime(event.timestamp)}</span>
                  </div>
                  <p className="mt-2 text-sm text-[var(--text-secondary)]">{event.message}</p>
                </div>
              ))}
              {!control?.recentEvents.length ? (
                <div className="rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-3 text-sm text-[var(--text-secondary)]">No supervisor events received yet.</div>
              ) : null}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
