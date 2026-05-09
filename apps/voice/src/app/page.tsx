'use client';

import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';

// ─── Typen ────────────────────────────────────────────────────────────────────

type RecordingState = 'idle' | 'recording' | 'processing';

interface TranscribeResponse { text: string; }
interface ChatMessage { role: 'user' | 'assistant'; content: string; }
interface ApiChatResponse { message?: string; response?: string; content?: string; }
interface SynthesizeResponse { audio_base64?: string; audio_url?: string; }

// ─── Endpunkte ────────────────────────────────────────────────────────────────

const VOICE_BASE_URL = process.env.NEXT_PUBLIC_VOICE_SERVICE_URL ?? '/voice';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '/api';

// ─── API-Helfer ───────────────────────────────────────────────────────────────

async function transcribeAudio(blob: Blob): Promise<string> {
  const form = new FormData();
  form.append('audio_file', blob, 'recording.webm');
  const res = await fetch(`${VOICE_BASE_URL}/stt/transcribe`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(`Transkription fehlgeschlagen: ${res.status}`);
  const data = (await res.json()) as TranscribeResponse;
  return data.text.trim();
}

async function askAssistant(messages: ChatMessage[]): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) throw new Error(`API-Fehler: ${res.status}`);
  const data = (await res.json()) as ApiChatResponse;
  return (data.message ?? data.response ?? data.content ?? '').trim();
}

