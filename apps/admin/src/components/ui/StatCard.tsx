'use client'

import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'
import { formatNumber } from '@/lib/api'

type Accent = 'cyan' | 'magenta' | 'violet' | 'gold'

const accentClasses: Record<Accent, string> = {
  cyan: 'border-cyan-400/20 bg-cyan-400/10 text-cyan-300',
  magenta: 'border-fuchsia-400/20 bg-fuchsia-400/10 text-fuchsia-300',
  violet: 'border-violet-400/20 bg-violet-400/10 text-violet-300',
  gold: 'border-amber-400/20 bg-amber-400/10 text-amber-300',
}

function isNumeric(value: string | number) {
  return typeof value === 'number' || /^\d+(\.\d+)?$/.test(value)
}

export function StatCard({
  icon: Icon,
  title,
  value,
  change,
  accent = 'cyan',
  subtitle,
}: {
  icon: LucideIcon
  title: string
  value: string | number
  change?: string
  accent?: Accent
  subtitle?: string
}) {
  const numeric = useMemo(() => (isNumeric(value) ? Number(value) : null), [value])
  const [display, setDisplay] = useState(numeric ?? 0)

  useEffect(() => {
    if (numeric === null) return
    const start = performance.now()
    const duration = 750
    const from = display
    const frame = (now: number) => {
      const progress = Math.min((now - start) / duration, 1)
      const next = Math.round(from + (numeric - from) * progress)
      setDisplay(next)
      if (progress < 1) requestAnimationFrame(frame)
    }
    requestAnimationFrame(frame)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [numeric])

  return (
    <motion.div
      whileHover={{ y: -2, scale: 1.01 }}
      transition={{ duration: 0.18 }}
      className="panel group overflow-hidden p-5"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">{title}</p>
          <div className="mt-3 text-3xl font-semibold tracking-tight text-white">
            {numeric === null ? value : formatNumber(display)}
          </div>
          {(change || subtitle) && (
            <p className="mt-2 text-sm text-[var(--text-secondary)]">
              {change ? <span className="text-cyan-300">{change}</span> : null}
              {change && subtitle ? <span className="mx-2 text-white/20">•</span> : null}
              {subtitle}
            </p>
          )}
        </div>
        <div className={`rounded-2xl border p-3 shadow-card ${accentClasses[accent]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <div className="mt-4 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
    </motion.div>
  )
}
