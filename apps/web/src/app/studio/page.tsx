'use client';

/**
 * Generative AI Studio — Open-Generative-AI-kompatibles Modul
 * Tabs: Image · Video · LipSync · Cinema
 * Alle wired an lokale Services (RTX 3090)
 * Zone: WORKSPACE
 */

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  PhotoIcon,
  FilmIcon,
  MusicalNoteIcon,
  SparklesIcon,
  ArrowPathIcon,
  ArrowDownTrayIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  PlayIcon,
  QueueListIcon,
  CameraIcon,
} from '@heroicons/react/24/outline';

const IMG_API  = '/api/image-generation';
const VID_API  = '/api/video-generation';
const MEDIA_API = '/api/media-processing';

type StudioTab = 'image' | 'video' | 'lipsync' | 'cinema';

interface ImageItem {
  id: string; prompt: string; model_used: string;
  zone: string; width: number; height: number; created_at: string;
}
interface VideoJob {
  id: string; prompt: string; resolution: string;
  duration_seconds: number; zone: string; status: string;
  file_path?: string | null; created_at: string; error?: string | null;
}
interface LipSyncJob {
  id: string; status: 'pending' | 'processing' | 'completed' | 'failed';
  video_url?: string; message?: string;
}

const IMAGE_MODELS = [
  { value: 'sdxl-turbo', label: 'SDXL-Turbo (lokal, RTX 3090)' },
  { value: 'stable-diffusion', label: 'Stable Diffusion' },
  { value: 'llava:13b', label: 'LLaVA 13B' },
  { value: 'llava:7b', label: 'LLaVA 7B' },
];

const CINEMA_PROMPTS = [
  { label: 'Epischer Opener', value: 'Cinematic wide shot, golden hour, dramatic landscape, film grain, anamorphic lens flares' },
  { label: 'Neon Noir', value: 'Rain-soaked city streets at night, neon reflections, atmospheric fog, cyberpunk aesthetic, high contrast' },
  { label: 'Nature Macro', value: 'Extreme close-up macro photography, morning dew on spider web, shallow depth of field, bokeh background' },
  { label: 'Sci-Fi Interior', value: 'Futuristic space station interior, glowing control panels, zero gravity, volumetric lighting' },
  { label: 'Fantasy Portal', value: 'Magical portal in ancient forest, mystical light rays, enchanted atmosphere, ethereal glow' },
];

export default function StudioPage() {
  const router = useRouter();
  const [token, setToken] = useState('');
  const [tab, setTab] = useState<StudioTab>('image');

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
            <SparklesIcon className="w-8 h-8 text-violet-400" />
            Generatives Studio
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Image · Video · LipSync · Cinema — alles lokal auf deiner RTX 3090.
            Inspiriert von Open Generative AI.
          </p>
        </header>

        <div className="flex gap-1 mb-6 bg-gray-900/60 border border-gray-800 rounded-xl p-1 overflow-x-auto">
          <TabPill active={tab === 'image'}   onClick={() => setTab('image')}   icon={PhotoIcon}  label="Image" color="violet" />
          <TabPill active={tab === 'video'}   onClick={() => setTab('video')}   icon={FilmIcon}   label="Video" color="blue" />
          <TabPill active={tab === 'lipsync'} onClick={() => setTab('lipsync')} icon={CameraIcon} label="Lip Sync" color="pink" />
          <TabPill active={tab === 'cinema'}  onClick={() => setTab('cinema')}  icon={QueueListIcon} label="Cinema" color="amber" />
        </div>

        {tab === 'image'   && <ImageStudio token={token} />}
        {tab === 'video'   && <VideoStudio token={token} />}
        {tab === 'lipsync' && <LipSyncStudio token={token} />}
        {tab === 'cinema'  && <CinemaStudio token={token} />}
      </div>
    </div>
  );
}

const COLORS: Record<string, string> = {
  violet: 'bg-violet-600',
  blue: 'bg-blue-600',
  pink: 'bg-pink-600',
  amber: 'bg-amber-600',
};

