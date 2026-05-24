import { GpuStatus } from './types'

interface GpuPanelProps {
  gpu: GpuStatus
}

export function GpuPanel({ gpu }: GpuPanelProps) {
  return (
    <div className="gpuPanel">
      <strong>RTX 3090 / GPU</strong>
      {gpu.available ? (
        <>
          <div className="gpuLine"><span>VRAM</span><span>{gpu.memory_used_mb} / {gpu.memory_total_mb} MB</span></div>
          <div className="gpuLine"><span>Temperatur</span><span>{gpu.temperature_c} °C</span></div>
          <div className="gpuLine"><span>Last</span><span>{gpu.utilization_pct} %</span></div>
        </>
      ) : <div className="systemMeta">GPU-Daten nicht verfügbar: {gpu.error}</div>}
    </div>
  )
}
