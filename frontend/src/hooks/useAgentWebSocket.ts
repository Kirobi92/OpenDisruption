/**
 * WebSocket Hook — verbindet mit dem Kirobi Avatar Backend
 * Handhabt Events, Audio-Output und Reconnect-Logik.
 */
import { useCallback, useEffect, useRef } from 'react'
import { useAgentStore } from '../stores/agentStore'

// Dynamisch: gleicher Host + korrektes Protokoll (wss wenn https)
// In Capacitor (native APK) ist hostname "localhost" → aus LocalStorage lesen
import { resolveBackendHost, BACKEND_PRESETS } from '../stores/agentStore'

function getBackendHost(): string {
  const _h = window.location.hostname
  const isCapacitor = _h === 'localhost' && !window.location.port
  if (!isCapacitor) return _h
  try {
    const raw = localStorage.getItem('kirobi_backend')
    if (raw) {
      const { mode, customHost } = JSON.parse(raw)
      return resolveBackendHost(mode, customHost)
    }
  } catch {}
  return BACKEND_PRESETS.lan
}

const _RAW_HOST = window.location.hostname
const IS_CAPACITOR = _RAW_HOST === 'localhost' && !window.location.port
const WS_HOST = getBackendHost()
const WS_PROTO = IS_CAPACITOR ? 'ws' : (window.location.protocol === 'https:' ? 'wss' : 'ws')
const HTTP_PROTO = IS_CAPACITOR ? 'http' : (window.location.protocol === 'https:' ? 'https' : 'http')
const WS_URL = `${WS_PROTO}://${WS_HOST}:8765/ws`
const AUDIO_URL = `${WS_PROTO}://${WS_HOST}:8766/audio`
const RECONNECT_DELAY = 3000

export function useAgentWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const nextStartTimeRef = useRef<number>(0)  // Scheduled Playback — kein Abgehacke
  const store = useAgentStore()

  // Audio Context initialisieren (lazy, wegen Browser-Policy)
  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext({ sampleRate: 24000 })
    }
    return audioContextRef.current
  }, [])

  // PCM Int16 Audio-Chunk abspielen — sequenziell ohne Lücken
  const playAudioChunk = useCallback(async (base64Data: string, sampleRate: number) => {
    try {
      const ctx = getAudioContext()
      if (ctx.state === 'suspended') await ctx.resume()

      const binary = atob(base64Data)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)

      // s16le -> Float32 [-1, 1]
      const view = new DataView(bytes.buffer)
      const frameCount = Math.floor(bytes.byteLength / 2)
      const audioBuffer = ctx.createBuffer(1, frameCount, sampleRate || 24000)
      const channel = audioBuffer.getChannelData(0)
      for (let i = 0; i < frameCount; i++) {
        channel[i] = view.getInt16(i * 2, true) / 32768
      }

      const source = ctx.createBufferSource()
      source.buffer = audioBuffer
      source.connect(ctx.destination)

      // Scheduled: nächster Chunk startet exakt nach dem letzten — kein Abgehacke
      const now = ctx.currentTime
      const startAt = Math.max(now + 0.04, nextStartTimeRef.current)  // 40ms lookahead
      source.start(startAt)
      nextStartTimeRef.current = startAt + audioBuffer.duration
    } catch (e) {
      console.warn('Audio-Chunk Fehler:', e)
    }
  }, [getAudioContext])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    store.setConnectionState('connecting')
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      store.setConnectionState('connected')
      console.log('🔌 Kirobi Avatar Agent verbunden')
    }

    ws.onmessage = (evt) => {
      try {
        const event = JSON.parse(evt.data)
        handleEvent(event)
      } catch (e) {
        console.error('WS Parse-Fehler:', e)
      }
    }

    ws.onclose = () => {
      store.setConnectionState('disconnected')
      store.setAgentState('idle')
      console.log('🔌 Verbindung getrennt — reconnect in', RECONNECT_DELAY, 'ms')
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY)
    }

    ws.onerror = (e) => {
      console.error('WS-Fehler:', e)
      store.setConnectionState('error')
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleEvent = useCallback((event: Record<string, unknown>) => {
    const type = event.type as string

    switch (type) {
      case 'system.ready':
        console.log('✅ System ready')
        break

      case 'agent.state':
        store.setAgentState(event.state as never)
        // Text-Buffer bei neuem Turn leeren
        if (event.state === 'listening' || event.state === 'thinking') {
          useAgentStore.setState({ agentText: '' })
        }
        break

      case 'transcript.partial':
        store.setUserTranscript(event.text as string, false)
        break

      case 'transcript.final':
        store.setUserTranscript(event.text as string, true)
        break

      case 'agent.text':
        if (event.delta) {
          store.appendAgentText(event.text as string, true)
        } else {
          store.appendAgentText(event.text as string, false)
        }
        break

      case 'audio.chunk':
        if (!store.isMuted) {
          playAudioChunk(event.data as string, (event.sample_rate as number) || 24000)
        }
        break

      case 'audio.end':
        store.setLipSync(0, null)
        nextStartTimeRef.current = 0  // Reset — nächste Antwort startet sofort
        break

      case 'avatar.lipSync':
        store.setLipSync(event.amplitude as number, event.viseme as string | null)
        break

      case 'system.error':
        console.error('Agent-Fehler:', event.message)
        store.setAgentState('error')
        break

      case 'ping':
        wsRef.current?.send(JSON.stringify({ type: 'pong', ts: Date.now() / 1000 }))
        break
    }
  }, [store, playAudioChunk])

  const unlockAudio = useCallback(async () => {
    const ctx = getAudioContext()
    if (ctx.state === 'suspended') await ctx.resume()
    // Stille abspielen um iOS/Android AudioContext zu entsperren
    const buf = ctx.createBuffer(1, 1, 22050)
    const src = ctx.createBufferSource()
    src.buffer = buf
    src.connect(ctx.destination)
    src.start()
  }, [getAudioContext])

  const sendInterrupt = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ type: 'control.interrupt' }))
  }, [])

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    wsRef.current?.close()
  }, [])

  useEffect(() => {
    connect()
    // Provider-Config laden
    fetch(`${HTTP_PROTO}://${WS_HOST}:8765/config`)
      .then(r => r.json())
      .then(d => store.setProviders(d.stt, d.llm, d.tts))
      .catch(() => {})

    return () => {
      disconnect()
      audioContextRef.current?.close()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return { sendInterrupt, unlockAudio }
}
