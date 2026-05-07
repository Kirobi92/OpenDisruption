'use client'

import { useState, useRef, useCallback } from 'react'

// ─── Typen ────────────────────────────────────────────────────────────────────

type RecordingState = 'idle' | 'recording' | 'processing'

interface TranscribeResponse {
  text: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface ApiChatResponse {
  message?: string
  response?: string
  content?: string
}

interface SynthesizeResponse {
  audio_base64?: string
  audio_url?: string
}

// ─── Konstanten ───────────────────────────────────────────────────────────────

const VOICE_BASE_URL =
  process.env.NEXT_PUBLIC_VOICE_SERVICE_URL ?? '/voice'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? '/api'

// ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

async function transcribeAudio(blob: Blob): Promise<string> {
  const form = new FormData()
  form.append('audio', blob, 'recording.webm')
  const res = await fetch(`${VOICE_BASE_URL}/transcribe`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(`Transkription fehlgeschlagen: ${res.status}`)
  const data = (await res.json()) as TranscribeResponse
  return data.text.trim()
}

async function askAssistant(
  messages: ChatMessage[],
): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })
  if (!res.ok) throw new Error(`API-Fehler: ${res.status}`)
  const data = (await res.json()) as ApiChatResponse
  return (data.message ?? data.response ?? data.content ?? '').trim()
}

