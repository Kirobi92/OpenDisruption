'use client';

/**
 * Voice Studio — Voicebox-kompatibles Modul
 * Funktionalitäten: Voice-Profile CRUD, Sample-Upload/-Aufnahme,
 * Effektkette, Audio-Generierung, History
 * Zone: WORKSPACE
 */

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  MicrophoneIcon,
  PlusIcon,
  TrashIcon,
  ArrowPathIcon,
  StopIcon,
  ArrowDownTrayIcon,
  UserCircleIcon,
  ClockIcon,
  SpeakerWaveIcon,
  DocumentArrowUpIcon,
  CheckIcon,
  XMarkIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline';

const VOICE_API = '/api/voice-processing';

type StudioTab = 'generate' | 'profiles' | 'history';

interface VoiceProfile {
  id: string;
  name: string;
  description: string;
  language: string;
  piper_voice: string;
  gender: string;
  speed: number;
  pitch: number;
  sample_count: number;
  created_at: string;
}

interface VoiceSample {
  id: string;
  profile_id: string;
  filename: string;
  file_path: string;
  reference_text: string;
  duration_s: number;
  created_at: string;
}

interface GenerationEntry {
  url: string;
  text: string;
  voice: string;
  ts: string;
}

const PIPER_VOICES = [
  'de_DE-thorsten-high',
  'de_DE-thorsten_emotional-medium',
  'de_DE-eva_k-x_low',
  'de_DE-kerstin-low',
  'en_US-ryan-high',
  'en_US-lessac-high',
  'en_GB-semaine-medium',
  'fr_FR-upmc-medium',
  'es_ES-sharvard-medium',
];

export default function VoiceStudioPage() {
  const router = useRouter();
  const [token, setToken] = useState('');
  const [tab, setTab] = useState<StudioTab>('generate');

  useEffect(() => {
    const t = typeof window !== 'undefined' ? localStorage.getItem('kirobi_token') : null;
    if (!t) { router.push('/'); return; }
    setToken(t);
  }, [router]);

  if (!token) return null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 text-white pb-24">
      <div className="max-w-5xl mx-auto px-4 py-8">
        <header className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <MicrophoneIcon className="w-8 h-8 text-cyan-400" />
            Voice Studio
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Voice-Profile, Effekte und Sprachsynthese — inspiriert von Voicebox.
          </p>
        </header>

        <div className="flex gap-2 mb-6 border-b border-gray-800">
          <StudioTabBtn active={tab === 'generate'} onClick={() => setTab('generate')}
            icon={SpeakerWaveIcon} label="Generieren" />
          <StudioTabBtn active={tab === 'profiles'} onClick={() => setTab('profiles')}
            icon={UserCircleIcon} label="Profile" />
          <StudioTabBtn active={tab === 'history'} onClick={() => setTab('history')}
            icon={ClockIcon} label="Verlauf" />
        </div>

        {tab === 'generate' && <GeneratePanel token={token} />}
        {tab === 'profiles' && <ProfilesPanel token={token} />}
        {tab === 'history' && <HistoryPanel />}
      </div>
    </div>
  );
}

