'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  PhotoIcon,
  MusicalNoteIcon,
  FilmIcon,
  SparklesIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

type Tab = 'image' | 'music' | 'video';

const IMG_API = '/api/image-generation';
const MUSIC_API = '/api/music-generation';
const VIDEO_API = '/api/video-generation';

interface ImageItem {
  id: string;
  prompt: string;
  model_used: string;
  zone: string;
  width: number;
  height: number;
  created_at: string;
}

interface TrackItem {
  id: string;
  prompt: string;
  enhanced_prompt?: string;
  genre?: string;
  duration_seconds: number;
  model_used: string;
  zone: string;
  is_placeholder: boolean;
  created_at: string;
}

interface VideoJob {
  id: string;
  prompt: string;
  resolution: string;
  duration_seconds: number;
  zone: string;
  status: string;
  file_path?: string | null;
  created_at: string;
  completed_at?: string | null;
  error?: string | null;
}

export default function CreativePage() {
  const router = useRouter();
  const [token, setToken] = useState('');
  const [tab, setTab] = useState<Tab>('image');

  useEffect(() => {
    const t = typeof window !== 'undefined' ? localStorage.getItem('kirobi_token') : null;
    if (!t) { router.push('/'); return; }
    setToken(t);
  }, [router]);

  if (!token) return null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 text-white pb-24">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <header className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <SparklesIcon className="w-8 h-8 text-fuchsia-400" />
            Kreativ-Studio
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Bilder, Musik und Videos — alles lokal auf deiner RTX 3090.
          </p>
        </header>

        <div className="flex gap-2 mb-6 border-b border-gray-800">
          <TabBtn active={tab === 'image'} onClick={() => setTab('image')} icon={PhotoIcon} label="Bild" />
          <TabBtn active={tab === 'music'} onClick={() => setTab('music')} icon={MusicalNoteIcon} label="Musik" />
          <TabBtn active={tab === 'video'} onClick={() => setTab('video')} icon={FilmIcon} label="Video" />
        </div>

        {tab === 'image' && <ImagePanel />}
        {tab === 'music' && <MusicPanel />}
        {tab === 'video' && <VideoPanel />}
      </div>
    </div>
  );
}

