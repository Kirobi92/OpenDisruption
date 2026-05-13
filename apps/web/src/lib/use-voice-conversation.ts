'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export interface VoiceConversationConfig {
  agent: string;
  voice: string;
  tone: string;
  language?: string;
  conversationId?: string | null;
  jwt: string;
  /**
   * 'oneshot' = client sends the full audio blob in one frame after recording stops (default).
   * 'chunked' = client streams the audio in 250 ms chunks while recording, then sends a JSON {type:'end'}
   *             frame to trigger STT. Reduces upload latency on long utterances.
   */
  mode?: 'oneshot' | 'chunked';
}

export interface VoiceTurn {
  id: string;
  user_text: string;
  assistant_text: string;
  audio_urls: string[];
  agent: string;
  voice: string;
  tone: string;
  conversation_id: string;
  created_at: string;
}

interface State {
  status: 'idle' | 'recording' | 'streaming' | 'speaking' | 'error';
  transcript: string;
  partialReply: string;
  error: string;
  conversationId: string | null;
  history: VoiceTurn[];
  audioChunks: number;
  firstAudioMs: number | null;
  totalMs: number | null;
}

const VOICE_BASE = '/voice';

// Build an absolute ws:// or wss:// URL for the WebSocket endpoint.
function wsUrl(): string {
  if (typeof window === 'undefined') return '';
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${proto}://${window.location.host}${VOICE_BASE}/conversation/ws`;
}

