// Shared TypeScript types for SystemModule and sub-components

export type ServiceStatus = {
  name: string
  port: number | null
  status: 'ok' | 'down'
  url?: string
  detail?: string
  latency_ms?: number | null
}

export type GpuStatus = {
  available: boolean
  memory_used_mb?: number
  memory_total_mb?: number
  temperature_c?: number
  utilization_pct?: number
  error?: string
}

export type SystemStatus = { ts: number; services: ServiceStatus[]; gpu: GpuStatus }

export type AudioStatus = {
  active_connections: number
  idle_s: number
  last_connection_ts: number | null
  status: string
  last_alert_ts?: number
  idle_limit_s?: number
  idle_limit_mode?: 'day' | 'night' | string
}

export type AlertEntry = {
  ts: number
  idle_s: number
  active_connections: number
  message: string
}

export type DashboardSnapshot = {
  timestamp: string
  matched_count: number
  skip_count: number
  dry_run_count: number
  total_count: number
  marked_rate_percent: number
  skip_rate_percent: number
  top_strategies: { strategy: string; count: number }[]
  quality_score: number
  assessment: string
}

export type DashboardData = {
  status: string
  schema_version: string
  snapshots: DashboardSnapshot[]
  snapshots_total: number
  avg_marked_rate: number
  min_marked_rate: number
  max_marked_rate: number
  latest_assessment: string
  trend: string | null
  sc_trend?: ScTrendData
}

export type DashboardConfig = {
  marked_rate_green: number
  marked_rate_yellow: number
}

export type MilestoneFiredEntry = {
  fired_thresholds: number[]
  highest_fired: number | null
  count: number
}

export type MilestoneFiredData = {
  status: string
  fired: Record<string, MilestoneFiredEntry>
}

export type MilestoneConfig = {
  status: string
  config: {
    global_milestones: number[]
    tag_overrides: Record<string, number[]>
  }
  ts: number
}

export type DownloadSnapshot = {
  week: string
  date: string
  debug_downloads: number
  release_downloads: number
  total: number
}

export type DownloadTagEntry = {
  snapshots: DownloadSnapshot[]
  total_downloads: number
  sparkline: string
  trend: string
  latest_week: string | null
  latest_debug: number
  latest_release: number
}

export type DownloadHistoryData = {
  status: string
  schema_version: string
  tags: Record<string, DownloadTagEntry>
  ts: number
}

export type DownloadCompareCell = {
  total: number
  debug: number
  release: number
}

export type DownloadCompareData = {
  status: string
  tags: string[]
  weeks: string[]
  matrix: Record<string, Record<string, DownloadCompareCell>>
  tag_totals: Record<string, number>
  ts: number
}

export type ScAlertEvent = {
  timestamp: string
  run_id: number
  run_started_at: string
  sc_issue_count: number
  threshold: number
  delta: number
}

export type ScAlertsData = {
  alerts: ScAlertEvent[]
  total: number
  limit: number
  offset: number
  has_more: boolean
  history_file: string
}

export type ScTrendEntry = {
  run_id: number
  sc_issue_count: number
  timestamp?: string
  commit?: string
}

export type ScTrendSummary = {
  total_runs: number
  valid_runs: number
  latest_count: number | null
  min_count: number | null
  max_count: number | null
  avg_last_5: number | null
  trend_direction: string | null
  trend_delta: number | null
  interpretation: string
}

export type ScTrendData = {
  available: boolean
  entries: ScTrendEntry[]
  summary: ScTrendSummary | null
  sc_trend_file?: string
  error?: string
}

export type MusicHealthData = {
  status: string
  service: string
  port: number
  database: { ok: boolean; error?: string | null }
  ollama: { reachable: boolean; error?: string | null }
  audiocraft: { available: boolean; note?: string }
  heartmula: { available: boolean; model_exists: boolean; model_path?: string }
}
