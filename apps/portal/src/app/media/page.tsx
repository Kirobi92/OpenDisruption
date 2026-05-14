'use client';

import { motion } from 'framer-motion';
import { ImagePlus, Music4, Sparkles, Upload, Video, X } from 'lucide-react';
import { useMemo, useRef, useState } from 'react';

import { BottomNav } from '@/components/layout/BottomNav';
import { Header } from '@/components/layout/Header';
import { useRequireAuth } from '@/lib/auth';
import { apiClient, uploadFile } from '@/lib/api';

type MediaTab = 'images' | 'music' | 'videos' | 'documents';

type ImageItem = { id: string; title: string; prompt: string; url: string; createdAt: string };
type MusicItem = { id: string; title: string; prompt: string; url?: string; createdAt: string };
type VideoItem = { id: string; title: string; prompt: string; url?: string; jobId?: string; status?: string; createdAt: string };
type DocumentItem = { id: string; title: string; type: string; createdAt: string };

function artDataUri(label: string, from: string, to: string) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop stop-color="${from}"/><stop offset="1" stop-color="${to}"/></linearGradient></defs><rect width="800" height="600" fill="url(#g)" rx="40"/><circle cx="600" cy="170" r="120" fill="rgba(255,255,255,0.18)"/><text x="56" y="330" font-size="52" fill="white" font-family="Inter, sans-serif">${label}</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