async function synthesizeSpeech(text: string): Promise<string | null> {
  const res = await fetch(`${VOICE_BASE_URL}/tts/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) return null;
  const data = (await res.json()) as SynthesizeResponse;
  if (data.audio_base64) return `data:audio/wav;base64,${data.audio_base64}`;
  return data.audio_url ?? null;
}

// ─── Icons ────────────────────────────────────────────────────────────────────

function MicIcon({ active }: { active: boolean }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"
         className={`h-10 w-10 transition-colors duration-300 ${active ? 'text-white' : 'text-[color:var(--text-primary)]'}`}
         aria-hidden="true">
      <path d="M12 1a4 4 0 0 1 4 4v6a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4Z" />
      <path d="M19 10a1 1 0 1 0-2 0 5 5 0 0 1-10 0 1 1 0 1 0-2 0 7 7 0 0 0 6 6.93V19H9a1 1 0 1 0 0 2h6a1 1 0 1 0 0-2h-2v-2.07A7 7 0 0 0 19 10Z" />
    </svg>
  );
}

function SpeakerIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5" aria-hidden="true">
      <path d="M13.5 4.06c0-1.336-1.616-2.005-2.56-1.06l-4.5 4.5H4.508c-1.141 0-2.318.664-2.66 1.905A9.76 9.76 0 0 0 1.5 12c0 .898.121 1.768.35 2.595.341 1.24 1.518 1.905 2.659 1.905h1.93l4.5 4.5c.945.945 2.561.276 2.561-1.06V4.06ZM18.584 5.106a.75.75 0 0 1 1.06 0c3.808 3.807 3.808 9.98 0 13.788a.75.75 0 0 1-1.06-1.06 8.25 8.25 0 0 0 0-11.668.75.75 0 0 1 0-1.06Z" />
      <path d="M15.932 7.757a.75.75 0 0 1 1.061 0 6 6 0 0 1 0 8.486.75.75 0 0 1-1.06-1.061 4.5 4.5 0 0 0 0-6.364.75.75 0 0 1 0-1.06Z" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg className="h-7 w-7 animate-spin text-aurora-cyan" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4Z" />
    </svg>
  );
}

// ─── Wave-Bars (während Aufnahme, CSS-Animation) ─────────────────────────────

function WaveBars({ active }: { active: boolean }) {
  if (!active) return null;
  return (
    <div className="flex h-6 items-end gap-1" aria-hidden="true">
      {[0.6, 0.9, 1.2, 0.85, 0.55].map((delay, i) => (
        <span
          key={i}
          className="block w-1 rounded-full bg-aurora-cyan"
          style={{ animation: `breathe ${delay}s ease-in-out ${i * 0.08}s infinite`, height: '100%' }}
        />
      ))}
    </div>
  );
}

// ─── Hauptkomponente ──────────────────────────────────────────────────────────

const SPRING = { duration: 0.4, ease: [0.16, 1, 0.3, 1] as const };

export default function VoicePage() {
  const reduced = useReducedMotion();
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [transcript, setTranscript] = useState<string>('');
  const [aiResponse, setAiResponse] = useState<string>('');
  const [audioSrc, setAudioSrc] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<ChatMessage[]>([]);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const startRecording = useCallback(async () => {
    setError(null);
    setTranscript('');
    setAiResponse('');
    setAudioSrc(null);

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError('Mikrofon-Zugriff verweigert. Bitte Berechtigung erteilen.');
      return;
    }

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm';

    const recorder = new MediaRecorder(stream, { mimeType });
    chunksRef.current = [];

    recorder.ondataavailable = (e: BlobEvent) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunksRef.current, { type: mimeType });
      await processRecording(blob);
    };

    recorder.start(250);
    mediaRecorderRef.current = recorder;
    setRecordingState('recording');
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    setRecordingState('processing');
  }, []);

  const processRecording = useCallback(
    async (blob: Blob) => {
      try {
        const text = await transcribeAudio(blob);
        setTranscript(text);
        if (!text) {
          setError('Keine Sprache erkannt. Bitte erneut versuchen.');
          setRecordingState('idle');
          return;
        }
        const updatedHistory: ChatMessage[] = [...history, { role: 'user', content: text }];
        const reply = await askAssistant(updatedHistory);
        setAiResponse(reply);
        setHistory([...updatedHistory, { role: 'assistant', content: reply }]);
        const src = await synthesizeSpeech(reply);
        setAudioSrc(src);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Unbekannter Fehler';
        setError(msg);
      } finally {
        setRecordingState('idle');
      }
    },
    [history],
  );

  const playAudio = useCallback(() => {
    if (!audioSrc) return;
    if (audioRef.current) {
      audioRef.current.src = audioSrc;
      audioRef.current.play().catch(() => setError('Audio-Wiedergabe fehlgeschlagen.'));
    }
  }, [audioSrc]);

  const resetConversation = useCallback(() => {
    setHistory([]);
    setTranscript('');
    setAiResponse('');
    setAudioSrc(null);
    setError(null);
  }, []);

  const handleMicButton = useCallback(() => {
    if (recordingState === 'idle') startRecording();
    else if (recordingState === 'recording') stopRecording();
  }, [recordingState, startRecording, stopRecording]);

  const isRecording = recordingState === 'recording';
  const isProcessing = recordingState === 'processing';

  return (
    <main className="relative flex min-h-dvh flex-col items-center justify-between overflow-hidden px-4 py-10 gap-8">
      <div className="ambient-field" aria-hidden="true" />

      {/* Header */}
      <header className="relative z-10 text-center">
        <motion.h1
          initial={reduced ? false : { opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={SPRING}
          className="text-3xl font-semibold tracking-display sm:text-4xl"
        >
          Kirobi <span className="text-gradient-aurora">Voice</span>
        </motion.h1>
        <p className="mt-1 text-sm text-[color:var(--text-secondary)]">
          Sprich mit deinem lokalen Assistenten.
        </p>
      </header>

      {/* Mittlerer Bereich */}
      <section className="relative z-10 flex w-full max-w-md flex-1 flex-col justify-center gap-4">
        <AnimatePresence mode="popLayout">
          {transcript && (
            <motion.div
              key="transcript"
              initial={reduced ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={SPRING}
              className="glass rounded-2xl px-5 py-4"
            >
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.28em] text-aurora-cyan">Du</p>
              <p className="leading-relaxed text-[color:var(--text-primary)]">{transcript}</p>
            </motion.div>
          )}

          {aiResponse && (
            <motion.div
              key="response"
              initial={reduced ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ ...SPRING, delay: 0.05 }}
              className="glass-raised rounded-2xl px-5 py-4"
              style={{ borderColor: 'rgba(232, 121, 249, 0.25)' }}
            >
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.28em]" style={{ color: 'var(--accent-magenta)' }}>
                Kirobi
              </p>
              <p className="leading-relaxed text-[color:var(--text-primary)]">{aiResponse}</p>
              {audioSrc && (
                <button
                  onClick={playAudio}
                  className="mt-3 inline-flex items-center gap-2 text-sm text-aurora-cyan transition-colors hover:text-white"
                  aria-label="Antwort vorlesen"
                >
                  <SpeakerIcon />
                  Vorlesen
                </button>
              )}
            </motion.div>
          )}

          {isProcessing && (
            <motion.div
              key="processing"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex items-center justify-center gap-3 py-4 text-[color:var(--text-secondary)]"
            >
              <Spinner />
              <span className="text-sm">Verarbeite…</span>
            </motion.div>
          )}

          {error && (
            <motion.div
              key="error"
              role="alert"
              initial={reduced ? false : { opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
            >
              {error}
            </motion.div>
          )}

          {!transcript && !aiResponse && !isProcessing && !error && (
            <motion.p
              key="hint"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="select-none text-center text-sm text-[color:var(--text-muted)]"
            >
              Drücke den Mikrofon-Button und sprich.
            </motion.p>
          )}
        </AnimatePresence>
      </section>

      {/* Mikrofon-Button */}
      <section className="relative z-10 flex flex-col items-center gap-6">
        <div className="relative flex items-center justify-center">
          {/* Aurora-Halo, immer sichtbar (sanft) */}
          <span
            aria-hidden="true"
            className="pointer-events-none absolute -inset-6 rounded-full blur-2xl opacity-60"
            style={{ background: 'radial-gradient(circle, rgba(94,234,212,0.4), transparent 70%)' }}
          />
          {/* Pulsierender Aufnahme-Ring */}
          {isRecording && (
            <>
              <span aria-hidden="true" className="absolute -inset-2 rounded-full bg-aurora-magenta/40 mic-ring-active" />
              <span aria-hidden="true" className="absolute -inset-4 rounded-full bg-aurora-cyan/30 mic-ring-active" style={{ animationDelay: '0.3s' }} />
            </>
          )}

          <motion.button
            onClick={handleMicButton}
            disabled={isProcessing}
            aria-label={isRecording ? 'Aufnahme stoppen' : 'Aufnahme starten'}
            whileTap={reduced ? undefined : { scale: 0.94 }}
            transition={{ duration: 0.15 }}
            className={[
              'relative z-10 flex h-28 w-28 items-center justify-center rounded-full',
              'border border-[color:var(--border-soft)] backdrop-blur-2xl',
              'transition-all duration-300 ease-spring',
              'focus:outline-none focus-visible:ring-4 focus-visible:ring-aurora-cyan/60 focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--bg-void)]',
              isRecording
                ? 'shadow-glow-magenta'
                : isProcessing
                  ? 'cursor-not-allowed opacity-60'
                  : 'shadow-glow-cyan hover:scale-[1.04]',
            ].join(' ')}
            style={{
              background: isRecording
                ? 'linear-gradient(135deg, #e879f9, #a78bfa)'
                : isProcessing
                  ? 'rgba(15, 20, 50, 0.6)'
                  : 'linear-gradient(135deg, #5eead4, #22d3ee)',
            }}
          >
            {isProcessing ? <Spinner /> : <MicIcon active={isRecording} />}
          </motion.button>
        </div>

        {/* Status-Label + Wave-Bars */}
        <div className="flex h-6 items-center gap-3 text-xs uppercase tracking-[0.24em] text-[color:var(--text-muted)]">
          {isRecording && (
            <>
              <WaveBars active={isRecording} />
              <span className="text-aurora-magenta">● Aufnahme läuft</span>
            </>
          )}
          {isProcessing && <span>Verarbeite Sprache…</span>}
          {recordingState === 'idle' && !transcript && !aiResponse && <span>Bereit</span>}
          {recordingState === 'idle' && (transcript || aiResponse) && <span>Bereit für nächste Frage</span>}
        </div>

        {(transcript || aiResponse || history.length > 0) && (
          <button
            onClick={resetConversation}
            className="text-xs text-[color:var(--text-muted)] underline-offset-2 transition-colors hover:text-aurora-cyan hover:underline"
          >
            Gespräch zurücksetzen
          </button>
        )}
      </section>

      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <audio ref={audioRef} className="hidden" />
    </main>
  );
}
