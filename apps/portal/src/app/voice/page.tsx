'use client';

import { motion } from 'framer-motion';
import { ArrowLeft, Sparkles } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useRef, useState } from 'react';

import { BottomNav } from '@/components/layout/BottomNav';
import { VoiceButton } from '@/components/voice/VoiceButton';
import { useRequireAuth } from '@/lib/auth';
import { apiClient, createConversation, sendMessage } from '@/lib/api';

type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';

type VoiceExchange = {
  id: string;
  transcript: string;
  response: string;
  timestamp: string;
};

function VoicePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isLoading, isAuthenticated } = useRequireAuth();

  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [transcript, setTranscript] = useState('');
  const [responseText, setResponseText] = useState('Sag einfach etwas und halte den Button gedrückt.');
  const [conversationLog, setConversationLog] = useState<VoiceExchange[]>([]);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioUrlRef = useRef<string | null>(null);
  const isPointerDownRef = useRef(false);

  useEffect(() => {
    return () => {
      mediaRecorderRef.current?.stop();
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
    };
  }, []);

  const ensureConversationId = async () => {
    const existingId = searchParams.get('conversation');
    if (existingId) {
      return existingId;
    }

    const conversation = await createConversation('Voice Session', 'WORKSPACE');
    router.replace(`/voice?conversation=${conversation.id}`);
    return conversation.id;
  };

  const playResponse = async (text: string) => {
    setVoiceState('speaking');
    const ttsResponse = await apiClient.get('/api/proxy/voice/tts', {
      params: { text, voice: 'kirobi_de' },
      responseType: 'blob',
    });

    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
    }

    audioUrlRef.current = URL.createObjectURL(ttsResponse.data as Blob);
    const audio = new Audio(audioUrlRef.current);

    audio.onended = () => {
      setVoiceState('idle');
    };

    await audio.play();
  };

  const handleRecordingStop = async () => {
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;

    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
    audioChunksRef.current = [];

    if (audioBlob.size === 0) {
      setVoiceState('idle');
      return;
    }

    setVoiceState('processing');

    const formData = new FormData();
    formData.append('audio', audioBlob, 'voice.webm');
    formData.append('file', audioBlob, 'voice.webm');

    try {
      const sttResponse = await apiClient.post('/api/proxy/voice/stt', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const heardText = String(sttResponse.data?.text ?? sttResponse.data?.transcript ?? '').trim();
      setTranscript(heardText || 'Keine Sprache erkannt.');

      if (!heardText) {
        setResponseText('Ich habe gerade nichts verstanden. Versuch es noch einmal in ruhiger Umgebung.');
        setVoiceState('idle');
        return;
      }

      const conversationId = await ensureConversationId();
      const result = await sendMessage(conversationId, heardText);
      const aiReply = result.assistantMessage?.content ?? 'Ich bin bei dir. Lass uns gleich weiterdenken.';

      setResponseText(aiReply);
      setConversationLog((current) => [
        {
          id: `voice-${Date.now()}`,
          transcript: heardText,
          response: aiReply,
          timestamp: new Date().toISOString(),
        },
        ...current,
      ]);

      await playResponse(aiReply);
    } catch {
      setResponseText('Die Sprachverarbeitung war gerade nicht erreichbar. Bitte versuche es gleich noch einmal.');
      setVoiceState('idle');
    }
  };

  const startRecording = async () => {
    if (voiceState !== 'idle') {
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      audioChunksRef.current = [];

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        void handleRecordingStop();
      };

      recorder.start();
      setTranscript('Ich höre zu...');
      setResponseText('Sprich frei. Ich bin ganz bei dir.');
      setVoiceState('listening');
    } catch {
      setResponseText('Mikrofonzugriff wurde nicht freigegeben. Bitte erlaube den Zugriff und versuche es erneut.');
      setVoiceState('idle');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  };

  if (isLoading || !isAuthenticated) {
    return <div className="min-h-screen bg-void" />;
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-void px-4 pb-24 pt-6 text-white md:px-8">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_10%,rgba(94,234,212,0.18),transparent_25%),radial-gradient(circle_at_85%_35%,rgba(232,121,249,0.12),transparent_24%),radial-gradient(circle_at_20%_80%,rgba(167,139,250,0.12),transparent_26%)]" />

      <div className="relative z-10 mx-auto max-w-5xl">
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => router.push('/chat')}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/75"
          >
            <ArrowLeft className="h-4 w-4" />
            Zurück zum Chat
          </button>
          <button
            type="button"
            onClick={() => router.push('/chat')}
            className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/65"
          >
            Exit
          </button>
        </div>

        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 rounded-[2rem] border border-white/10 bg-white/5 px-6 py-10 shadow-card backdrop-blur-xl md:px-10"
        >
          <div className="text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-aurora-cyan/20 bg-aurora-cyan/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-aurora-cyan">
              <Sparkles className="h-4 w-4" />
              Voice Flow
            </div>
            <p className="mx-auto mt-6 max-w-2xl text-xl font-medium text-white/90">{responseText}</p>
          </div>

          <div className="mt-12 flex flex-col items-center justify-center gap-8 text-center">
            <div
              onMouseDown={() => {
                isPointerDownRef.current = true;
                void startRecording();
              }}
              onMouseUp={() => {
                if (isPointerDownRef.current) {
                  isPointerDownRef.current = false;
                  stopRecording();
                }
              }}
              onMouseLeave={() => {
                if (isPointerDownRef.current) {
                  isPointerDownRef.current = false;
                  stopRecording();
                }
              }}
              onTouchStart={() => {
                isPointerDownRef.current = true;
                void startRecording();
              }}
              onTouchEnd={() => {
                if (isPointerDownRef.current) {
                  isPointerDownRef.current = false;
                  stopRecording();
                }
              }}
              className="select-none"
            >
              <VoiceButton
                state={voiceState}
                onClick={() => {
                  if (voiceState === 'idle') {
                    void startRecording();
                  } else if (voiceState === 'listening') {
                    stopRecording();
                  }
                }}
              />
            </div>

            <div className="space-y-3">
              <div className="text-sm uppercase tracking-[0.26em] text-white/45">Live Transcript</div>
              <div className="mx-auto max-w-2xl rounded-[1.5rem] border border-white/10 bg-black/15 px-5 py-4 text-lg text-white/80">
                {transcript}
              </div>
            </div>
          </div>
        </motion.section>

        <section className="mt-8 rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-card backdrop-blur-xl">
          <div className="mb-4 text-sm uppercase tracking-[0.24em] text-white/45">Verlauf</div>
          <div className="max-h-[280px] space-y-3 overflow-y-auto pr-1">
            {conversationLog.length > 0 ? (
              conversationLog.map((entry) => (
                <div key={entry.id} className="rounded-3xl border border-white/10 bg-black/10 p-4">
                  <div className="text-xs text-white/40">{new Date(entry.timestamp).toLocaleTimeString('de-DE')}</div>
                  <div className="mt-2 text-sm text-aurora-cyan">Du: {entry.transcript}</div>
                  <div className="mt-2 text-sm text-white/75">Kirobi: {entry.response}</div>
                </div>
              ))
            ) : (
              <div className="rounded-3xl border border-dashed border-white/10 p-6 text-sm text-white/50">
                Noch keine Voice-Exchanges. Halte den Button gedrückt und beginne zu sprechen.
              </div>
            )}
          </div>
        </section>
      </div>

      <BottomNav />
    </main>
  );
}

export default function VoicePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-void" />}>
      <VoicePageContent />
    </Suspense>
  );
}
