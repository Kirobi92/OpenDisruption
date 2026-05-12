import { AlertTriangle, CheckCircle2, LoaderCircle, XCircle } from 'lucide-react'
import { ServiceState, titleCase } from '@/lib/api'

const styles: Record<ServiceState, string> = {
  online: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-300',
  offline: 'border-red-500/25 bg-red-500/10 text-red-300',
  degraded: 'border-amber-500/25 bg-amber-500/10 text-amber-300',
  unknown: 'border-white/10 bg-white/5 text-slate-300',
}

const icons = {
  online: CheckCircle2,
  offline: XCircle,
  degraded: AlertTriangle,
  unknown: LoaderCircle,
}

export function ServiceBadge({ status, compact = false }: { status: ServiceState; compact?: boolean }) {
  const Icon = icons[status]
  const spacing = compact ? 'px-2 py-0.5' : 'px-2.5 py-1'
  const iconSize = compact ? 'h-3 w-3' : 'h-3.5 w-3.5'
  const motion = status === 'unknown' ? 'animate-spin' : status === 'online' ? 'animate-pulse' : ''

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border text-xs font-medium ${spacing} ${styles[status]}`}>
      <Icon className={`${iconSize} ${motion}`} />
      {titleCase(status)}
    </span>
  )
}