function TabPill({ active, onClick, icon: Icon, label, color }: {
  active: boolean; onClick: () => void;
  icon: React.ComponentType<{ className?: string }>; label: string; color: string;
}) {
  return (
    <button onClick={onClick}
      className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
        active ? `${COLORS[color]} text-white shadow` : 'text-gray-400 hover:text-white'
      }`}>
      <Icon className="w-4 h-4" />
      <span>{label}</span>
    </button>
  );
}

// ─── Image Studio ──────────────────────────────────────────────────────────────

function ImageStudio({ token }: { token: string }) {
  const [prompt, setPrompt] = useState('');
  const [negPrompt, setNegPrompt] = useState('');
  const [model, setModel] = useState('sdxl-turbo');
  const [width, setWidth] = useState(512);
  const [height, setHeight] = useState(512);
  const [steps, setSteps] = useState(20);
  const [guidance, setGuidance] = useState(7.5);
  const [zone, setZone] = useState('WORKSPACE');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [items, setItems] = useState<ImageItem[]>([]);
  const [preview, setPreview] = useState<ImageItem | null>(null);

  async function load() {
    try {
      const r = await axios.get<ImageItem[]>(`${IMG_API}/images?limit=48`);
      setItems(r.data);
    } catch (_e) { /* ignore */ }
  }
  useEffect(() => { load(); }, []);

  async function generate() {
    if (!prompt.trim()) return;
    setBusy(true); setErr('');
    try {
      await axios.post(`${IMG_API}/generate`, {
        prompt, negative_prompt: negPrompt, model, width, height,
        num_inference_steps: steps, guidance_scale: guidance, zone,
      }, { headers: { Authorization: `Bearer ${token}` } });
      await load();
    } catch (e: unknown) {
      const d = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setErr(`Fehler: ${d || String(e)}`);
    } finally { setBusy(false); }
  }

  const RESOLUTIONS: [number, number, string][] = [
    [512, 512, '512×512'], [768, 768, '768×768'],
    [1024, 576, '1024×576 (16:9)'], [576, 1024, '576×1024 (9:16)'],
    [1024, 1024, '1024×1024'],
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <div className="lg:col-span-1 bg-gray-900/60 border border-gray-800 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-violet-300">Bild-Generator</h2>

          <div>
            <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Prompt</label>
            <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)}
              placeholder="Beschreibe das Bild in Detail..."
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm h-28 focus:outline-none focus:border-violet-500 resize-none" />
          </div>

          <div>
            <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Negativer Prompt</label>
            <textarea value={negPrompt} onChange={(e) => setNegPrompt(e.target.value)}
              placeholder="Was soll NICHT im Bild sein..."
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm h-16 focus:outline-none focus:border-violet-500 resize-none" />
          </div>

          <div>
            <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Modell</label>
            <select value={model} onChange={(e) => setModel(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500">
              {IMAGE_MODELS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Auflösung</label>
            <div className="grid grid-cols-2 gap-1">
              {RESOLUTIONS.map(([w, h, label]) => (
                <button key={label} onClick={() => { setWidth(w); setHeight(h); }}
                  className={`py-1.5 text-xs rounded-lg transition ${
                    width === w && height === h
                      ? 'bg-violet-700 text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  }`}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Steps: {steps}</label>
              <input type="range" min="5" max="50" step="1" value={steps}
                onChange={(e) => setSteps(Number(e.target.value))}
                className="w-full accent-violet-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">CFG: {guidance.toFixed(1)}</label>
              <input type="range" min="1" max="20" step="0.5" value={guidance}
                onChange={(e) => setGuidance(Number(e.target.value))}
                className="w-full accent-violet-500" />
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Zone</label>
            <select value={zone} onChange={(e) => setZone(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500">
              <option value="PUBLIC">PUBLIC</option>
              <option value="WORKSPACE">WORKSPACE</option>
              <option value="FAMILY_PRIVATE">FAMILY_PRIVATE</option>
            </select>
          </div>

          {err && <p className="text-sm text-rose-400">{err}</p>}

          <button onClick={generate} disabled={busy || !prompt.trim()}
            className="w-full inline-flex items-center justify-center gap-2 py-2.5 bg-violet-600 hover:bg-violet-700 disabled:bg-gray-700 rounded-lg text-sm font-medium transition">
            {busy ? <ArrowPathIcon className="w-4 h-4 animate-spin" /> : <PhotoIcon className="w-4 h-4" />}
            {busy ? 'Generiere...' : 'Bild generieren'}
          </button>
        </div>

        {/* Gallery */}
        <div className="lg:col-span-2">
          {preview && (
            <div className="mb-4 bg-gray-900/60 border border-violet-700 rounded-xl p-3 relative">
              <button onClick={() => setPreview(null)}
                className="absolute top-2 right-2 p-1 bg-gray-800 hover:bg-gray-700 rounded-lg">
                <span className="text-xs">✕</span>
              </button>
              <img src={`${IMG_API}/file/${preview.id}`} alt={preview.prompt}
                className="w-full rounded-lg max-h-96 object-contain" />
              <p className="text-xs text-gray-400 mt-2">{preview.prompt}</p>
              <div className="flex gap-2 mt-2">
                <a href={`${IMG_API}/file/${preview.id}`} download
                  className="inline-flex items-center gap-1 px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs">
                  <ArrowDownTrayIcon className="w-3.5 h-3.5" /> Download
                </a>
              </div>
            </div>
          )}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {items.map((it) => (
              <div key={it.id} onClick={() => setPreview(it)}
                className="cursor-pointer group bg-gray-900/60 border border-gray-800 hover:border-violet-500 rounded-xl overflow-hidden transition">
                <img src={`${IMG_API}/file/${it.id}`} alt={it.prompt}
                  className="w-full aspect-square object-cover group-hover:scale-105 transition-transform duration-300" />
                <div className="p-2">
                  <p className="text-xs text-gray-300 line-clamp-2">{it.prompt}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">{it.model_used} · {it.width}×{it.height}</p>
                </div>
              </div>
            ))}
            {items.length === 0 && !busy && (
              <div className="col-span-full text-center py-12 text-gray-600">
                <PhotoIcon className="w-12 h-12 mx-auto mb-2 opacity-20" />
                <p className="text-sm">Noch keine Bilder. Starte die Generierung links.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Video Studio ──────────────────────────────────────────────────────────────

function VideoStudio({ token }: { token: string }) {
  const [prompt, setPrompt] = useState('');
  const [resolution, setResolution] = useState('512x512');
  const [duration, setDuration] = useState(4);
  const [fps, setFps] = useState(24);
  const [zone, setZone] = useState('WORKSPACE');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [items, setItems] = useState<VideoJob[]>([]);

  async function load() {
    try {
      const r = await axios.get<VideoJob[]>(`${VID_API}/jobs`);
      setItems(r.data);
    } catch (_e) { /* ignore */ }
  }

  useEffect(() => {
    load();
    const iv = setInterval(load, 5000);
    return () => clearInterval(iv);
  }, []);

  async function generate() {
    if (!prompt.trim()) return;
    setBusy(true); setErr('');
    try {
      await axios.post(`${VID_API}/generate`, {
        prompt, resolution, duration, fps, zone,
      }, { headers: { Authorization: `Bearer ${token}` } });
      await load();
    } catch (e: unknown) {
      const d = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setErr(`Fehler: ${d || String(e)}`);
    } finally { setBusy(false); }
  }

  const RESOLUTIONS = ['256x256', '512x512', '768x512', '1024x576', '1280x720'];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-1 bg-gray-900/60 border border-gray-800 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-blue-300">Video-Generator</h2>

        <div>
          <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Prompt</label>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)}
            placeholder="Beschreibe das Video..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm h-28 focus:outline-none focus:border-blue-500 resize-none" />
        </div>

        <div>
          <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Auflösung</label>
          <select value={resolution} onChange={(e) => setResolution(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
            {RESOLUTIONS.map((r) => <option key={r} value={r}>{r.replace('x', '×')}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Dauer: {duration}s</label>
            <input type="range" min="2" max="16" step="2" value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full accent-blue-500" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">FPS: {fps}</label>
            <input type="range" min="12" max="30" step="6" value={fps}
              onChange={(e) => setFps(Number(e.target.value))}
              className="w-full accent-blue-500" />
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Zone</label>
          <select value={zone} onChange={(e) => setZone(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
            <option value="PUBLIC">PUBLIC</option>
            <option value="WORKSPACE">WORKSPACE</option>
            <option value="FAMILY_PRIVATE">FAMILY_PRIVATE</option>
          </select>
        </div>

        {err && <p className="text-sm text-rose-400">{err}</p>}

        <button onClick={generate} disabled={busy || !prompt.trim()}
          className="w-full inline-flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-lg text-sm font-medium transition">
          {busy ? <ArrowPathIcon className="w-4 h-4 animate-spin" /> : <FilmIcon className="w-4 h-4" />}
          {busy ? 'Job erstellen...' : 'Video generieren'}
        </button>
      </div>

      <div className="lg:col-span-2 space-y-3">
        {items.map((it) => (
          <div key={it.id} className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 line-clamp-2">{it.prompt}</p>
                <p className="text-xs text-gray-500 mt-1">{it.resolution} · {it.duration_seconds}s · {new Date(it.created_at).toLocaleString('de-DE')}</p>
                {it.error && <p className="text-xs text-rose-400 mt-1">{it.error}</p>}
              </div>
              <StatusBadge status={it.status} />
            </div>
            {it.status === 'completed' && (
              /* eslint-disable-next-line jsx-a11y/media-has-caption */
              <video controls src={`${VID_API}/file/${it.id}`}
                className="w-full rounded-lg mt-2" />
            )}
          </div>
        ))}
        {items.length === 0 && (
          <div className="text-center py-16 text-gray-600">
            <FilmIcon className="w-12 h-12 mx-auto mb-2 opacity-20" />
            <p className="text-sm">Noch keine Video-Jobs.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── LipSync Studio ────────────────────────────────────────────────────────────

function LipSyncStudio({ token }: { token: string }) {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [jobs, setJobs] = useState<LipSyncJob[]>([]);
  const videoRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLInputElement>(null);

  async function submit() {
    if (!videoFile || !audioFile) return;
    setBusy(true); setErr('');
    try {
      const fd = new FormData();
      fd.append('video', videoFile);
      fd.append('audio', audioFile);
      const r = await axios.post(`${MEDIA_API}/lipsync`, fd, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const job: LipSyncJob = { id: r.data?.job_id || Date.now().toString(), status: 'processing', message: 'Job gestartet...' };
      setJobs((j) => [job, ...j]);
      // Poll status
      pollJob(job.id);
    } catch (e: unknown) {
      const d = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      // Graceful fallback: show placeholder message
      if ((e as { response?: { status?: number } }).response?.status === 404 || (e as { response?: { status?: number } }).response?.status === 422) {
        setErr('LipSync-Endpoint noch nicht implementiert im media-processing Service. Wird in einer späteren Phase aktiviert.');
      } else {
        setErr(`Fehler: ${d || String(e)}`);
      }
    } finally { setBusy(false); }
  }

  function pollJob(jobId: string) {
    const iv = setInterval(async () => {
      try {
        const r = await axios.get(`${MEDIA_API}/lipsync/${jobId}`);
        setJobs((prev) => prev.map((j) =>
          j.id === jobId ? { ...j, status: r.data.status, video_url: r.data.video_url } : j
        ));
        if (r.data.status === 'completed' || r.data.status === 'failed') clearInterval(iv);
      } catch (_e) { clearInterval(iv); }
    }, 3000);
  }

  return (
    <div className="space-y-6">
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-pink-300 flex items-center gap-2">
          <CameraIcon className="w-4 h-4" /> Lip Sync Studio
        </h2>
        <p className="text-xs text-gray-500">
          Lade ein Video und eine Audiodatei hoch — der media-processing Service synchronisiert die Lippenbewegungen.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border-2 border-dashed border-gray-700 hover:border-pink-600 rounded-xl p-6 text-center cursor-pointer transition"
            onClick={() => videoRef.current?.click()}>
            <input ref={videoRef} type="file" accept="video/*" className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) { setVideoFile(f); setVideoUrl(URL.createObjectURL(f)); }
              }} />
            <FilmIcon className="w-10 h-10 mx-auto mb-2 text-gray-600" />
            {videoFile ? (
              <p className="text-sm text-pink-300">{videoFile.name}</p>
            ) : (
              <>
                <p className="text-sm text-gray-400">Video hochladen</p>
                <p className="text-xs text-gray-600 mt-1">MP4, MOV, AVI</p>
              </>
            )}
          </div>

          <div className="border-2 border-dashed border-gray-700 hover:border-pink-600 rounded-xl p-6 text-center cursor-pointer transition"
            onClick={() => audioRef.current?.click()}>
            <input ref={audioRef} type="file" accept="audio/*" className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) { setAudioFile(f); setAudioUrl(URL.createObjectURL(f)); }
              }} />
            <MusicalNoteIcon className="w-10 h-10 mx-auto mb-2 text-gray-600" />
            {audioFile ? (
              <p className="text-sm text-pink-300">{audioFile.name}</p>
            ) : (
              <>
                <p className="text-sm text-gray-400">Audio hochladen</p>
                <p className="text-xs text-gray-600 mt-1">WAV, MP3, AAC</p>
              </>
            )}
          </div>
        </div>

        {videoUrl && (
          /* eslint-disable-next-line jsx-a11y/media-has-caption */
          <video src={videoUrl} controls className="w-full max-h-48 rounded-lg" />
        )}
        {audioUrl && (
          /* eslint-disable-next-line jsx-a11y/media-has-caption */
          <audio src={audioUrl} controls className="w-full" />
        )}

        {err && (
          <div className="flex items-start gap-2 bg-amber-950/50 border border-amber-700 rounded-lg p-3">
            <ExclamationTriangleIcon className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-300">{err}</p>
          </div>
        )}

        <button onClick={submit} disabled={busy || !videoFile || !audioFile}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-pink-600 hover:bg-pink-700 disabled:bg-gray-700 rounded-lg text-sm font-medium transition">
          {busy ? <ArrowPathIcon className="w-4 h-4 animate-spin" /> : <PlayIcon className="w-4 h-4" />}
          {busy ? 'Verarbeite...' : 'LipSync starten'}
        </button>
      </div>

      {jobs.map((job) => (
        <div key={job.id} className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-300">Job {job.id.slice(0, 8)}...</p>
            <StatusBadge status={job.status} />
          </div>
          {job.status === 'completed' && job.video_url && (
            /* eslint-disable-next-line jsx-a11y/media-has-caption */
            <video controls src={job.video_url} className="w-full rounded-lg" />
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Cinema Studio ─────────────────────────────────────────────────────────────

function CinemaStudio({ token }: { token: string }) {
  const [scenes, setScenes] = useState([
    { prompt: '', duration: 4, resolution: '1024x576' },
  ]);
  const [style, setStyle] = useState('cinematic');
  const [zone, setZone] = useState('WORKSPACE');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [results, setResults] = useState<string[]>([]);

  function addScene() {
    setScenes((s) => [...s, { prompt: '', duration: 4, resolution: '1024x576' }]);
  }

  function removeScene(idx: number) {
    setScenes((s) => s.filter((_, i) => i !== idx));
  }

  function updateScene(idx: number, field: string, value: string | number) {
    setScenes((s) => s.map((sc, i) => i === idx ? { ...sc, [field]: value } : sc));
  }

  function applyPreset(preset: string) {
    setScenes((s) => s.map((sc, i) =>
      i === 0 ? { ...sc, prompt: `${preset}, ${style} style` } : sc
    ));
  }

  async function generateSequence() {
    const valid = scenes.filter((s) => s.prompt.trim());
    if (valid.length === 0) return;
    setBusy(true); setErr(''); setResults([]);
    const ids: string[] = [];
    for (const scene of valid) {
      try {
        const r = await axios.post(`${VID_API}/generate`, {
          prompt: `${scene.prompt} — ${style} cinematic style`,
          resolution: scene.resolution,
          duration: scene.duration,
          zone,
        }, { headers: { Authorization: `Bearer ${token}` } });
        if (r.data?.id) ids.push(r.data.id);
      } catch (_e) { /* continue */ }
    }
    setResults(ids);
    setBusy(false);
  }

  return (
    <div className="space-y-6">
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-amber-300 flex items-center gap-2">
          <QueueListIcon className="w-4 h-4" /> Cinema — Sequenz-Generator
        </h2>
        <p className="text-xs text-gray-500">
          Erstelle eine Sequenz von Szenen. Jede Szene wird als Video generiert — ideal für cinematische Sequenzen.
        </p>

        {/* Style + Presets */}
        <div className="flex gap-3 items-center flex-wrap">
          <select value={style} onChange={(e) => setStyle(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-amber-500">
            {['cinematic', 'documentary', 'noir', 'fantasy', 'sci-fi', 'horror', 'romance'].map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <span className="text-xs text-gray-500">Szenen-Presets:</span>
          {CINEMA_PROMPTS.map((p) => (
            <button key={p.label} onClick={() => applyPreset(p.value)}
              className="px-2 py-1 bg-gray-800 hover:bg-amber-900/40 border border-gray-700 hover:border-amber-700 rounded text-xs transition">
              {p.label}
            </button>
          ))}
        </div>

        {/* Scene Editor */}
        <div className="space-y-3">
          {scenes.map((scene, idx) => (
            <div key={idx} className="bg-gray-800/60 border border-gray-700 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-amber-300 uppercase tracking-wider">Szene {idx + 1}</span>
                {scenes.length > 1 && (
                  <button onClick={() => removeScene(idx)}
                    className="p-1 hover:bg-rose-900 rounded transition text-rose-400">
                    ✕
                  </button>
                )}
              </div>
              <textarea
                value={scene.prompt}
                onChange={(e) => updateScene(idx, 'prompt', e.target.value)}
                placeholder={`Beschreibe Szene ${idx + 1}...`}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm h-20 focus:outline-none focus:border-amber-500 resize-none"
              />
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] text-gray-500 uppercase mb-1">Dauer: {scene.duration}s</label>
                  <input type="range" min="2" max="16" step="2" value={scene.duration}
                    onChange={(e) => updateScene(idx, 'duration', Number(e.target.value))}
                    className="w-full accent-amber-500" />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500 uppercase mb-1">Auflösung</label>
                  <select value={scene.resolution}
                    onChange={(e) => updateScene(idx, 'resolution', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs focus:outline-none">
                    {['512x512', '1024x576', '1280x720'].map((r) => (
                      <option key={r} value={r}>{r.replace('x', '×')}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-3 items-center flex-wrap">
          <button onClick={addScene}
            className="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs transition">
            + Szene hinzufügen
          </button>
          <select value={zone} onChange={(e) => setZone(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs focus:outline-none">
            <option value="PUBLIC">PUBLIC</option>
            <option value="WORKSPACE">WORKSPACE</option>
            <option value="FAMILY_PRIVATE">FAMILY_PRIVATE</option>
          </select>
        </div>

        {err && <p className="text-sm text-rose-400">{err}</p>}

        <button onClick={generateSequence} disabled={busy || scenes.every((s) => !s.prompt.trim())}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-amber-600 hover:bg-amber-700 disabled:bg-gray-700 rounded-lg text-sm font-medium transition">
          {busy ? <ArrowPathIcon className="w-4 h-4 animate-spin" /> : <QueueListIcon className="w-4 h-4" />}
          {busy ? `Generiere Szene...` : `${scenes.filter((s) => s.prompt.trim()).length} Szene(n) generieren`}
        </button>
      </div>

      {results.length > 0 && (
        <div className="bg-gray-900/60 border border-amber-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircleIcon className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-semibold text-amber-300">{results.length} Jobs gestartet</h3>
          </div>
          <p className="text-xs text-gray-500">
            Wechsle zum <strong className="text-amber-400">Video-Tab</strong> um den Fortschritt zu sehen. Jobs laufen auf deiner RTX 3090.
          </p>
          <div className="space-y-1">
            {results.map((id) => (
              <div key={id} className="flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2">
                <span className="text-xs text-gray-400 font-mono">{id.slice(0, 16)}...</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── helpers ──────────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    completed: 'bg-emerald-900 text-emerald-300',
    failed: 'bg-rose-900 text-rose-300',
    processing: 'bg-amber-900 text-amber-300',
    pending: 'bg-gray-800 text-gray-400',
  };
  return (
    <span className={`flex-shrink-0 px-2 py-1 text-xs rounded ${map[status] || 'bg-gray-800 text-gray-400'}`}>
      {status}
    </span>
  );
}