function StudioTabBtn({ active, onClick, icon: Icon, label }: {
  active: boolean; onClick: () => void;
  icon: React.ComponentType<{ className?: string }>; label: string;
}) {
  return (
    <button onClick={onClick}
      className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
        active ? 'border-cyan-500 text-white' : 'border-transparent text-gray-400 hover:text-white hover:border-gray-700'
      }`}>
      <Icon className="w-5 h-5" />
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
}

// ─── Generate Panel ────────────────────────────────────────────────────────────

function GeneratePanel({ token }: { token: string }) {
  const [text, setText] = useState('');
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const [voice, setVoice] = useState('de_DE-thorsten-high');
  const [tone, setTone] = useState('neutral');
  const [speed, setSpeed] = useState(1.0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [history, setHistory] = useState<GenerationEntry[]>(() => {
    if (typeof window === 'undefined') return [];
    try { return JSON.parse(localStorage.getItem('voice_studio_history') || '[]'); } catch { return []; }
  });
  const [effects, setEffects] = useState<{ type: string; enabled: boolean; params: Record<string, number> }[]>([]);

  useEffect(() => {
    axios.get(`${VOICE_API}/profiles`)
      .then((r) => setProfiles(r.data))
      .catch(() => {});
  }, []);

  function addEffect(type: string) {
    const defaults: Record<string, Record<string, number>> = {
      reverb: { room_size: 0.5, damping: 0.5, wet: 0.3 },
      pitch_shift: { semitones: 0 },
      speed_change: { factor: 1.0 },
      eq: { bass: 0, mid: 0, treble: 0 },
    };
    setEffects((e) => [...e, { type, enabled: true, params: defaults[type] || {} }]);
  }

  function removeEffect(idx: number) {
    setEffects((e) => e.filter((_, i) => i !== idx));
  }

  function toggleEffect(idx: number) {
    setEffects((e) => e.map((fx, i) => i === idx ? { ...fx, enabled: !fx.enabled } : fx));
  }

  function updateEffectParam(idx: number, key: string, val: number) {
    setEffects((e) => e.map((fx, i) => i === idx ? { ...fx, params: { ...fx.params, [key]: val } } : fx));
  }

  async function generate() {
    if (!text.trim()) return;
    setBusy(true); setErr(''); setAudioUrl('');
    try {
      const headers = { Authorization: `Bearer ${token}` };
      let audioPath: string | undefined;

      if (selectedProfile) {
        const r = await axios.post(`${VOICE_API}/profiles/${selectedProfile}/generate`,
          { text, tone }, { headers });
        audioPath = r.data?.audio_url;
      } else {
        const r = await axios.post(`${VOICE_API}/tts/synthesize`, { text, voice, tone, speed }, { headers });
        audioPath = r.data?.audio_url;
      }

      if (audioPath) {
        const url = audioPath.startsWith('http') ? audioPath
          : audioPath.startsWith('/audio/') ? `${VOICE_API}${audioPath}`
          : `${VOICE_API}/audio/${audioPath.split('/').pop()}`;
        const entry: GenerationEntry = { url, text: text.slice(0, 100), voice, ts: new Date().toISOString() };
        const next = [entry, ...history].slice(0, 50);
        setHistory(next);
        if (typeof window !== 'undefined') localStorage.setItem('voice_studio_history', JSON.stringify(next));
        setAudioUrl(url);
      }
    } catch (e: unknown) {
      const r = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setErr(`Fehler: ${r || String(e)}`);
    } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
          <SpeakerWaveIcon className="w-4 h-4 text-cyan-400" />
          Text-zu-Sprache
        </h2>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Gib hier deinen Text ein, der gesprochen werden soll..."
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm h-32 focus:outline-none focus:border-cyan-500 resize-y"
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {profiles.length > 0 && (
            <div>
              <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Voice-Profil</label>
              <select
                value={selectedProfile}
                onChange={(e) => setSelectedProfile(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
              >
                <option value="">— Kein Profil —</option>
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} ({p.piper_voice})</option>
                ))}
              </select>
            </div>
          )}
          {!selectedProfile && (
            <>
              <div>
                <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Stimme</label>
                <select value={voice} onChange={(e) => setVoice(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500">
                  {PIPER_VOICES.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Speed: {speed.toFixed(1)}</label>
                <input type="range" min="0.5" max="2.0" step="0.1" value={speed}
                  onChange={(e) => setSpeed(Number(e.target.value))}
                  className="w-full accent-cyan-500 mt-2" />
              </div>
            </>
          )}
          <div>
            <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Ton</label>
            <select value={tone} onChange={(e) => setTone(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500">
              <option value="neutral">Neutral</option>
              <option value="friendly">Freundlich</option>
              <option value="professional">Professionell</option>
              <option value="calm">Ruhig</option>
              <option value="energetic">Energetisch</option>
            </select>
          </div>
        </div>

        {/* Effects Chain */}
        <div className="border border-gray-700 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h3 className="text-xs font-semibold text-gray-300 flex items-center gap-1.5 uppercase tracking-wider">
              <AdjustmentsHorizontalIcon className="w-4 h-4" /> Effektkette
            </h3>
            <div className="flex gap-2 flex-wrap">
              {['reverb', 'pitch_shift', 'speed_change', 'eq'].map((type) => (
                <button key={type} onClick={() => addEffect(type)}
                  className="px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded text-xs transition">
                  + {type.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>
          {effects.length === 0 && (
            <p className="text-xs text-gray-600 text-center py-2">Keine Effekte aktiv</p>
          )}
          {effects.map((fx, idx) => (
            <div key={idx} className={`bg-gray-800 rounded-lg p-3 border ${fx.enabled ? 'border-cyan-800' : 'border-gray-700 opacity-50'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-200 capitalize">{fx.type.replace('_', ' ')}</span>
                <div className="flex gap-2">
                  <button onClick={() => toggleEffect(idx)}
                    className={`w-6 h-6 rounded flex items-center justify-center ${fx.enabled ? 'bg-cyan-700' : 'bg-gray-700'}`}>
                    {fx.enabled ? <CheckIcon className="w-3.5 h-3.5" /> : <XMarkIcon className="w-3.5 h-3.5" />}
                  </button>
                  <button onClick={() => removeEffect(idx)}
                    className="w-6 h-6 rounded flex items-center justify-center bg-rose-900 hover:bg-rose-800">
                    <TrashIcon className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(fx.params).map(([key, val]) => (
                  <div key={key}>
                    <label className="block text-[10px] text-gray-500 uppercase mb-0.5">{key.replace('_', ' ')}: {(val as number).toFixed(2)}</label>
                    <input type="range" min="-12" max="12" step="0.1" value={val as number}
                      onChange={(e) => updateEffectParam(idx, key, Number(e.target.value))}
                      className="w-full accent-cyan-500" />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {err && <p className="text-sm text-rose-400">{err}</p>}

        <button onClick={generate} disabled={busy || !text.trim()}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-700 rounded-lg text-sm font-medium transition">
          {busy ? <ArrowPathIcon className="w-4 h-4 animate-spin" /> : <SpeakerWaveIcon className="w-4 h-4" />}
          {busy ? 'Generiere...' : 'Sprache generieren'}
        </button>
      </div>

      {audioUrl && (
        <div className="bg-gray-900/60 border border-cyan-800 rounded-xl p-4 space-y-3">
          <h3 className="text-sm font-semibold text-cyan-300">Ergebnis</h3>
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <audio controls src={audioUrl} className="w-full" autoPlay />
          <a href={audioUrl} download="voice-output.wav"
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs transition">
            <ArrowDownTrayIcon className="w-3.5 h-3.5" /> Herunterladen
          </a>
        </div>
      )}
    </div>
  );
}

// ─── Profiles Panel ────────────────────────────────────────────────────────────

function ProfilesPanel({ token }: { token: string }) {
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [selected, setSelected] = useState<VoiceProfile | null>(null);
  const [samples, setSamples] = useState<VoiceSample[]>([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: '', description: '', language: 'de_DE',
    piper_voice: 'de_DE-thorsten-high', gender: 'neutral',
    speed: 1.0, pitch: 0.0,
  });
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const [refText, setRefText] = useState('');
  const [recording, setRecording] = useState(false);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function loadProfiles() {
    setLoading(true);
    try {
      const r = await axios.get<VoiceProfile[]>(`${VOICE_API}/profiles`);
      setProfiles(r.data);
    } catch (_e) { /* ignore */ }
    finally { setLoading(false); }
  }

  async function loadSamples(profileId: string) {
    try {
      const r = await axios.get<VoiceSample[]>(`${VOICE_API}/profiles/${profileId}/samples`);
      setSamples(r.data);
    } catch (_e) { setSamples([]); }
  }

  useEffect(() => { loadProfiles(); }, []);
  useEffect(() => {
    if (selected) loadSamples(selected.id);
    else setSamples([]);
  }, [selected]);

  async function createProfile() {
    setBusy(true);
    try {
      await axios.post(`${VOICE_API}/profiles`, form, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCreating(false);
      setForm({ name: '', description: '', language: 'de_DE', piper_voice: 'de_DE-thorsten-high', gender: 'neutral', speed: 1.0, pitch: 0.0 });
      await loadProfiles();
    } catch (_e) { /* ignore */ }
    finally { setBusy(false); }
  }

  async function deleteProfile(id: string) {
    await axios.delete(`${VOICE_API}/profiles/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (selected?.id === id) setSelected(null);
    await loadProfiles();
  }

  async function uploadSample(file: File) {
    if (!selected) return;
    const fd = new FormData();
    fd.append('file', file);
    fd.append('reference_text', refText);
    setBusy(true);
    try {
      await axios.post(`${VOICE_API}/profiles/${selected.id}/samples`, fd, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setRefText('');
      await loadSamples(selected.id);
    } catch (_e) { /* ignore */ }
    finally { setBusy(false); }
  }

  async function deleteSample(sampleId: string) {
    if (!selected) return;
    await axios.delete(`${VOICE_API}/profiles/${selected.id}/samples/${sampleId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    await loadSamples(selected.id);
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
        await uploadSample(new File([blob], 'recording.wav', { type: 'audio/wav' }));
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      mediaRef.current = mr;
      setRecording(true);
    } catch (_e) { alert('Mikrofon nicht verfügbar'); }
  }

  function stopRecording() {
    mediaRef.current?.stop();
    setRecording(false);
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Profile List */}
      <div className="md:col-span-1 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-200">Voice-Profile</h2>
          <button onClick={() => setCreating(!creating)}
            className="inline-flex items-center gap-1 px-3 py-1.5 bg-cyan-700 hover:bg-cyan-600 rounded-lg text-xs transition">
            <PlusIcon className="w-3.5 h-3.5" /> Neu
          </button>
        </div>

        {creating && (
          <div className="bg-gray-900/60 border border-cyan-700 rounded-xl p-4 space-y-3">
            <h3 className="text-xs font-semibold text-cyan-300 uppercase tracking-wider">Neues Profil</h3>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Name"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-cyan-500" />
            <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Beschreibung (optional)"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-cyan-500" />
            <select value={form.piper_voice} onChange={(e) => setForm({ ...form, piper_voice: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-cyan-500">
              {PIPER_VOICES.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Speed: {form.speed.toFixed(1)}</label>
                <input type="range" min="0.5" max="2.0" step="0.1" value={form.speed}
                  onChange={(e) => setForm({ ...form, speed: Number(e.target.value) })}
                  className="w-full accent-cyan-500" />
              </div>
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Pitch: {form.pitch.toFixed(1)}</label>
                <input type="range" min="-10" max="10" step="0.5" value={form.pitch}
                  onChange={(e) => setForm({ ...form, pitch: Number(e.target.value) })}
                  className="w-full accent-cyan-500" />
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={createProfile} disabled={busy || !form.name.trim()}
                className="flex-1 py-1.5 bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-700 rounded-lg text-xs font-medium transition">
                {busy ? 'Erstelle...' : 'Erstellen'}
              </button>
              <button onClick={() => setCreating(false)}
                className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-xs transition">
                Abbrechen
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <p className="text-gray-500 text-sm text-center py-4">Lade Profile...</p>
        ) : profiles.length === 0 ? (
          <div className="text-center py-8 text-gray-600 text-sm">
            <UserCircleIcon className="w-12 h-12 mx-auto mb-2 opacity-20" />
            <p>Noch keine Profile.</p>
          </div>
        ) : (
          profiles.map((p) => (
            <div key={p.id}
              onClick={() => setSelected(p.id === selected?.id ? null : p)}
              className={`cursor-pointer bg-gray-900/60 border rounded-xl p-3 transition group ${
                selected?.id === p.id ? 'border-cyan-500' : 'border-gray-800 hover:border-gray-600'
              }`}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-200">{p.name}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">{p.piper_voice}</p>
                  <p className="text-[10px] text-gray-500">{p.sample_count} Samples · Speed {p.speed.toFixed(1)}</p>
                </div>
                <button onClick={(e) => { e.stopPropagation(); deleteProfile(p.id); }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-rose-900 rounded transition">
                  <TrashIcon className="w-4 h-4 text-rose-400" />
                </button>
              </div>
              {p.description && (
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{p.description}</p>
              )}
            </div>
          ))
        )}
      </div>

      {/* Profile Detail / Samples */}
      <div className="md:col-span-2">
        {!selected ? (
          <div className="flex items-center justify-center h-64 text-gray-600">
            <div className="text-center">
              <UserCircleIcon className="w-16 h-16 mx-auto mb-3 opacity-20" />
              <p className="text-sm">Wähle ein Profil aus der Liste</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-gray-200 mb-2">{selected.name}</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs text-gray-500">
                <div><span className="text-gray-400">Stimme:</span> {selected.piper_voice}</div>
                <div><span className="text-gray-400">Sprache:</span> {selected.language}</div>
                <div><span className="text-gray-400">Speed:</span> {selected.speed.toFixed(1)}x</div>
                <div><span className="text-gray-400">Pitch:</span> {selected.pitch.toFixed(1)}</div>
                <div><span className="text-gray-400">Samples:</span> {selected.sample_count}</div>
              </div>
            </div>

            <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 space-y-3">
              <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                <DocumentArrowUpIcon className="w-4 h-4" /> Referenz-Samples
              </h3>
              <input
                value={refText}
                onChange={(e) => setRefText(e.target.value)}
                placeholder="Referenztext (was im Sample gesprochen wird)"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-cyan-500"
              />
              <div className="flex gap-3 flex-wrap">
                <button onClick={() => fileRef.current?.click()}
                  className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs transition">
                  <DocumentArrowUpIcon className="w-3.5 h-3.5" /> Datei hochladen
                </button>
                <input ref={fileRef} type="file" accept="audio/*" className="hidden"
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadSample(f); e.target.value = ''; }} />
                <button
                  onClick={recording ? stopRecording : startRecording}
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition ${
                    recording ? 'bg-rose-700 hover:bg-rose-600 animate-pulse' : 'bg-gray-800 hover:bg-gray-700'
                  }`}>
                  {recording ? <StopIcon className="w-3.5 h-3.5" /> : <MicrophoneIcon className="w-3.5 h-3.5" />}
                  {recording ? 'Aufnahme stoppen' : 'Aufnehmen'}
                </button>
              </div>

              <div className="space-y-2 mt-2">
                {samples.map((s) => (
                  <div key={s.id} className="bg-gray-800 rounded-lg p-3 flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-gray-300 truncate">{s.filename}</p>
                      {s.reference_text && (
                        <p className="text-[10px] text-gray-500 truncate">{s.reference_text}</p>
                      )}
                      <p className="text-[10px] text-gray-600">{s.duration_s > 0 ? `${s.duration_s.toFixed(1)}s` : ''}</p>
                    </div>
                    <button onClick={() => deleteSample(s.id)}
                      className="p-1 hover:bg-rose-900 rounded transition flex-shrink-0">
                      <TrashIcon className="w-3.5 h-3.5 text-rose-400" />
                    </button>
                  </div>
                ))}
                {samples.length === 0 && (
                  <p className="text-xs text-gray-600 text-center py-2">Noch keine Samples hochgeladen.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── History Panel ────────────────────────────────────────────────────────────

function HistoryPanel() {
  const [history] = useState<GenerationEntry[]>(() => {
    if (typeof window === 'undefined') return [];
    try { return JSON.parse(localStorage.getItem('voice_studio_history') || '[]'); } catch { return []; }
  });

  if (history.length === 0) {
    return (
      <div className="text-center py-16 text-gray-600">
        <ClockIcon className="w-12 h-12 mx-auto mb-3 opacity-20" />
        <p className="text-sm">Noch keine generierten Audios in dieser Session.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {history.map((entry, idx) => (
        <div key={idx} className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 space-y-2">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-200 line-clamp-2">{entry.text}</p>
              <p className="text-[10px] text-gray-500 mt-1">{entry.voice} · {new Date(entry.ts).toLocaleString('de-DE')}</p>
            </div>
            <a href={entry.url} download
              className="flex-shrink-0 p-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg transition">
              <ArrowDownTrayIcon className="w-4 h-4" />
            </a>
          </div>
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <audio controls src={entry.url} className="w-full" />
        </div>
      ))}
    </div>
  );
}
