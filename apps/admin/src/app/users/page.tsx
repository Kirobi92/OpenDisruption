'use client'

import { useMemo } from 'react'
import { CircleGauge, Database, ShieldCheck, Users2 } from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard'
import { ServiceBadge } from '@/components/ui/ServiceBadge'
import { USER_PROFILES, formatBytes, formatNumber, formatRelativeTime, useDashboardActivity, useKnowledgeCollections, useServiceHealthMatrix } from '@/lib/api'

export default function UsersPage() {
  const { data: activity = [] } = useDashboardActivity(20)
  const { data: collections = [] } = useKnowledgeCollections()
  const { data: probes = [] } = useServiceHealthMatrix()

  const collectionMap = new Map(collections.map((collection) => [collection.name, collection]))
  const authStatus = probes.find((probe) => probe.definition.name === 'auth')?.status ?? 'unknown'

  const userCards = useMemo(
    () =>
      USER_PROFILES.map((user) => {
        const vault = collectionMap.get(user.collection)
        const lastActive = activity.find(
          (item) => item.actor.toLowerCase().includes(user.username.toLowerCase()) || item.summary.toLowerCase().includes(user.username.toLowerCase()),
        )?.created_at
        return { user, vault, lastActive }
      }),
    [activity, collectionMap],
  )

  const activeUsers = userCards.filter((card) => card.lastActive).length
  const totalVaultPoints = userCards.reduce((sum, card) => sum + (card.vault?.pointsCount ?? 0), 0)
  const totalVaultStorage = userCards.reduce((sum, card) => sum + (card.vault?.estimatedDiskBytes ?? 0), 0)

  return (
    <div className="space-y-6">
      <section className="panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Users</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">User management snapshot</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--text-secondary)]">
          Static owner/family profiles enriched with live last-activity hints and their matching personal knowledge vault collections.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Users2} title="Profiles" value={USER_PROFILES.length} subtitle="Sven, Samira, Sineo" accent="cyan" />
        <StatCard icon={CircleGauge} title="Recently active" value={activeUsers} subtitle="Seen in dashboard activity" accent="magenta" />
        <StatCard icon={Database} title="Vault points" value={totalVaultPoints} subtitle={formatBytes(totalVaultStorage)} accent="violet" />
        <StatCard icon={ShieldCheck} title="Auth service" value={authStatus.toUpperCase()} subtitle="health source for permissions" accent="gold" />
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        {userCards.map(({ user, vault, lastActive }) => (
          <div key={user.id} className="panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-2xl">{user.avatar}</div>
                <div>
                  <p className="text-lg font-semibold text-white">{user.displayName}</p>
                  <p className="mt-1 text-sm text-[var(--text-secondary)]">{user.role}</p>
                </div>
              </div>
              <ServiceBadge status={vault?.status ?? 'unknown'} compact />
            </div>

            <div className="mt-5 rounded-2xl border border-white/5 bg-white/[0.03] p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-[var(--text-muted)]">Knowledge vault</p>
              <p className="mt-2 text-sm text-white">{user.collection}</p>
              <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-[var(--text-secondary)]">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.2em] text-[var(--text-muted)]">Vectors</p>
                  <p className="mt-1">{formatNumber(vault?.pointsCount ?? 0)}</p>
                </div>
                <div>
                  <p className="text-[11px] uppercase tracking-[0.2em] text-[var(--text-muted)]">Storage</p>
                  <p className="mt-1">{formatBytes(vault?.estimatedDiskBytes ?? 0)}</p>
                </div>
              </div>
            </div>

            <div className="mt-5">
              <p className="text-xs uppercase tracking-[0.2em] text-[var(--text-muted)]">Zone permissions</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {user.zonePermissions.map((zone) => (
                  <span key={zone} className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-200">
                    {zone}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-5">
              <p className="text-xs uppercase tracking-[0.2em] text-[var(--text-muted)]">Preferences</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {user.preferences.map((preference) => (
                  <span key={preference} className="rounded-full border border-cyan-400/15 bg-cyan-400/10 px-2.5 py-1 text-xs text-cyan-100">
                    {preference}
                  </span>
                ))}
              </div>
            </div>

            <p className="mt-5 text-sm text-[var(--text-secondary)]">Last active {formatRelativeTime(lastActive)}</p>
          </div>
        ))}
      </section>
    </div>
  )
}
