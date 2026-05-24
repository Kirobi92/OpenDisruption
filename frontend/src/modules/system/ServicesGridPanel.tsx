import { ServiceStatus } from './types'

interface ServicesGridPanelProps {
  services: ServiceStatus[]
}

export function ServicesGridPanel({ services }: ServicesGridPanelProps) {
  return (
    <div className="systemGrid">
      {services.map((svc) => (
        <article key={svc.name} className={`systemCard ${svc.status}`}>
          <div className="systemCardTop">
            <div className="systemName">{svc.name}</div>
            <div className="systemPort">{svc.port ? `:${svc.port}` : 'systemd'}</div>
          </div>
          <span className={`systemPill ${svc.status}`}>{svc.status === 'ok' ? 'ONLINE' : 'DOWN'}</span>
          <div className="systemMeta">{svc.detail || svc.url || 'bereit'}</div>
          {typeof svc.latency_ms === 'number' && <div className="systemMeta">{svc.latency_ms} ms</div>}
        </article>
      ))}
    </div>
  )
}