function TabBtn({ active, onClick, icon: Icon, label }: { active: boolean; onClick: () => void; icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
        active ? 'border-fuchsia-500 text-white' : 'border-transparent text-gray-400 hover:text-white hover:border-gray-700'
      }`}
    >
      <Icon className="w-5 h-5" />
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
}

// ---------- Image ----------
function ImagePanel() {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('llava:13b');
  const [width, setWidth] = useState(512);
  const [height, setHeight] = useState(512);
  const [zone, setZone] = useState('WORKSPACE');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [items, setItems] = useState<ImageItem[]>([]);

  async function load() {
    try {
      const r = await axios.get<ImageItem[]>(`${IMG_API}/images?limit=24`);
      setItems(r.data);
    } catch (e) { console.error(e); }
  }
  useEffect(() => { load(); }, []);

  async function generate() {
    if (!prompt.trim()) return;
    setBusy(true); setErr('');
    try {
      await axios.post(`${IMG_API}/generate`, { prompt, model, width, height, zone });
      setPrompt('');
      await load();
    } catch (e: unknown) {
      const m = e instanceof Error ? e.message : String(e);
      setErr(`Fehler: ${m}`);
    } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Beschreibe das Bild ... z.B. 'Sonnenuntergang ueber den Bergen, fotorealistisch'"
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm h-24 focus:outline-none focus:border-fuchsia-500 resize-none"
        />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
          <FieldSelect label="Modell" value={model} onChange={setModel}
            options={[['llava:13b','LLaVA 13B'],['llava:7b','LLaVA 7B'],['stable-diffusion','Stable Diffusion']]} />
          <FieldSelect label="Breite" value={String(width)} onChange={(v) => setWidth(Number(v))}
            options={[['256','256'],['512','512'],['768','768'],['1024','1024']]} />
          <FieldSelect label="Hoehe" value={String(height)} onChange={(v) => setHeight(Number(v))}
            options={[['256','256'],['512','512'],['768','768'],['1024','1024']]} />
          <FieldSelect label="Zone" value={zone} onChange={setZone}
            options={[['PUBLIC','PUBLIC'],['WORKSPACE','WORKSPACE'],['FAMILY_PRIVATE','FAMILY_PRIVATE']]} />
        </div>
        {err && <p className="text-sm text-rose-400 mt-3">{err}</p>}
        <button
          onClick={generate}
          disabled={busy || !prompt.trim()}
          className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-fuchsia-600 hover:bg-fuchsia-700 disabled:bg-gray-700 rounded-lg text-sm font-medium transition"
        >
          {busy ? <ArrowPathIcon className="w-4 h-4 animate-spin" /> : <PhotoIcon className="w-4 h-4" />}
          {busy ? 'Generiere...' : 'Bild generieren'}
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {items.map((it) => (
          <a key={it.id} href={`${IMG_API}/file/${it.id}`} target="_blank" rel="noreferrer"
             className="group bg-gray-900/60 border border-gray-800 rounded-xl overflow-hidden hover:border-fuchsia-500 transition">
            <img src={`${IMG_API}/file/${it.id}`} alt={it.prompt} className="w-full aspect-square object-cover" />
            <div className="p-2">
              <p className="text-xs text-gray-300 line-clamp-2">{it.prompt}</p>
              <p className="text-[10px] text-gray-500 mt-1">{it.model_used} · {it.width}×{it.height}</p>
            </div>
          </a>
        ))}
        {items.length === 0 && <p className="text-gray-500 text-sm col-span-full text-center py-8">Noch keine Bilder generiert.</p>}
      </div>
    </div>
  );
}

// ---------- Music ----------
function MusicPanel() {
  const [prompt, setPrompt] = useState('');
  const [genre, setGenre] = useState('ambient');
  const [duration, setDuration] = useState(15);
  const [zone, setZone] = useState('WORKSPACE');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [items, setItems] = useState<TrackItem[]>([]);

  async function load() {
    try {
      const r = await axios.get<TrackItem[]>(`${MUSIC_API}/tracks?limit=24`);
      setItems(r.data);
    } catch (e) { console.error(e); }
  }
  useEffect(() => { load(); }, []);

  async function generate() {
    if (!prompt.trim()) return;
    setBusy(true); setErr('');
    try {
      await axios.post(`${MUSIC_API}/generate`, { prompt, genre, duration_seconds: duration, zone });
      setPrompt('');
      await load();
    } catch (e: unknown) {
      const m = e instanceof Error ? e.message : String(e);
      setErr(`Fehler: ${m}`);
    } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Beschreibe den Track ... z.B. 'entspannte Klavier-Melodie mit Regen im Hintergrund'"
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm h-24 focus:outline-none focus:border-fuchsia-500 resize-none"
        />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-3">
          <FieldSelect label="Genre" value={genre} onChange={setGenre}
            options={[['ambient','Ambient'],['electronic','Electronic'],['classical','Klassik'],['jazz','Jazz'],['rock','Rock'],['lofi','Lo-Fi'],['cinematic','Cinematic']]} />
          <FieldSelect label="Dauer" value={String(duration)} onChange={(v) => setDuration(Number(v))}
            options={[['10','10s'],['15','15s'],['30','30s'],['60','60s']]} />
          <FieldSelect label="Zone" value={zone} onChange={setZone}
            options={[['PUBLIC','PUBLIC'],['WORKSPACE','WORKSPACE'],['FAMILY_PRIVATE','FAMILY_PRIVATE']]} />
        </div>
        {err && <p className="text-sm text-rose-400 mt-3">{err}</p>}
        <button
          onClick={generate}
          disabled={busy || !prompt.trim()}
          className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-fuchsia-600 hover:bg-fuchsia-700 disabled:bg-gray-700 rounded-lg text-sm font-medium transition"
        >
          {busy ? <ArrowPathIcon className="w-4 h-4 animate-spin" /> : <MusicalNoteIcon className="w-4 h-4" />}
          {busy ? 'Generiere...' : 'Track generieren'}
        </button>
      </div>

      <div className="space-y-3">
        {items.map((it) => (
          <div key={it.id} className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 line-clamp-2">{it.prompt}</p>
                {it.enhanced_prompt && it.enhanced_prompt !== it.prompt && (
                  <p className="text-xs text-gray-500 mt-1 line-clamp-2">↳ {it.enhanced_prompt}</p>
                )}
              </div>
              <div className="text-right flex-shrink-0">
                <span className="inline-block px-2 py-0.5 bg-gray-800 rounded text-xs text-gray-300">{it.genre}</span>
                <p className="text-[10px] text-gray-500 mt-1">{it.duration_seconds}s · {it.model_used}</p>
                {it.is_placeholder && <p className="text-[10px] text-amber-400">⚠ Placeholder (AudioCraft fehlt)</p>}
              </div>
            </div>
            <audio controls src={`${MUSIC_API}/file/${it.id}`} className="w-full mt-2" />
          </div>
        ))}
        {items.length === 0 && <p className="text-gray-500 text-sm text-center py-8">Noch keine Tracks generiert.</p>}
      </div>
    </div>
  );
}

// ---------- Video ----------
function VideoPanel() {
  const [prompt, setPrompt] = useState('');
  const [resolution, setResolution] = useState('512x512');
  const [duration, setDuration] = useState(4);
  const [zone, setZone] = useState('WORKSPACE');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [items, setItems] = useState<VideoJob[]>([]);

  async function load() {
    try {
      const r = await axios.get<VideoJob[]>(`${VIDEO_API}/jobs`);
      setItems(r.data);
    } catch (e) { console.error(e); }
  }
  useEffect(() => {
    load();
    const int = setInterval(load, 5000);
    return () => clearInterval(int);
  }, []);

  async function generate() {
    if (!prompt.trim()) return;
    setBusy(true); setErr('');
    try {
      await axios.post(`${VIDEO_API}/generate`, { prompt, resolution, duration, zone });
      setPrompt('');
      await load();
    } catch (e: unknown) {
      const m = e instanceof Error ? e.message : String(e);
      setErr(`Fehler: ${m}`);
    } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Beschreibe das Video ... z.B. 'fliegender Adler ueber einer Bergkette, Sonnenaufgang'"
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm h-24 focus:outline-none focus:border-fuchsia-500 resize-none"
        />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-3">
          <FieldSelect label="Aufloesung" value={resolution} onChange={setResolution}
            options={[['256x256','256×256'],['512x512','512×512'],['768x768','768×768'],['1024x576','1024×576']]} />
          <FieldSelect label="Dauer" value={String(duration)} onChange={(v) => setDuration(Number(v))}
            options={[['2','2s'],['4','4s'],['8','8s'],['16','16s']]} />
          <FieldSelect label="Zone" value={zone} onChange={setZone}
            options={[['PUBLIC','PUBLIC'],['WORKSPACE','WORKSPACE'],['FAMILY_PRIVATE','FAMILY_PRIVATE']]} />
        </div>
        {err && <p className="text-sm text-rose-400 mt-3">{err}</p>}
        <button
          onClick={generate}
          disabled={busy || !prompt.trim()}
          className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-fuchsia-600 hover:bg-fuchsia-700 disabled:bg-gray-700 rounded-lg text-sm font-medium transition"
        >
          {busy ? <ArrowPathIcon className="w-4 h-4 animate-spin" /> : <FilmIcon className="w-4 h-4" />}
          {busy ? 'Job wird erstellt...' : 'Video-Job starten'}
        </button>
      </div>

      <div className="space-y-3">
        {items.map((it) => (
          <div key={it.id} className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 line-clamp-2">{it.prompt}</p>
                <p className="text-xs text-gray-500 mt-1">{it.resolution} · {it.duration_seconds}s · {new Date(it.created_at).toLocaleString('de-DE')}</p>
                {it.error && <p className="text-xs text-rose-400 mt-1">{it.error}</p>}
              </div>
              <span className={`flex-shrink-0 px-2 py-1 text-xs rounded ${
                it.status === 'completed' ? 'bg-emerald-900 text-emerald-300'
                : it.status === 'failed' ? 'bg-rose-900 text-rose-300'
                : it.status === 'processing' ? 'bg-amber-900 text-amber-300'
                : 'bg-gray-800 text-gray-400'
              }`}>{it.status}</span>
            </div>
            {it.status === 'completed' && (
              <video controls src={`${VIDEO_API}/file/${it.id}`} className="w-full mt-2 rounded-lg" />
            )}
          </div>
        ))}
        {items.length === 0 && <p className="text-gray-500 text-sm text-center py-8">Noch keine Videos generiert.</p>}
      </div>
    </div>
  );
}

// ---------- helpers ----------
function FieldSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: [string, string][] }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-400 mb-1 uppercase tracking-wider">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-fuchsia-500"
      >
        {options.map(([v, l]) => (<option key={v} value={v}>{l}</option>))}
      </select>
    </div>
  );
}
