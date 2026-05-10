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

interface TurnEntry {
  id: string;
  user_text: string;
  assistant_text: string;
  audio_url: string;
  agent: string;
  voice: string;
  tone: string;
  model?: string;
  created_at: string;
}

interface TurnResponse {
  conversation_id: string;
  transcript: string;
  reply_text: string;
  reply_text_tts: string;
  audio_url: string;
  agent: string;
  tone: string;
  voice: string;
  model?: string;
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

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [history, setHistory] = useState<TurnEntry[]>([]);
  const [recording, setRecording] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string>('');
  const [statusMsg, setStatusMsg] = useState<string>('Bereit. Druecke das Mikrofon, um zu starten.');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioElRef = useRef<HTMLAudioElement | null>(null);

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
        setError('Konnte Voice-Settings nicht laden.');
      }
    })();
  }, [token]);

  async function startRecording() {
    try {
      setError('');
      setStatusMsg('Hoere zu...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true } });
      streamRef.current = stream;
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mr.onstop = handleRecorderStop;
      mr.start();
      mediaRecorderRef.current = mr;
      setRecording(true);
    } catch (err: unknown) {
      console.error('Mic error', err);
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Mikrofon-Zugriff fehlgeschlagen: ${msg}`);
      setStatusMsg('Bereit.');
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    setRecording(false);
  }

  async function handleRecorderStop() {
    if (audioChunksRef.current.length === 0) { setStatusMsg('Bereit.'); return; }
    const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
    audioChunksRef.current = [];
    await sendTurn(blob);
  }

  async function sendTurn(blob: Blob) {
    setThinking(true);
    setStatusMsg('Denkt nach...');
    try {
      const fd = new FormData();
      fd.append('audio_file', blob, 'turn.webm');
      const params = new URLSearchParams();
      if (conversationId) params.set('conversation_id', conversationId);
      params.set('agent', agent);
      params.set('tone', tone);
      params.set('voice', voice);
      const url = `${VOICE_BASE}/conversation/turn?${params.toString()}`;
      const resp = await axios.post<TurnResponse>(url, fd, { timeout: 180000 });
      const data = resp.data;
      setConversationId(data.conversation_id);
      const entry: TurnEntry = {
        id: `${Date.now()}`,
        user_text: data.transcript,
        assistant_text: data.reply_text,
        audio_url: `${VOICE_BASE}${data.audio_url}`,
        agent: data.agent,
        voice: data.voice,
        tone: data.tone,
        model: data.model,
        created_at: new Date().toISOString(),
      };
      setHistory((h) => [...h, entry]);
      setStatusMsg('Antwort fertig.');
      if (autoPlay && audioElRef.current) {
        audioElRef.current.src = entry.audio_url;
        try { await audioElRef.current.play(); } catch { /* autoplay blocked */ }
      }
    } catch (err: unknown) {
      console.error('Turn failed', err);
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Fehler: ${msg}`);
      setStatusMsg('Fehler — bitte erneut versuchen.');
    } finally {
      setThinking(false);
    }
  }

  function resetConversation() {
    setConversationId(null);
    setHistory([]);
    setStatusMsg('Neue Konversation gestartet.');
  }

  function playEntry(entry: TurnEntry) {
    if (audioElRef.current) {
      audioElRef.current.src = entry.audio_url;
      audioElRef.current.play().catch(() => {});
    }
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
              onChange={(e) => { setAgent(e.target.value); setConversationId(null); }}
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
                {e.model && (<><span>·</span><span className="text-gray-600">{e.model}</span></>)}
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
