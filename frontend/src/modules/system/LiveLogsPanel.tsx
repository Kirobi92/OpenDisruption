import { useCallback, useEffect, useRef, useState } from 'react'

interface LiveLogsPanelProps {
  base: string
}

const LOG_SERVICES = ['kirobi-backend', 'kirobi-frontend', 'comfyui', 'hermes'] as const
type LogService = typeof LOG_SERVICES[number]

export function LiveLogsPanel({ base }: LiveLogsPanelProps) {
  const [logService, setLogService] = useState<LogService>('kirobi-backend')
  const [logLines, setLogLines] = useState<string[]>([])
  const [logActive, setLogActive] = useState(false)
  const sourceRef = useRef<EventSource | null>(null)

  const stopStream = useCallback(() => {
    sourceRef.current?.close()
    sourceRef.current = null
  }, [])

  useEffect(() => {
    if (!logActive) {
      stopStream()
      return
    }
    setLogLines([])
    const source = new EventSource(`${base}/api/system/logs/${logService}`)
    sourceRef.current = source
    source.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setLogLines((lines) => [...lines.slice(-80), data.line])
      } catch {
        setLogLines((lines) => [...lines.slice(-80), event.data])
      }
    }
    source.onerror = () =>
      setLogLines((lines) => [...lines.slice(-80), '[SSE getrennt oder Service nicht erlaubt]'])
    return () => source.close()
  }, [base, logActive, logService, stopStream])

  return (
    <div className="gpuPanel" style={{ marginTop: 14 }}>
      <strong>Live Logs</strong>
      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
        <select value={logService} onChange={(e) => setLogService(e.target.value as LogService)}>
          {LOG_SERVICES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button type="button" onClick={() => setLogActive((v) => !v)}>
          {logActive ? 'Stop' : 'Stream starten'}
        </button>
      </div>
      <pre style={{ maxHeight: 260, overflow: 'auto', whiteSpace: 'pre-wrap', fontSize: 11 }}>
        {logLines.join('\n') || 'Noch kein Logstream aktiv.'}
      </pre>
    </div>
  )
}
