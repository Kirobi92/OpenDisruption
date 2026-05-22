/**
 * MicButton — Push-to-Talk / Auto-Mode Button mit Audio-Visualisierung
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { useAgentStore } from '../../stores/agentStore'
import styles from './MicButton.module.css'

interface MicButtonProps {
  onInterrupt: () => void
}

export function MicButton({ onInterrupt }: MicButtonProps) {
  const { agentState, inputMode, isRecording, isMuted, connectionState } = useAgentStore()
  const { setIsRecording, setIsMuted, setInputMode } = useAgentStore()
  const [audioLevel, setAudioLevel] = useState(0)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const analyzerRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number>(0)
  const audioWsRef = useRef<WebSocket | null>(null)

  // Audio Visualisierung
  const startVisualization = useCallback((stream: MediaStream) => {
    const ctx = new AudioContext()
    const source = ctx.createMediaStreamSource(stream)
    const analyzer = ctx.createAnalyser()
    analyzer.fftSize = 256
    source.connect(analyzer)
    analyzerRef.current = analyzer

    const tick = () => {
      const data = new Uint8Array(analyzer.frequencyBinCount)
      analyzer.getByteFrequencyData(data)
      const avg = data.slice(0, 8).reduce((a, b) => a + b, 0) / 8
      setAudioLevel(avg / 255)
      animFrameRef.current = requestAnimationFrame(tick)
    }
    tick()
  }, [])

  // Mikrofon starten → Audio-WS (Pipecat Port 8766)
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
      })
      mediaStreamRef.current = stream
      startVisualization(stream)
      setIsRecording(true)

      // WebSocket zu Pipecat Audio-Transport (dynamischer Host für LAN/Tailscale)
      const _h = window.location.hostname
      let wsHost = _h
      if (_h === 'localhost' && !window.location.port) {
        try {
          const raw = localStorage.getItem('kirobi_backend')
          const { mode, customHost } = raw ? JSON.parse(raw) : { mode: 'lan', customHost: '' }
          wsHost = mode === 'custom' ? (customHost || '192.168.178.10')
                 : mode === 'tailscale' ? '100.127.16.62'
                 : '192.168.178.10'
        } catch { wsHost = '192.168.178.10' }
      }
      const ws = new WebSocket(`ws://${wsHost}:8766/audio`)
      audioWsRef.current = ws
      ws.binaryType = 'arraybuffer'

      ws.onopen = () => {
        const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })
        recorder.ondataavailable = (e) => {
          if (ws.readyState === WebSocket.OPEN && e.data.size > 0) {
            ws.send(e.data)
          }
        }
        recorder.start(100) // 100ms chunks
      }

      ws.onclose = () => stopRecording()
    } catch (err) {
      console.error('Mikrofon-Zugriff verweigert:', err)
    }
  }, [startVisualization, setIsRecording])

  const stopRecording = useCallback(() => {
    cancelAnimationFrame(animFrameRef.current)
    mediaStreamRef.current?.getTracks().forEach(t => t.stop())
    mediaStreamRef.current = null
    analyzerRef.current = null
    audioWsRef.current?.close()
    audioWsRef.current = null
    setAudioLevel(0)
    setIsRecording(false)
  }, [setIsRecording])

  // Auto-Mode: Automatisch starten wenn verbunden
  useEffect(() => {
    if (inputMode === 'auto' && connectionState === 'connected' && !isRecording && !isMuted) {
      startRecording()
    }
    return () => {
      if (inputMode === 'push-to-talk') stopRecording()
    }
  }, [connectionState, inputMode]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleMainClick = useCallback(() => {
    if (agentState === 'speaking') {
      // Interrupt
      onInterrupt()
      return
    }
    if (inputMode === 'push-to-talk') {
      if (isRecording) stopRecording()
      else startRecording()
    }
  }, [agentState, inputMode, isRecording, onInterrupt, startRecording, stopRecording])

  const toggleMute = useCallback(() => {
    if (isMuted) {
      setIsMuted(false)
      startRecording()
    } else {
      setIsMuted(true)
      stopRecording()
    }
  }, [isMuted, setIsMuted, startRecording, stopRecording])

  const isActive = isRecording && !isMuted
  const isInterruptable = agentState === 'speaking'
  const isDisabled = connectionState !== 'connected'

  const ringScale = 1 + audioLevel * 0.4

  return (
    <div className={styles.container}>
      {/* Mode Toggle */}
      <div className={styles.modeToggle}>
        <button
          className={`${styles.modeBtn} ${inputMode === 'auto' ? styles.active : ''}`}
          onClick={() => setInputMode('auto')}
        >Auto</button>
        <button
          className={`${styles.modeBtn} ${inputMode === 'push-to-talk' ? styles.active : ''}`}
          onClick={() => setInputMode('push-to-talk')}
        >PTT</button>
      </div>

      {/* Main Button */}
      <div className={styles.buttonWrapper}>
        {/* Animierter Ring */}
        <div
          className={`${styles.ring} ${isActive ? styles.ringActive : ''}`}
          style={{ transform: `scale(${isActive ? ringScale : 1})` }}
        />
        <button
          className={`${styles.mainBtn}
            ${isActive ? styles.mainBtnActive : ''}
            ${isInterruptable ? styles.mainBtnInterrupt : ''}
            ${isDisabled ? styles.mainBtnDisabled : ''}`}
          onClick={handleMainClick}
          disabled={isDisabled}
          title={isInterruptable ? 'Unterbrechen' : isRecording ? 'Aktiv (klicken zum Stoppen)' : 'Klicken zum Sprechen'}
        >
          {isInterruptable ? '⏹' : isMuted ? '🔇' : isActive ? '🎙' : '🎤'}
        </button>
      </div>

      {/* Mute */}
      <button
        className={`${styles.muteBtn} ${isMuted ? styles.muteBtnActive : ''}`}
        onClick={toggleMute}
        title={isMuted ? 'Ton einschalten' : 'Ton ausschalten'}
      >
        {isMuted ? '🔇' : '🔊'}
      </button>
    </div>
  )
}
