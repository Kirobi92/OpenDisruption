'use client';

import dynamic from 'next/dynamic';
import { motion, useReducedMotion } from 'framer-motion';

// Force client-side render for the WebGL canvas.
const VaultGraph3D = dynamic(() => import('@/components/VaultGraph3D'), {
  ssr: false,
  loading: () => (
    <div className="flex h-[78vh] w-full items-center justify-center rounded-3xl border border-white/10 bg-void-950/60 backdrop-blur-xl">
      <div className="text-center">
        <div className="mx-auto h-14 w-14 animate-pulse rounded-full bg-gradient-to-br from-aurora-cyan/40 via-aurora-violet/40 to-aurora-magenta/40 blur-md" />
        <p className="mt-4 font-mono text-xs uppercase tracking-[0.4em] text-white/50">
          Materializing vault graph…
        </p>
      </div>
    </div>
  ),
});

export default function KnowledgeGraphPage() {
  const reduce = useReducedMotion();
  const fade = reduce ? {} : { initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 } };

  return (
    <main className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <motion.header
        {...fade}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] as const }}
        className="mb-6"
      >
        <div className="font-mono text-[11px] uppercase tracking-[0.45em] text-aurora-cyan/70">
          KIDI · Vault Cortex
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="bg-gradient-to-br from-white via-aurora-cyan to-aurora-violet bg-clip-text text-3xl font-semibold text-transparent sm:text-4xl">
            3D Wissensgraph
          </h1>
          {/* 3D HIGH-END Upgrade-Button */}
          <a
            href="/knowledge-graph-3d"
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-aurora-violet/20 to-aurora-cyan/20 border border-aurora-violet/40 px-4 py-2 text-sm font-semibold text-aurora-violet hover:from-aurora-violet/30 hover:to-aurora-cyan/30 hover:border-aurora-violet/60 transition-all shadow-glow-violet"
          >
            <span>⚡</span>
            <span>3D HIGH-END</span>
            <span className="font-mono text-[10px] text-aurora-cyan/80">RTX</span>
          </a>
        </div>
        <p className="mt-2 max-w-2xl text-sm text-white/60">
          Lebende Karte deines Obsidian-Vaults. Knoten sind Notes, Kanten sind{' '}
          <code className="rounded bg-void-800/60 px-1.5 py-0.5 text-aurora-cyan">[[wikilinks]]</code>.
          Größe ∝ eingehende Links · Farbe ∝ Sicherheits-Zone. GPU-beschleunigt via WebGL —
          deine RTX 3090 macht den Rest.
        </p>
      </motion.header>

      <motion.div
        {...fade}
        transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] as const }}
      >
        <VaultGraph3D />
      </motion.div>

      <motion.section
        {...fade}
        transition={{ duration: 0.5, delay: 0.2, ease: [0.16, 1, 0.3, 1] as const }}
        className="mt-6 grid gap-4 sm:grid-cols-3"
      >
        <div className="rounded-2xl border border-white/10 bg-void-900/50 p-4 backdrop-blur-md">
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-aurora-cyan">
            Interaktion
          </div>
          <p className="mt-2 text-sm text-white/70">
            Drag zum Rotieren · Scroll zum Zoom · Hover für Details · Knoten ziehen für
            Reorganisation.
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-void-900/50 p-4 backdrop-blur-md">
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-aurora-violet">
            Zonen-Schutz
          </div>
          <p className="mt-2 text-sm text-white/70">
            SACRED-Notes werden nicht indiziert · FAMILY_PRIVATE ist sichtbar nur für
            authentifizierte Familienmitglieder.
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-void-900/50 p-4 backdrop-blur-md">
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-aurora-magenta">
            Live-Update
          </div>
          <p className="mt-2 text-sm text-white/70">
            Graph wird via{' '}
            <code className="rounded bg-void-800/60 px-1 text-aurora-cyan">
              python infra/scripts/build-repo-graph.py
            </code>{' '}
            generiert (Build-Hook oder cron).
          </p>
        </div>
      </motion.section>
    </main>
  );
}
