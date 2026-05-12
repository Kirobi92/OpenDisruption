'use client'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ActivitySquare, Aperture, ChartNoAxesCombined, ShieldCheck } from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard'
import { formatNumber, useAnalyticsStats, useModelUsage, useServiceHealthMatrix, useWeeklyDailyStats, useZoneStats } from '@/lib/api'

const piePalette = ['#5eead4', '#e879f9', '#a78bfa', '#fbbf24', '#60a5fa', '#34d399']

function latencyColor(value: number, status: string) {
  if (status === 'offline') return '#f87171'
  if (value <= 120) return '#5eead4'
  if (value <= 350) return '#fbbf24'
  return '#fb7185'
}

export default function AnalyticsPage() {
  const { data: stats } = useAnalyticsStats()
  const { data: weekly = [] } = useWeeklyDailyStats(7)
  const { data: zoneStats = [] } = useZoneStats()
  const { data: modelUsage = [] } = useModelUsage()
  const { data: probes = [] } = useServiceHealthMatrix()

  const eventsTrend = weekly.map((entry) => ({
    date: entry.date.slice(5),
    events: entry.total_events,
    users: entry.active_users,
  }))

  const zoneChart = zoneStats.map((entry) => ({
    zone: entry.zone,
    reads: entry.read_count,
    writes: entry.write_count,
    total: entry.total_count,
  }))

  const latencyChart = probes.map((probe) => ({
    service: probe.definition.label,
    latency: probe.latencyMs ?? 0,
    status: probe.status,
  }))

  const modelChart = modelUsage.map((entry) => ({
    name: entry.model_used,
    value: entry.usage_count,
  }))

  return (
    <div className="space-y-6">
      <section className="panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Analytics</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">Events, model usage & latency</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--text-secondary)]">
          Recharts-based analytics for today/week, model selection patterns, zone access distribution and a latency heatmap across local APIs.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={ActivitySquare} title="Events today" value={stats?.eventsToday ?? 0} subtitle="analytics /stats" accent="magenta" />
        <StatCard icon={ShieldCheck} title="Active users" value={stats?.activeUsers ?? 0} subtitle="daily distinct users" accent="cyan" />
        <StatCard icon={ChartNoAxesCombined} title="Conversations" value={stats?.totalConversations ?? 0} subtitle={`${stats?.totalMessages ?? 0} messages indexed`} accent="violet" />
        <StatCard icon={Aperture} title="Observed services" value={probes.length} subtitle="latency heatmap source" accent="gold" />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="panel p-6">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Events today / week</p>
          <h2 className="mt-2 text-xl font-semibold text-white">Seven-day activity trend</h2>
          <div className="mt-5 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={eventsTrend}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="4 4" />
                <XAxis dataKey="date" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip contentStyle={{ background: '#080b1f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16 }} />
                <Legend />
                <Line type="monotone" dataKey="events" stroke="#5eead4" strokeWidth={3} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="users" stroke="#e879f9" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel p-6">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Model usage distribution</p>
          <h2 className="mt-2 text-xl font-semibold text-white">Messages by model</h2>
          <div className="mt-5 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={modelChart} dataKey="value" nameKey="name" innerRadius={75} outerRadius={110} paddingAngle={3}>
                  {modelChart.map((entry, index) => (
                    <Cell key={`${entry.name}-${index}`} fill={piePalette[index % piePalette.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#080b1f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16 }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="panel p-6">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Zone access patterns</p>
          <h2 className="mt-2 text-xl font-semibold text-white">Read vs write totals</h2>
          <div className="mt-5 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={zoneChart}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="4 4" />
                <XAxis dataKey="zone" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip contentStyle={{ background: '#080b1f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16 }} />
                <Legend />
                <Bar dataKey="reads" fill="#5eead4" radius={[8, 8, 0, 0]} />
                <Bar dataKey="writes" fill="#a78bfa" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel p-6">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">API latency heatmap</p>
          <h2 className="mt-2 text-xl font-semibold text-white">Observed service latency</h2>
          <div className="mt-5 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={latencyChart} layout="vertical" margin={{ left: 32 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="4 4" />
                <XAxis type="number" stroke="#64748b" />
                <YAxis type="category" dataKey="service" width={120} stroke="#64748b" />
                <Tooltip contentStyle={{ background: '#080b1f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16 }} formatter={(value) => [`${value} ms`, 'Latency']} />
                <Bar dataKey="latency" radius={[0, 8, 8, 0]}>
                  {latencyChart.map((entry, index) => (
                    <Cell key={`${entry.service}-${index}`} fill={latencyColor(entry.latency, entry.status)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-3 text-sm text-[var(--text-secondary)]">Across {formatNumber(latencyChart.length)} local surfaces – green ≤120ms, amber ≤350ms, red above or offline.</p>
        </div>
      </section>
    </div>
  )
}
