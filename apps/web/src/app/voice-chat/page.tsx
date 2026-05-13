'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  MicrophoneIcon,
  StopIcon,
  PlayIcon,
  SpeakerWaveIcon,
  ArrowPathIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { useVoiceConversation } from '@/lib/use-voice-conversation';

interface AgentOption {
  id: string;
  label: string;
  description: string;
  category?: string;
  default_model?: string;
}

interface VoiceOption {
  voice_id: string;
  label: string;
  language: string;
  gender: string;
  quality: string;
  description: string;
}

interface ToneOption {
  tone_id: string;
  label: string;
  emoji: string;
  description: string;
}

const VOICE_BASE = '/voice';
const API_BASE = '/api';

export default function VoiceChatPage() {
  const router = useRouter();
  const [token, setToken] = useState<string>('');
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [tones, setTones] = useState<ToneOption[]>([]);

  const [agent, setAgent] = useState('kirobi');
  const [voice, setVoice] = useState('de_DE-thorsten-high');
  const [tone, setTone] = useState('neutral');
  const [autoPlay, setAutoPlay] = useState(true);
  const [pushToTalk, setPushToTalk] = useState(false);
  const [streamMode, setStreamMode] = useState<'oneshot' | 'chunked'>('chunked');

  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const voice_ws = useVoiceConversation();
  const { state: vsState, start: vsStart, stop: vsStop, reset: vsReset, setAutoplay: vsSetAutoplay } = voice_ws;

  const recording = vsState.status === 'recording';
  const thinking = vsState.status === 'streaming';
  const speaking = vsState.status === 'speaking';
  const error = vsState.error;
  const conversationId = vsState.conversationId;
  const history = vsState.history;

  const statusMsg = (() => {
    if (vsState.status === 'recording') return 'Hoere zu...';
    if (vsState.status === 'streaming') return vsState.transcript ? 'Denkt nach…' : 'Verarbeite Sprache…';
    if (vsState.status === 'speaking') {
      const ms = vsState.firstAudioMs ? `${(vsState.firstAudioMs / 1000).toFixed(1)}s bis erstes Audio` : '';
      return `Spricht… ${ms}`;
    }
    if (vsState.status === 'error') return 'Fehler — bitte erneut versuchen.';
    if (vsState.history.length === 0) return 'Bereit. Druecke das Mikrofon, um zu starten.';
    return 'Bereit fuer naechste Frage.';
  })();

  useEffect(() => {
    const t = typeof window !== 'undefined' ? localStorage.getItem('kirobi_token') : null;
    if (!t) { router.push('/'); return; }
    setToken(t);
  }, [router]);

  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        const [opts, vs, ts] = await Promise.all([
          axios.get(`${API_BASE}/chat/runtime/options`, { headers: { Authorization: `Bearer ${token}` } }),
          axios.get(`${VOICE_BASE}/voices`),
          axios.get(`${VOICE_BASE}/personas`),
        ]);
        setAgents(opts.data.agent_options || []);
        setVoices(vs.data.voices || []);
        setTones(ts.data.tones || []);
      } catch (err) {
        console.error('Settings load failed', err);
        // settings load is non-fatal — surface via console only
      }
    })();
  }, [token]);

  // Keep the hook's autoplay flag in sync with the user toggle.
  useEffect(() => { vsSetAutoplay(autoPlay); }, [autoPlay, vsSetAutoplay]);

  async function startRecording() {
    try {
      await vsStart({
        agent, voice, tone,
        language: 'de',
        conversationId,
        jwt: token,
        mode: streamMode,
      });
    } catch (err: unknown) {
      console.error('Voice start failed', err);
    }
  }

  async function stopRecording() {
    await vsStop();
  }

  function resetConversation() {
    vsReset();
  }

  function playEntry(entry: { audio_urls: string[] }) {
    if (!audioElRef.current || entry.audio_urls.length === 0) return;
    let i = 0;
    const playNext = () => {
      if (!audioElRef.current || i >= entry.audio_urls.length) return;
      audioElRef.current.src = entry.audio_urls[i++];
      audioElRef.current.onended = playNext;
      audioElRef.current.play().catch(() => { /* ignore */ });
    };
    playNext();
  }

  if (!token) return null;

  const currentAgent = agents.find((a) => a.id === agent);
  const currentVoice = voices.find((v) => v.voice_id === voice);
  const currentTone = tones.find((t) => t.tone_id === tone);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-8 pb-32">
        <header className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">🎙️ Sprach-Chat</h1>
          <p className="text-gray-400 mt-1 text-sm">
            Kontinuierlicher Sprach-Dialog mit deinen Agenten — komplett lokal auf deiner RTX 3090.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
          <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
            <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">Agent</label>
            <select
              value={agent}
              onChange={(e) => { setAgent(e.target.value); vsReset(); }}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-kirobi-500"
            >
              {agents.map((a) => (<option key={a.id} value={a.id}>{a.label}</option>))}
            </select>
            {currentAgent && (<p className="text-xs text-gray-500 mt-2 line-clamp-2">{currentAgent.description}</p>)}
          </div>

          <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
            <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">Stimme</label>
            <select
              value={voice}
              onChange={(e) => setVoice(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-kirobi-500"
            >
              {voices.map((v) => (<option key={v.voice_id} value={v.voice_id}>{v.label} [{v.language}]</option>))}
            </select>
            {currentVoice && (<p className="text-xs text-gray-500 mt-2 line-clamp-2">{currentVoice.description}</p>)}
          </div>

          <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
            <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">Tonfall</label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-kirobi-500"
            >
              {tones.map((t) => (<option key={t.tone_id} value={t.tone_id}>{t.emoji} {t.label}</option>))}
            </select>
            {currentTone && (<p className="text-xs text-gray-500 mt-2 line-clamp-2">{currentTone.description}</p>)}
          </div>
        </div>

        <div className="flex flex-wrap gap-3 mb-6 text-sm">
          <label className="flex items-center gap-2 px-3 py-2 bg-gray-900/60 border border-gray-800 rounded-lg cursor-pointer hover:border-kirobi-500 transition">
            <input type="checkbox" checked={autoPlay} onChange={(e) => setAutoPlay(e.target.checked)} className="accent-kirobi-500" />
            <span>Antwort automatisch abspielen</span>
          </label>
          <label className="flex items-center gap-2 px-3 py-2 bg-gray-900/60 border border-gray-800 rounded-lg cursor-pointer hover:border-kirobi-500 transition">
            <input type="checkbox" checked={pushToTalk} onChange={(e) => setPushToTalk(e.target.checked)} className="accent-kirobi-500" />
            <span>Push-to-Talk (gedrueckt halten)</span>
          </label>
          <label className="flex items-center gap-2 px-3 py-2 bg-gray-900/60 border border-gray-800 rounded-lg cursor-pointer hover:border-kirobi-500 transition">
            <input
              type="checkbox"
              checked={streamMode === 'chunked'}
              onChange={(e) => setStreamMode(e.target.checked ? 'chunked' : 'oneshot')}
              className="accent-kirobi-500"
            />
            <span>Live-Upload (Audio waehrend Aufnahme streamen)</span>
          </label>
          <button
            onClick={resetConversation}
            className="flex items-center gap-2 px-3 py-2 bg-rose-900/40 border border-rose-800 rounded-lg hover:bg-rose-900/60 transition"
          >
            <TrashIcon className="w-4 h-4" />
            <span>Konversation zuruecksetzen</span>
          </button>
        </div>

        <div className="space-y-3 mb-8">
          {history.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <SpeakerWaveIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Noch keine Konversation. Sprich los!</p>
            </div>
          )}
          {history.map((e) => (
            <div key={e.id} className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
              <div className="text-xs text-gray-500 mb-2 flex items-center gap-2 flex-wrap">
                <span>{new Date(e.created_at).toLocaleTimeString('de-DE')}</span>
                <span>·</span><span className="text-kirobi-400">{e.agent}</span>
                <span>·</span><span>{e.voice}</span>
                <span>·</span><span>{e.tone}</span>
                <span>·</span><span className="text-gray-600">{e.audio_urls.length} chunks</span>
              </div>
              <p className="text-sm text-gray-300 mb-2"><span className="text-gray-500 mr-2">Du:</span>{e.user_text}</p>
              <p className="text-sm text-white whitespace-pre-wrap"><span className="text-kirobi-400 mr-2">{e.agent}:</span>{e.assistant_text}</p>
              <button
                onClick={() => playEntry(e)}
                className="mt-3 inline-flex items-center gap-2 px-3 py-1 bg-kirobi-900/40 border border-kirobi-700 rounded-lg text-xs hover:bg-kirobi-900/60 transition"
              >
                <PlayIcon className="w-3 h-3" />
                <span>Erneut abspielen</span>
              </button>
            </div>
          ))}

          {(vsState.transcript || vsState.partialReply) && (thinking || speaking) && (
            <div className="bg-kirobi-950/40 border border-kirobi-800/60 rounded-xl p-4">
              <div className="text-xs text-kirobi-400 mb-2 flex items-center gap-2">
                <span className="inline-block w-2 h-2 bg-kirobi-400 rounded-full animate-pulse" />
                <span>{speaking ? 'Spricht…' : 'Streamt…'}</span>
                {vsState.firstAudioMs && <span className="text-gray-500">· {(vsState.firstAudioMs / 1000).toFixed(1)}s bis 1. Audio</span>}
                {vsState.audioChunks > 0 && <span className="text-gray-500">· {vsState.audioChunks} chunks</span>}
              </div>
              {vsState.transcript && (
                <p className="text-sm text-gray-300 mb-2"><span className="text-gray-500 mr-2">Du:</span>{vsState.transcript}</p>
              )}
              {vsState.partialReply && (
                <p className="text-sm text-white whitespace-pre-wrap"><span className="text-kirobi-400 mr-2">{agent}:</span>{vsState.partialReply}<span className="text-kirobi-400 animate-pulse">▌</span></p>
              )}
            </div>
          )}
        </div>

        <div className="text-center text-sm text-gray-400 mb-4">
          {error && <p className="text-rose-400 mb-2">{error}</p>}
          <p>{statusMsg}</p>
        </div>

        <audio ref={audioElRef} preload="auto" />
      </div>

      <div className="fixed bottom-20 md:bottom-8 left-0 right-0 flex justify-center pointer-events-none">
        <button
          onClick={pushToTalk ? undefined : (recording ? stopRecording : startRecording)}
          onMouseDown={pushToTalk ? startRecording : undefined}
          onMouseUp={pushToTalk ? stopRecording : undefined}
          onTouchStart={pushToTalk ? startRecording : undefined}
          onTouchEnd={pushToTalk ? stopRecording : undefined}
          disabled={thinking}
          className={`pointer-events-auto flex items-center justify-center w-20 h-20 rounded-full shadow-2xl transition-all ${
            recording ? 'bg-rose-600 hover:bg-rose-700 animate-pulse'
            : thinking ? 'bg-gray-600 cursor-wait'
            : 'bg-kirobi-600 hover:bg-kirobi-700 hover:scale-110'
          }`}
        >
          {thinking ? (<ArrowPathIcon className="w-10 h-10 animate-spin" />)
            : recording ? (<StopIcon className="w-10 h-10" />)
            : (<MicrophoneIcon className="w-10 h-10" />)}
        </button>
      </div>
    </div>
  );
}