export function useVoiceConversation() {
  const [state, setState] = useState<State>({
    status: 'idle',
    transcript: '',
    partialReply: '',
    error: '',
    conversationId: null,
    history: [],
    audioChunks: 0,
    firstAudioMs: null,
    totalMs: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const audioQueueRef = useRef<string[]>([]);
  const playingRef = useRef<boolean>(false);
  const startTsRef = useRef<number>(0);
  const firstAudioRef = useRef<boolean>(false);
  const currentTurnRef = useRef<{
    user: string;
    reply: string;
    audio_urls: string[];
    conv_id: string;
    agent: string;
    voice: string;
    tone: string;
  }>({ user: '', reply: '', audio_urls: [], conv_id: '', agent: '', voice: '', tone: '' });
  const cfgRef = useRef<VoiceConversationConfig | null>(null);
  const autoplayRef = useRef<boolean>(true);

  // Lazily create a hidden <audio> element for sequential playback.
  useEffect(() => {
    if (typeof document === 'undefined') return;
    const el = document.createElement('audio');
    el.style.display = 'none';
    el.preload = 'auto';
    document.body.appendChild(el);
    audioElRef.current = el;

    const onEnded = () => {
      playingRef.current = false;
      playNext();
    };
    el.addEventListener('ended', onEnded);
    el.addEventListener('error', onEnded);
    return () => {
      el.removeEventListener('ended', onEnded);
      el.removeEventListener('error', onEnded);
      document.body.removeChild(el);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function playNext() {
    if (playingRef.current) return;
    const next = audioQueueRef.current.shift();
    if (!next || !audioElRef.current) {
      // queue drained
      setState((s) => (s.status === 'speaking' ? { ...s, status: 'idle' } : s));
      return;
    }
    playingRef.current = true;
    audioElRef.current.src = next;
    audioElRef.current.play().catch(() => {
      // Autoplay blocked or src error — drop it and continue.
      playingRef.current = false;
      playNext();
    });
  }

  function enqueueAudio(url: string) {
    audioQueueRef.current.push(url);
    if (autoplayRef.current) playNext();
  }

  function setAutoplay(enabled: boolean) {
    autoplayRef.current = enabled;
  }

  const reset = useCallback(() => {
    audioQueueRef.current = [];
    playingRef.current = false;
    if (audioElRef.current) {
      try { audioElRef.current.pause(); } catch { /* ignore */ }
      audioElRef.current.removeAttribute('src');
    }
    setState({
      status: 'idle',
      transcript: '',
      partialReply: '',
      error: '',
      conversationId: null,
      history: [],
      audioChunks: 0,
      firstAudioMs: null,
      totalMs: null,
    });
  }, []);

  const handleEvent = useCallback((evt: Record<string, unknown>) => {
    const type = String(evt.event ?? '');
    if (type === 'transcript') {
      const text = String(evt.text ?? '');
      currentTurnRef.current.user = text;
      setState((s) => ({ ...s, transcript: text, status: 'streaming' }));
    } else if (type === 'text_chunk') {
      const delta = String(evt.delta ?? '');
      currentTurnRef.current.reply += delta;
      setState((s) => ({ ...s, partialReply: s.partialReply + delta }));
    } else if (type === 'audio_chunk') {
      const url = `${VOICE_BASE}${String(evt.url ?? '')}`;
      currentTurnRef.current.audio_urls.push(url);
      if (!firstAudioRef.current) {
        firstAudioRef.current = true;
        setState((s) => ({ ...s, firstAudioMs: Date.now() - startTsRef.current, status: 'speaking' }));
      }
      enqueueAudio(url);
      setState((s) => ({ ...s, audioChunks: s.audioChunks + 1 }));
    } else if (type === 'done') {
      const convId = String(evt.conversation_id ?? '');
      const totalMs = Date.now() - startTsRef.current;
      currentTurnRef.current.conv_id = convId;
      const turn: VoiceTurn = {
        id: `${Date.now()}`,
        user_text: currentTurnRef.current.user,
        assistant_text: currentTurnRef.current.reply || String(evt.reply_text ?? ''),
        audio_urls: [...currentTurnRef.current.audio_urls],
        agent: currentTurnRef.current.agent,
        voice: currentTurnRef.current.voice,
        tone: currentTurnRef.current.tone,
        conversation_id: convId,
        created_at: new Date().toISOString(),
      };
      setState((s) => ({
        ...s,
        conversationId: convId,
        history: [...s.history, turn],
        totalMs,
      }));
      try { wsRef.current?.close(); } catch { /* ignore */ }
      wsRef.current = null;
    } else if (type === 'error') {
      const detail = String(evt.detail ?? 'unknown error');
      setState((s) => ({ ...s, status: 'error', error: detail }));
      try { wsRef.current?.close(); } catch { /* ignore */ }
      wsRef.current = null;
    }
  }, []);

  const stop = useCallback(async () => {
    const rec = recorderRef.current;
    const cfg = cfgRef.current;
    if (rec && rec.state !== 'inactive') {
      // Ensure all collected chunks are flushed to ondataavailable BEFORE we send.
      await new Promise<void>((resolve) => {
        rec.onstop = () => resolve();
        rec.stop();
      });
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    recorderRef.current = null;

    if (cfg?.mode === 'chunked') {
      // Tail-flush any pending blob, then signal end.
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        if (chunksRef.current.length > 0) {
          const tail = new Blob(chunksRef.current, { type: 'audio/webm' });
          chunksRef.current = [];
          const buf = await tail.arrayBuffer();
          ws.send(buf);
        }
        ws.send(JSON.stringify({ type: 'end' }));
      }
      setState((s) => ({ ...s, status: 'streaming' }));
    } else {
      // oneshot: send the whole blob now
      const ws = wsRef.current;
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
      chunksRef.current = [];
      if (ws && ws.readyState === WebSocket.OPEN) {
        const buf = await blob.arrayBuffer();
        ws.send(buf);
        setState((s) => ({ ...s, status: 'streaming' }));
      }
    }
  }, []);

  const start = useCallback(async (cfg: VoiceConversationConfig) => {
    cfgRef.current = cfg;
    firstAudioRef.current = false;
    audioQueueRef.current = [];
    playingRef.current = false;
    currentTurnRef.current = {
      user: '',
      reply: '',
      audio_urls: [],
      conv_id: '',
      agent: cfg.agent,
      voice: cfg.voice,
      tone: cfg.tone,
    };
    setState((s) => ({
      ...s,
      transcript: '',
      partialReply: '',
      error: '',
      audioChunks: 0,
      firstAudioMs: null,
      totalMs: null,
      status: 'recording',
    }));

    // Open WS up front so the upload is already-warm by the time the user stops.
    const ws = new WebSocket(wsUrl());
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onmessage = (e) => {
      try { handleEvent(JSON.parse(String(e.data))); } catch { /* ignore non-JSON */ }
    };
    ws.onerror = () => {
      setState((s) => ({ ...s, status: 'error', error: 'WebSocket-Verbindung fehlgeschlagen' }));
    };
    ws.onclose = () => {
      // If we never got a `done` event the server likely errored.
      setState((s) => (s.status === 'streaming' || s.status === 'recording'
        ? { ...s, status: 'idle' }
        : s));
    };

    await new Promise<void>((resolve, reject) => {
      ws.onopen = () => resolve();
      setTimeout(() => reject(new Error('WS open timeout')), 8000);
    }).catch((err) => {
      setState((s) => ({ ...s, status: 'error', error: String(err) }));
      throw err;
    });

    // Send config frame.
    ws.send(JSON.stringify({
      type: 'config',
      agent: cfg.agent,
      tone: cfg.tone,
      voice: cfg.voice,
      language: cfg.language ?? 'de',
      conversation_id: cfg.conversationId ?? null,
      jwt: cfg.jwt,
      mode: cfg.mode ?? 'oneshot',
    }));

    // Start mic capture.
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
    } catch (err) {
      setState((s) => ({ ...s, status: 'error', error: `Mikrofon: ${(err as Error).message}` }));
      try { ws.close(); } catch { /* ignore */ }
      throw err;
    }
    streamRef.current = stream;

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm';
    const recorder = new MediaRecorder(stream, { mimeType });
    chunksRef.current = [];

    if (cfg.mode === 'chunked') {
      // Stream each chunk to the server live.
      recorder.ondataavailable = (e: BlobEvent) => {
        if (e.data.size === 0) return;
        if (ws.readyState === WebSocket.OPEN) {
          e.data.arrayBuffer().then((buf) => ws.send(buf)).catch(() => { /* ignore */ });
        } else {
          chunksRef.current.push(e.data);
        }
      };
      recorder.start(250);
    } else {
      // Buffer everything client-side, send a single blob on stop.
      recorder.ondataavailable = (e: BlobEvent) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.start(250);
    }
    recorderRef.current = recorder;
    startTsRef.current = Date.now();
  }, [handleEvent]);

  return { state, start, stop, reset, setAutoplay };
}
