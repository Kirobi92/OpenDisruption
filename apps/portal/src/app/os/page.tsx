'use client';

import { motion } from 'framer-motion';
import {
  ArrowRight,
  Bot,
  Brain,
  FileUp,
  Mic,
  Music4,
  Sparkles,
  Video,
  Wand2,
} from 'lucide-react';
import Link from 'next/link';
import useSWR from 'swr';

import { BottomNav } from '@/components/layout/BottomNav';
import { Header } from '@/components/layout/Header';
import { useRequireAuth } from '@/lib/auth';
import { resolveCompanionProfile } from '@/lib/companions';
import { fetcher, useConversations, useServiceHealth, useMusicServiceHealth, type HealthResponse } from '@/lib/api';

type HeartMuLaStatus = {
  available?: boolean;
  model_exists?: boolean;
  model_path?: string;
  message?: string;
};

function HealthPill({ health, fallbackLabel = 'Verbinde…' }: { health?: HealthResponse; fallbackLabel?: string }) {
  if (!health) {
    return <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/60">{fallbackLabel}</span>;
  }

  const rawStatus = String(health.status ?? '').toLowerCase();
  const online = health.healthy === true || rawStatus === 'healthy' || rawStatus === 'ready' || rawStatus === 'ok';
  const classes = online
    ? 'border-emerald-400/25 bg-emerald-400/10 text-emerald-200'
    : 'border-amber-400/25 bg-amber-400/10 text-amber-200';

  return (
    <span className={`rounded-full border px-3 py-1 text-xs ${classes}`}>
      {online ? 'Online' : rawStatus || 'Pruefen'}
    </span>
  );
}

