/**
 * Agent State Store — Zustand
 * Globaler State für den Voice-Agent und Avatar.
 */
import { create } from 'zustand'

export type AgentState = 'idle' | 'listening' | 'transcribing' | 'thinking' | 'speaking' | 'error'
export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error'
export type InputMode = 'auto' | 'push-to-talk'
export type BackendMode = 'lan' | 'tailscale' | 'custom'

export const BACKEND_PRESETS: Record<BackendMode, string> = {
  lan:       '192.168.178.10',
  tailscale: '100.127.16.62',
  custom:    '',
}

function getStoredBackend(): { mode: BackendMode; customHost: string } {
  try {
    const raw = localStorage.getItem('kirobi_backend')
    if (raw) return JSON.parse(raw)
  } catch {}
  return { mode: 'lan', customHost: '' }
}

export function resolveBackendHost(mode: BackendMode, customHost: string): string {
  if (mode === 'custom') return customHost || '192.168.178.10'
  return BACKEND_PRESETS[mode]
}

export function getRuntimeBackendHost(): string {
  const rawHost = window.location.hostname
  const isCapacitor = rawHost === 'localhost' && !window.location.port
  if (!isCapacitor) return rawHost
  try {
    const raw = localStorage.getItem('kirobi_backend')
    if (raw) {
      const { mode, customHost } = JSON.parse(raw)
      return resolveBackendHost(mode, customHost)
    }
  } catch {}
  return BACKEND_PRESETS.lan
}

export function getBackendHttpBase(): string {
  const rawHost = window.location.hostname
  const isCapacitor = rawHost === 'localhost' && !window.location.port
  const proto = isCapacitor ? 'http' : (window.location.protocol === 'https:' ? 'https' : 'http')
  return `${proto}://${getRuntimeBackendHost()}:8765`
}

export interface AgentStore {
  // Connection
  connectionState: ConnectionState
  wsUrl: string

  // Backend switcher
  backendMode: BackendMode
  customBackendHost: string
  setBackendMode: (mode: BackendMode, customHost?: string) => void

  // Agent
  agentState: AgentState
  userTranscript: string
  userTranscriptFinal: string
  agentText: string
  agentTextFull: string

  // Avatar Lip-Sync
  mouthAmplitude: number   // 0.0 - 1.0
  viseme: string | null

  // UI
  inputMode: InputMode
  isRecording: boolean
  isMuted: boolean
  volume: number

  // Provider info
  sttProvider: string
  llmProvider: string
  ttsProvider: string

  // Actions
  setConnectionState: (s: ConnectionState) => void
  setAgentState: (s: AgentState) => void
  setUserTranscript: (t: string, final?: boolean) => void
  appendAgentText: (t: string, delta?: boolean) => void
  setLipSync: (amplitude: number, viseme?: string | null) => void
  setInputMode: (m: InputMode) => void
  setIsRecording: (v: boolean) => void
  setIsMuted: (v: boolean) => void
  setVolume: (v: number) => void
  setProviders: (stt: string, llm: string, tts: string) => void
  reset: () => void
}

const _stored = getStoredBackend()

const initialState = {
  connectionState: 'disconnected' as ConnectionState,
  wsUrl: 'ws://localhost:8765/ws',
  backendMode: _stored.mode,
  customBackendHost: _stored.customHost,
  agentState: 'idle' as AgentState,
  userTranscript: '',
  userTranscriptFinal: '',
  agentText: '',
  agentTextFull: '',
  mouthAmplitude: 0,
  viseme: null,
  inputMode: 'auto' as InputMode,
  isRecording: false,
  isMuted: false,
  volume: 1.0,
  sttProvider: '...',
  llmProvider: '...',
  ttsProvider: '...',
}

export const useAgentStore = create<AgentStore>((set) => ({
  ...initialState,

  setConnectionState: (connectionState) => set({ connectionState }),
  setAgentState: (agentState) => set({ agentState }),

  setBackendMode: (mode, customHost = '') => {
    const host = resolveBackendHost(mode, customHost)
    try { localStorage.setItem('kirobi_backend', JSON.stringify({ mode, customHost })) } catch {}
    set({ backendMode: mode, customBackendHost: customHost })
    // Seite neu laden damit WebSocket-Hook neue URL übernimmt
    window.location.reload()
  },

  setUserTranscript: (t, final = false) => set(final
    ? { userTranscriptFinal: t, userTranscript: t }
    : { userTranscript: t }
  ),

  appendAgentText: (t, delta = true) => set((state) => ({
    agentText: delta ? state.agentText + t : t,
    agentTextFull: delta ? state.agentTextFull + t : t,
  })),

  setLipSync: (amplitude, viseme = null) => set({ mouthAmplitude: amplitude, viseme }),
  setInputMode: (inputMode) => set({ inputMode }),
  setIsRecording: (isRecording) => set({ isRecording }),
  setIsMuted: (isMuted) => set({ isMuted }),
  setVolume: (volume) => set({ volume }),
  setProviders: (sttProvider, llmProvider, ttsProvider) => set({ sttProvider, llmProvider, ttsProvider }),

  reset: () => set({
    agentState: 'idle',
    userTranscript: '',
    agentText: '',
    mouthAmplitude: 0,
    viseme: null,
  }),
}))