async function synthesizeSpeech(text: string): Promise<string | null> {
  const res = await fetch(`${VOICE_BASE_URL}/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) return null
  const data = (await res.json()) as SynthesizeResponse
  if (data.audio_base64) {
    return `data:audio/wav;base64,${data.audio_base64}`
  }
  return data.audio_url ?? null
}

// ─── Mikrofon-Icon ────────────────────────────────────────────────────────────

function MicIcon({ active }: { active: boolean }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`w-10 h-10 transition-colors duration-300 ${
        active ? 'text-white' : 'text-slate-300'
      }`}
      aria-hidden="true"
    >
      <path d="M12 1a4 4 0 0 1 4 4v6a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4Z" />
      <path d="M19 10a1 1 0 1 0-2 0 5 5 0 0 1-10 0 1 1 0 1 0-2 0 7 7 0 0 0 6 6.93V19H9a1 1 0 1 0 0 2h6a1 1 0 1 0 0-2h-2v-2.07A7 7 0 0 0 19 10Z" />
    </svg>
  )
}

// ─── Lautsprecher-Icon ────────────────────────────────────────────────────────

function SpeakerIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="w-5 h-5"
      aria-hidden="true"
    >
      <path d="M13.5 4.06c0-1.336-1.616-2.005-2.56-1.06l-4.5 4.5H4.508c-1.141 0-2.318.664-2.66 1.905A9.76 9.76 0 0 0 1.5 12c0 .898.121 1.768.35 2.595.341 1.24 1.518 1.905 2.659 1.905h1.93l4.5 4.5c.945.945 2.561.276 2.561-1.06V4.06ZM18.584 5.106a.75.75 0 0 1 1.06 0c3.808 3.807 3.808 9.98 0 13.788a.75.75 0 0 1-1.06-1.06 8.25 8.25 0 0 0 0-11.668.75.75 0 0 1 0-1.06Z" />
      <path d="M15.932 7.757a.75.75 0 0 1 1.061 0 6 6 0 0 1 0 8.486.75.75 0 0 1-1.06-1.061 4.5 4.5 0 0 0 0-6.364.75.75 0 0 1 0-1.06Z" />
    </svg>
  )
}

// ─── Spinner ──────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <svg
      className="animate-spin w-6 h-6 text-kirobi-400"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4Z"
      />
    </svg>
  )
}

// ─── Hauptkomponente ──────────────────────────────────────────────────────────

export default function VoicePage() {
  const [recordingState, setRecordingState] = useState<RecordingState>('idle')
  const [transcript, setTranscript] = useState<string>('')
  const [aiResponse, setAiResponse] = useState<string>('')
  const [audioSrc, setAudioSrc] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<ChatMessage[]>([])

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // ── Aufnahme starten ──────────────────────────────────────────────────────

  const startRecording = useCallback(async () => {
    setError(null)
    setTranscript('')
    setAiResponse('')
    setAudioSrc(null)

    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      setError('Mikrofon-Zugriff verweigert. Bitte Berechtigung erteilen.')
      return
    }

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm'

    const recorder = new MediaRecorder(stream, { mimeType })
    chunksRef.current = []

    recorder.ondataavailable = (e: BlobEvent) => {
      if (e.data.size > 0) chunksRef.current.push(e.data)
    }

    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop())
      const blob = new Blob(chunksRef.current, { type: mimeType })
      await processRecording(blob)
    }

    recorder.start(250)
    mediaRecorderRef.current = recorder
    setRecordingState('recording')
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Aufnahme stoppen ──────────────────────────────────────────────────────

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop()
    setRecordingState('processing')
  }, [])

  // ── Aufnahme verarbeiten ──────────────────────────────────────────────────

  const processRecording = useCallback(
    async (blob: Blob) => {
      try {
        // 1. Transkription
        const text = await transcribeAudio(blob)
        setTranscript(text)

        if (!text) {
          setError('Keine Sprache erkannt. Bitte erneut versuchen.')
          setRecordingState('idle')
          return
        }

        // 2. KI-Antwort
        const updatedHistory: ChatMessage[] = [
          ...history,
          { role: 'user', content: text },
        ]
        const reply = await askAssistant(updatedHistory)
        setAiResponse(reply)
        setHistory([...updatedHistory, { role: 'assistant', content: reply }])

        // 3. Sprachausgabe vorbereiten (nicht automatisch abspielen)
        const src = await synthesizeSpeech(reply)
        setAudioSrc(src)
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Unbekannter Fehler'
        setError(msg)
      } finally {
        setRecordingState('idle')
      }
    },
    [history],
  )

  // ── Sprachausgabe abspielen ───────────────────────────────────────────────

  const playAudio = useCallback(() => {
    if (!audioSrc) return
    if (audioRef.current) {
      audioRef.current.src = audioSrc
      audioRef.current.play().catch(() => {
        setError('Audio-Wiedergabe fehlgeschlagen.')
      })
    }
  }, [audioSrc])

  // ── Gespräch zurücksetzen ─────────────────────────────────────────────────

  const resetConversation = useCallback(() => {
    setHistory([])
    setTranscript('')
    setAiResponse('')
    setAudioSrc(null)
    setError(null)
  }, [])

  // ── Mikrofon-Button Handler ───────────────────────────────────────────────

  const handleMicButton = useCallback(() => {
    if (recordingState === 'idle') startRecording()
    else if (recordingState === 'recording') stopRecording()
  }, [recordingState, startRecording, stopRecording])

  // ── Render ────────────────────────────────────────────────────────────────

  const isRecording = recordingState === 'recording'
  const isProcessing = recordingState === 'processing'

  return (
    <main className="min-h-dvh bg-slate-900 flex flex-col items-center justify-between px-4 py-10 gap-8">
      {/* Header */}
      <header className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
          Kirobi <span className="text-kirobi-400">Voice</span>
        </h1>
        <p className="text-sm text-slate-500 mt-1">Sprich mit deinem Assistenten</p>
      </header>

      {/* Mittlerer Bereich: Transkription + Antwort */}
      <section className="w-full max-w-md flex flex-col gap-4 flex-1 justify-center">
        {/* Transkription */}
        {transcript && (
          <div className="rounded-2xl bg-slate-800 border border-slate-700 px-5 py-4">
            <p className="text-xs font-medium text-kirobi-400 uppercase tracking-widest mb-1">
              Du
            </p>
            <p className="text-slate-100 leading-relaxed">{transcript}</p>
          </div>
        )}

        {/* KI-Antwort */}
        {aiResponse && (
          <div className="rounded-2xl bg-slate-800 border border-kirobi-800 px-5 py-4">
            <p className="text-xs font-medium text-kirobi-400 uppercase tracking-widest mb-1">
              Kirobi
            </p>
            <p className="text-slate-100 leading-relaxed">{aiResponse}</p>

            {/* Sprachausgabe-Button */}
            {audioSrc && (
              <button
                onClick={playAudio}
                className="mt-3 inline-flex items-center gap-2 text-sm text-kirobi-400 hover:text-kirobi-300 transition-colors"
                aria-label="Antwort vorlesen"
              >
                <SpeakerIcon />
                Vorlesen
              </button>
            )}
          </div>
        )}

        {/* Verarbeitungs-Indikator */}
        {isProcessing && (
          <div className="flex items-center justify-center gap-3 text-slate-400 py-4">
            <Spinner />
            <span className="text-sm">Verarbeite…</span>
          </div>
        )}

        {/* Fehler */}
        {error && (
          <div
            role="alert"
            className="rounded-xl bg-red-950 border border-red-800 px-4 py-3 text-sm text-red-300"
          >
            {error}
          </div>
        )}

        {/* Leerer Zustand */}
        {!transcript && !aiResponse && !isProcessing && !error && (
          <p className="text-center text-slate-600 text-sm select-none">
            Drücke den Mikrofon-Button und sprich
          </p>
        )}
      </section>

      {/* Mikrofon-Button */}
      <section className="flex flex-col items-center gap-6">
        <div className="relative flex items-center justify-center">
          {/* Pulsierender Ring während Aufnahme */}
          {isRecording && (
            <span
              className="absolute inset-0 rounded-full bg-red-500 mic-ring-active"
              aria-hidden="true"
            />
          )}
          <button
            onClick={handleMicButton}
            disabled={isProcessing}
            aria-label={isRecording ? 'Aufnahme stoppen' : 'Aufnahme starten'}
            className={[
              'relative z-10 w-24 h-24 rounded-full flex items-center justify-center',
              'transition-all duration-200 focus:outline-none focus-visible:ring-4',
              'focus-visible:ring-kirobi-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
              isRecording
                ? 'bg-red-600 hover:bg-red-500 shadow-lg shadow-red-900/50'
                : isProcessing
                  ? 'bg-slate-700 cursor-not-allowed opacity-60'
                  : 'bg-kirobi-600 hover:bg-kirobi-500 shadow-lg shadow-kirobi-900/50 active:scale-95',
            ].join(' ')}
          >
            {isProcessing ? <Spinner /> : <MicIcon active={isRecording} />}
          </button>
        </div>

        {/* Status-Label */}
        <p className="text-xs text-slate-500 h-4">
          {isRecording && (
            <span className="text-red-400 animate-pulse">● Aufnahme läuft…</span>
          )}
          {isProcessing && <span>Verarbeite Sprache…</span>}
          {recordingState === 'idle' && !transcript && !aiResponse && (
            <span>Bereit</span>
          )}
        </p>

        {/* Gespräch zurücksetzen */}
        {(transcript || aiResponse || history.length > 0) && (
          <button
            onClick={resetConversation}
            className="text-xs text-slate-600 hover:text-slate-400 transition-colors underline underline-offset-2"
          >
            Gespräch zurücksetzen
          </button>
        )}
      </section>

      {/* Verstecktes Audio-Element für Sprachausgabe */}
      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <audio ref={audioRef} className="hidden" />
    </main>
  )
}