export default function OpenDisruptionOsPage() {
  const { user, isLoading, isAuthenticated } = useRequireAuth();
  const companion = resolveCompanionProfile(user?.username);
  const { data: conversations = [] } = useConversations();
  const { data: hermesHealth } = useServiceHealth(companion.hermesService);
  const { data: voiceHealth } = useServiceHealth('voice');
  const { data: imageHealth } = useServiceHealth('image-generation');
  const { data: musicHealth } = useMusicServiceHealth();
  const { data: videoHealth } = useServiceHealth('video-generation');
  const { data: retrievalHealth } = useServiceHealth('retrieval');
  const { data: ingestHealth } = useServiceHealth('ingest');
  const { data: heartmula } = useSWR<HeartMuLaStatus>(
    '/api/proxy/music-generation/heartmula/status',
    fetcher,
    { refreshInterval: 10000 },
  );

  if (isLoading || !isAuthenticated) {
    return <div className="min-h-screen bg-void" />;
  }

  const liveSurfaces = [
    { title: companion.assistantName, description: 'Eigene Hermes-Runtime mit persoenlichem Profil.', href: companion.hermesPath, health: hermesHealth, icon: Bot },
    { title: 'Voicebox', description: 'Lokale STT/TTS fuer natuerliche Gespraeche.', href: '/voice', health: voiceHealth, icon: Mic },
    { title: 'Image Studio', description: 'Lokale Bildgenerierung ueber deine GPU.', href: '/media', health: imageHealth, icon: Wand2 },
    { title: 'Music + HeartMuLa', description: 'Musikgeneration, Lyrics und HeartMuLa-Status.', href: '/media', health: musicHealth, icon: Music4 },
    { title: 'Video Studio', description: 'Asynchrone Videogenerierung und Renderjobs.', href: '/media', health: videoHealth, icon: Video },
    { title: 'Knowledge Flow', description: 'Uploads, Ingest und Retrieval fuer Memory-Aufbau.', href: '/brain', health: retrievalHealth, icon: Brain },
  ];

  return (
    <div className="min-h-screen pb-24 md:pb-10">
      <Header title="Hermes OS" />
      <main className="mx-auto max-w-7xl px-4 pb-12 pt-20 md:px-6">
        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          className="aurora-bg overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-white/10 to-white/5 p-6 shadow-card md:p-8"
        >
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-aurora-cyan/20 bg-aurora-cyan/10 px-4 py-2 text-xs uppercase tracking-[0.28em] text-aurora-cyan">
                <Bot className="h-4 w-4" />
                Persönliches OpenDisruption Control Center
              </div>
              <h1 className="mt-5 text-4xl font-semibold text-white md:text-5xl">{companion.assistantName}</h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-white/72">{companion.summary}</p>
              <p className="mt-3 text-sm text-white/50">Fokusbereich: {companion.focus}</p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-3xl border border-white/10 bg-black/10 p-4">
                <div className="text-xs uppercase tracking-[0.22em] text-white/45">Hermes Status</div>
                <div className="mt-3">
                  <HealthPill health={hermesHealth} />
                </div>
              </div>
              <div className="rounded-3xl border border-white/10 bg-black/10 p-4">
                <div className="text-xs uppercase tracking-[0.22em] text-white/45">Memory Flow</div>
                <div className="mt-3 text-sm text-white/75">{conversations.length} Chat-Kontexte bereits verknuepft</div>
              </div>
            </div>
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet px-5 py-2.5 font-semibold text-void shadow-glow-cyan"
            >
              Chat starten
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/voice" className="rounded-full border border-white/10 bg-white/5 px-5 py-2.5 text-sm text-white/75 transition hover:text-white">
              Voicebox
            </Link>
            <Link href="/media" className="rounded-full border border-white/10 bg-white/5 px-5 py-2.5 text-sm text-white/75 transition hover:text-white">
              Studio
            </Link>
            <a href={companion.hermesPath} className="rounded-full border border-white/10 bg-white/5 px-5 py-2.5 text-sm text-white/75 transition hover:text-white">
              Hermes Runtime
            </a>
          </div>
        </motion.section>

        <section className="mt-8 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="glass rounded-[2rem] p-6 shadow-card"
          >
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-semibold text-white">Voice-first Workflow</h2>
                <p className="mt-2 text-sm leading-7 text-white/60">
                  Sprache, Chat, Uploads und generative Aktionen laufen ueber dieselbe lokale Benutzerreise.
                </p>
              </div>
              <HealthPill health={voiceHealth} />
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              <Link href="/voice" className="rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-white/75">
                <Mic className="mb-3 h-5 w-5 text-aurora-cyan" />
                Natuerliches Gespraech mit STT und TTS
              </Link>
              <Link href="/chat" className="rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-white/75">
                <Bot className="mb-3 h-5 w-5 text-aurora-magenta" />
                Derselbe persoenliche Agent auch im Chat
              </Link>
              <Link href="/brain" className="rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-white/75">
                <Brain className="mb-3 h-5 w-5 text-aurora-violet" />
                Wissensspeicher und semantische Suche
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-[2rem] p-6 shadow-card"
          >
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-400/20 bg-amber-400/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-amber-200">
              <Music4 className="h-4 w-4" />
              HeartMuLa
            </div>
            <h2 className="mt-4 text-2xl font-semibold text-white">Lyrics- und Musik-Engine</h2>
            <p className="mt-3 text-sm leading-7 text-white/60">
              HeartMuLa haengt jetzt sichtbar am Portal und kann fuer kreative Sessions direkt aus dem Studio genutzt werden.
            </p>
            <div className="mt-5 rounded-3xl border border-white/10 bg-black/10 p-4">
              <div className="text-sm text-white/80">
                {heartmula?.available ? 'HeartMuLa lokal bereit.' : heartmula?.message ?? 'HeartMuLa-Status wird geladen.'}
              </div>
              <div className="mt-2 text-xs text-white/45">
                Modellpfad: {heartmula?.model_path ?? 'wird ermittelt'}
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link href="/media" className="rounded-full border border-white/10 bg-white/5 px-5 py-2.5 text-sm text-white/75 transition hover:text-white">
                Musikstudio
              </Link>
              <a href="/music-generation/" className="rounded-full border border-white/10 bg-white/5 px-5 py-2.5 text-sm text-white/75 transition hover:text-white">
                Service UI
              </a>
            </div>
          </motion.div>
        </section>

        <section className="mt-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-white">Live Services fuer deinen Benutzerraum</h2>
            <span className="text-sm text-white/45">Hermes, Voicebox, Generative AI und Knowledge</span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {liveSurfaces.map(({ title, description, href, health, icon: Icon }, index) => (
              <motion.a
                key={title}
                href={href}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.04 * index }}
                className="glass rounded-[2rem] p-5 shadow-card transition hover:-translate-y-1 hover:border-aurora-cyan/25"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-aurora-cyan">
                    <Icon className="h-6 w-6" />
                  </div>
                  <HealthPill health={health} />
                </div>
                <div className="mt-4 text-lg font-semibold text-white">{title}</div>
                <p className="mt-2 text-sm leading-7 text-white/58">{description}</p>
              </motion.a>
            ))}
          </div>
        </section>

        <section className="mt-8 grid gap-4 lg:grid-cols-3">
          <div className="glass rounded-[2rem] p-6 shadow-card">
            <FileUp className="h-6 w-6 text-aurora-cyan" />
            <h3 className="mt-4 text-xl font-semibold text-white">Uploads & Ingest</h3>
            <p className="mt-3 text-sm leading-7 text-white/60">
              Dokumente, Bilder, Audio und weitere Quellen koennen direkt ins System fliessen.
            </p>
            <div className="mt-4">
              <HealthPill health={ingestHealth} />
            </div>
          </div>
          <div className="glass rounded-[2rem] p-6 shadow-card">
            <Sparkles className="h-6 w-6 text-aurora-magenta" />
            <h3 className="mt-4 text-xl font-semibold text-white">Generative Studio</h3>
            <p className="mt-3 text-sm leading-7 text-white/60">
              Bilder, Musik und Videos werden lokal ueber dieselbe Benutzeroberflaeche initiiert und verwaltet.
            </p>
            <Link href="/media" className="mt-5 inline-flex items-center gap-2 text-sm text-aurora-cyan">
              Studio oeffnen
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="glass rounded-[2rem] p-6 shadow-card">
            <Brain className="h-6 w-6 text-aurora-violet" />
            <h3 className="mt-4 text-xl font-semibold text-white">Memory & Retrieval</h3>
            <p className="mt-3 text-sm leading-7 text-white/60">
              Chat-Kontexte, Dokumente und persoenliches Wissen bleiben ueber Retrieval und Benutzerordner verbunden.
            </p>
            <Link href="/brain" className="mt-5 inline-flex items-center gap-2 text-sm text-aurora-cyan">
              Wissensgraph
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>
      <BottomNav />
    </div>
  );
}