export default function MediaPage() {
  const { isLoading, isAuthenticated } = useRequireAuth();
  const [activeTab, setActiveTab] = useState<MediaTab>('images');
  const [panelOpen, setPanelOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [imagePrompt, setImagePrompt] = useState('');
  const [imageStyle, setImageStyle] = useState('Künstlerisch');
  const [musicPrompt, setMusicPrompt] = useState('');
  const [musicGenre, setMusicGenre] = useState('Ambient');
  const [musicDuration, setMusicDuration] = useState(45);
  const [videoPrompt, setVideoPrompt] = useState('');
  const [videoStyle, setVideoStyle] = useState('Cinematic');
  const [videoDuration, setVideoDuration] = useState(30);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [images, setImages] = useState<ImageItem[]>([
    { id: 'img-1', title: 'Aurora Thoughtspace', prompt: 'Lichtmeer in cyan und violett', url: artDataUri('Aurora Thoughtspace', '#22d3ee', '#a78bfa'), createdAt: '2026-05-10' },
    { id: 'img-2', title: 'Future Ritual', prompt: 'Futuristischer Raum mit goldenen Akzenten', url: artDataUri('Future Ritual', '#e879f9', '#fbbf24'), createdAt: '2026-05-09' },
  ]);
  const [musicItems, setMusicItems] = useState<MusicItem[]>([
    { id: 'music-1', title: 'Deep Focus Pulse', prompt: 'Ambient Flow', createdAt: '2026-05-10' },
    { id: 'music-2', title: 'Golden Family Loop', prompt: 'Warm synth texture', createdAt: '2026-05-09' },
  ]);
  const [videos, setVideos] = useState<VideoItem[]>([
    { id: 'video-1', title: 'Vision Reel', prompt: 'Slow cinematic orbit through a neon archive', createdAt: '2026-05-10' },
  ]);
  const [documents, setDocuments] = useState<DocumentItem[]>([
    { id: 'doc-1', title: 'Research Summary.pdf', type: 'PDF', createdAt: '2026-05-08' },
    { id: 'doc-2', title: 'Creative Notes.md', type: 'Markdown', createdAt: '2026-05-07' },
  ]);

  const tabMeta = useMemo(
    () => ({
      images: { label: 'Bilder', icon: ImagePlus },
      music: { label: 'Musik', icon: Music4 },
      videos: { label: 'Videos', icon: Video },
      documents: { label: 'Dokumente', icon: Upload },
    }),
    [],
  );

  const handleGenerate = async () => {
    setIsGenerating(true);

    try {
      if (activeTab === 'images') {
        const response = await apiClient.post('/api/proxy/image-generation/generate', {
          prompt: imagePrompt,
          style: imageStyle,
        });
        const payload = response.data ?? {};
        const imageId = String(payload.id ?? '');
        setImages((current) => [
          {
            id: imageId || `img-${Date.now()}`,
            title: String((payload.title ?? imagePrompt.slice(0, 40)) || 'Neues Bild'),
            prompt: imagePrompt,
            url: imageId
              ? `/api/proxy/image-generation/file/${imageId}`
              : artDataUri('Generated Image', '#5eead4', '#0d1230'),
            createdAt: new Date().toISOString().slice(0, 10),
          },
          ...current,
        ]);
      }

      if (activeTab === 'music') {
        const response = await apiClient.post('/api/proxy/music-generation/generate', {
          prompt: musicPrompt,
          genre: musicGenre,
          duration: musicDuration,
        });
        const payload = response.data ?? {};
        const trackId = String(payload.id ?? '');
        setMusicItems((current) => [
          {
            id: trackId || `music-${Date.now()}`,
            title: String(payload.title ?? `${musicGenre} Session`),
            prompt: musicPrompt,
            url: trackId ? `/api/proxy/music-generation/file/${trackId}` : undefined,
            createdAt: new Date().toISOString().slice(0, 10),
          },
          ...current,
        ]);
      }

      if (activeTab === 'videos') {
        const response = await apiClient.post('/api/proxy/video-generation/generate', {
          prompt: videoPrompt,
          duration: videoDuration,
          style: videoStyle,
        });
        const payload = response.data ?? {};
        const jobId = String(payload.job_id ?? '');
        setVideos((current) => [
          {
            id: jobId || `video-${Date.now()}`,
            title: String(payload.title ?? `${videoStyle} Clip`),
            prompt: videoPrompt,
            url: undefined, // wird nach Polling gesetzt
            jobId,
            status: payload.status ?? 'processing',
            createdAt: new Date().toISOString().slice(0, 10),
          },
          ...current,
        ]);
        // Polling für Job-Status starten
        if (jobId) {
          void pollVideoJob(jobId);
        }
      }

      setPanelOpen(false);
    } finally {
      setIsGenerating(false);
    }
  };

  const pollVideoJob = async (jobId: string) => {
    for (let i = 0; i < 30; i++) {
      await new Promise((r) => setTimeout(r, 5000));
      try {
        const resp = await apiClient.get(`/api/proxy/video-generation/jobs/${jobId}`);
        const job = resp.data ?? {};
        if (job.status === 'completed') {
          setVideos((current) =>
            current.map((v) =>
              v.id === jobId
                ? { ...v, url: `/api/proxy/video-generation/file/${jobId}`, status: 'completed' }
                : v,
            ),
          );
          return;
        }
        if (job.status === 'failed') {
          setVideos((current) =>
            current.map((v) => (v.id === jobId ? { ...v, status: 'failed' } : v)),
          );
          return;
        }
      } catch {
        // weiter versuchen
      }
    }
  };

  const handleUpload = async (file: File) => {
    if (activeTab === 'documents') {
      const uploaded = await uploadFile(file, 'WORKSPACE');
      setDocuments((current) => [
        {
          id: String(uploaded.id ?? uploaded.fileId ?? file.name),
          title: file.name,
          type: file.type || 'Dokument',
          createdAt: new Date().toISOString().slice(0, 10),
        },
        ...current,
      ]);
      return;
    }

    if (activeTab === 'images') {
      setImages((current) => [
        {
          id: `img-${Date.now()}`,
          title: file.name,
          prompt: 'Upload',
          url: URL.createObjectURL(file),
          createdAt: new Date().toISOString().slice(0, 10),
        },
        ...current,
      ]);
    }

    if (activeTab === 'music') {
      setMusicItems((current) => [
        {
          id: `music-${Date.now()}`,
          title: file.name,
          prompt: 'Upload',
          url: URL.createObjectURL(file),
          createdAt: new Date().toISOString().slice(0, 10),
        },
        ...current,
      ]);
    }

    if (activeTab === 'videos') {
      setVideos((current) => [
        {
          id: `video-${Date.now()}`,
          title: file.name,
          prompt: 'Upload',
          url: URL.createObjectURL(file),
          createdAt: new Date().toISOString().slice(0, 10),
        },
        ...current,
      ]);
    }
  };

  if (isLoading || !isAuthenticated) {
    return <div className="min-h-screen bg-void" />;
  }

  return (
    <div className="min-h-screen pb-24 md:pb-8">
      <Header title="Medien" />
      <main className="mx-auto max-w-7xl px-4 pb-10 pt-20 md:px-6">
        <div className="flex flex-wrap gap-3">
          {(['images', 'music', 'videos', 'documents'] as MediaTab[]).map((tab) => {
            const Icon = tabMeta[tab].icon;
            return (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={`inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm transition ${
                  activeTab === tab
                    ? 'bg-gradient-to-r from-kirobi-400 to-aurora-violet font-semibold text-void shadow-glow-cyan'
                    : 'border border-white/10 bg-white/5 text-white/65 hover:text-white'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tabMeta[tab].label}
              </button>
            );
          })}
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold">Deine Medienbibliothek</h1>
            <p className="mt-2 text-white/60">Erstellen, sammeln und kuratieren in einem aurora-glühenden Raum.</p>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="rounded-full border border-white/10 bg-white/5 px-5 py-2.5 text-sm text-white/75"
            >
              Upload
            </button>
            {activeTab !== 'documents' ? (
              <button
                type="button"
                onClick={() => setPanelOpen(true)}
                className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet px-5 py-2.5 font-semibold text-void shadow-glow-cyan"
              >
                <Sparkles className="h-4 w-4" />
                Generieren
              </button>
            ) : null}
          </div>
        </div>

        {activeTab === 'images' ? (
          <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {images.map((image) => (
              <motion.div key={image.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass overflow-hidden rounded-[2rem] shadow-card">
                <img src={image.url} alt={image.title} className="h-52 w-full object-cover" />
                <div className="p-5">
                  <div className="text-lg font-semibold">{image.title}</div>
                  <p className="mt-2 text-sm text-white/60">{image.prompt}</p>
                </div>
              </motion.div>
            ))}
          </section>
        ) : null}

        {activeTab === 'music' ? (
          <section className="mt-6 grid gap-4 xl:grid-cols-2">
            {musicItems.map((track) => (
              <div key={track.id} className="glass rounded-[2rem] p-5 shadow-card">
                <div className="text-lg font-semibold">{track.title}</div>
                <p className="mt-2 text-sm text-white/60">{track.prompt}</p>
                <div className="mt-4">
                  <audio controls className="w-full">
                    {track.url ? <source src={track.url} /> : null}
                  </audio>
                </div>
              </div>
            ))}
          </section>
        ) : null}

        {activeTab === 'videos' ? (
          <section className="mt-6 grid gap-4 xl:grid-cols-2">
            {videos.map((video) => (
              <div key={video.id} className="glass overflow-hidden rounded-[2rem] shadow-card">
                {video.url ? (
                  <video controls className="h-64 w-full bg-black">
                    <source src={video.url} type="video/mp4" />
                  </video>
                ) : (
                  <div className="flex h-64 flex-col items-center justify-center gap-3 bg-gradient-to-br from-aurora-violet/30 to-void-rise text-white/60">
                    {video.status === 'failed' ? (
                      <span className="text-red-400">Generierung fehlgeschlagen</span>
                    ) : (
                      <>
                        <div className="h-6 w-6 animate-spin rounded-full border-2 border-white/20 border-t-white/80" />
                        <span className="text-sm">Video wird generiert…</span>
                      </>
                    )}
                  </div>
                )}
                <div className="p-5">
                  <div className="text-lg font-semibold">{video.title}</div>
                  <p className="mt-2 text-sm text-white/60">{video.prompt}</p>
                </div>
              </div>
            ))}
          </section>
        ) : null}

        {activeTab === 'documents' ? (
          <section className="mt-6 glass rounded-[2rem] p-6 shadow-card">
            <div
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                const file = event.dataTransfer.files?.[0];
                if (file) {
                  void handleUpload(file);
                }
              }}
              className="rounded-[2rem] border-2 border-dashed border-white/10 bg-white/5 p-10 text-center text-white/60"
            >
              Ziehe Dokumente hier hinein oder nutze den Upload-Button.
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {documents.map((document) => (
                <div key={document.id} className="rounded-3xl border border-white/10 bg-black/10 p-5">
                  <div className="text-lg font-semibold">{document.title}</div>
                  <div className="mt-2 text-sm text-white/55">{document.type}</div>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept={activeTab === 'documents' ? '.pdf,.md,.txt,.json' : undefined}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) {
              void handleUpload(file);
            }
            event.target.value = '';
          }}
        />
      </main>

      {panelOpen ? (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/55">
          <div className="h-full w-full max-w-xl border-l border-white/10 bg-void-deep p-6 shadow-card">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold">Generieren</h2>
              <button type="button" onClick={() => setPanelOpen(false)} className="rounded-full border border-white/10 p-2">
                <X className="h-4 w-4" />
              </button>
            </div>

            {activeTab === 'images' ? (
              <div className="mt-6 space-y-4">
                <textarea
                  value={imagePrompt}
                  onChange={(event) => setImagePrompt(event.target.value)}
                  placeholder="Was soll das Bild zeigen?"
                  className="min-h-[150px] w-full rounded-3xl border border-white/10 bg-white/5 px-4 py-3 outline-none"
                />
                <select value={imageStyle} onChange={(event) => setImageStyle(event.target.value)} className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 px-4 outline-none">
                  {['Realistisch', 'Künstlerisch', 'Abstrakt', 'Fotorealistisch'].map((style) => (
                    <option key={style} value={style} className="bg-void-deep">
                      {style}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}

            {activeTab === 'music' ? (
              <div className="mt-6 space-y-4">
                <textarea
                  value={musicPrompt}
                  onChange={(event) => setMusicPrompt(event.target.value)}
                  placeholder="Beschreibe Stimmung, Instrumente oder Szene"
                  className="min-h-[150px] w-full rounded-3xl border border-white/10 bg-white/5 px-4 py-3 outline-none"
                />
                <select value={musicGenre} onChange={(event) => setMusicGenre(event.target.value)} className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 px-4 outline-none">
                  {['Pop', 'Electronic', 'Klassik', 'Ambient', 'Jazz'].map((genre) => (
                    <option key={genre} value={genre} className="bg-void-deep">
                      {genre}
                    </option>
                  ))}
                </select>
                <div>
                  <div className="mb-2 text-sm text-white/60">Dauer: {musicDuration}s</div>
                  <input type="range" min={10} max={120} value={musicDuration} onChange={(event) => setMusicDuration(Number(event.target.value))} className="w-full" />
                </div>
              </div>
            ) : null}

            {activeTab === 'videos' ? (
              <div className="mt-6 space-y-4">
                <textarea
                  value={videoPrompt}
                  onChange={(event) => setVideoPrompt(event.target.value)}
                  placeholder="Erzähle die Szene für dein Video"
                  className="min-h-[150px] w-full rounded-3xl border border-white/10 bg-white/5 px-4 py-3 outline-none"
                />
                <select value={videoStyle} onChange={(event) => setVideoStyle(event.target.value)} className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 px-4 outline-none">
                  {['Cinematic', 'Dreamy', 'Documentary', 'Stylized'].map((style) => (
                    <option key={style} value={style} className="bg-void-deep">
                      {style}
                    </option>
                  ))}
                </select>
                <div>
                  <div className="mb-2 text-sm text-white/60">Dauer: {videoDuration}s</div>
                  <input type="range" min={10} max={120} value={videoDuration} onChange={(event) => setVideoDuration(Number(event.target.value))} className="w-full" />
                </div>
              </div>
            ) : null}

            <button
              type="button"
              onClick={() => void handleGenerate()}
              className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-kirobi-400 to-aurora-violet px-5 py-3 font-semibold text-void shadow-glow-cyan"
            >
              {isGenerating ? 'Wird generiert...' : 'Jetzt generieren'}
            </button>
          </div>
        </div>
      ) : null}

      <BottomNav />
    </div>
  );
}
