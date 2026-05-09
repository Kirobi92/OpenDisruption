'use client';

// /knowledge-graph-3d — HIGH-END 3D Wissensgraph mit Vanilla Three.js
// Auth-gated (localStorage access_token), full-bleed Canvas

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import Link from 'next/link';

// Dynamischer Import mit ssr:false — Three.js läuft nur im Client
const VaultGraph3DHighEnd = dynamic(
  () => import('@/components/VaultGraph3DHighEnd'),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-screen w-full items-center justify-center bg-void-950">
        <div className="text-center">
          <div className="mx-auto h-20 w-20 animate-pulse rounded-full bg-gradient-to-br from-aurora-cyan/30 via-aurora-violet/30 to-aurora-magenta/30 blur-xl" />
          <p className="mt-6 font-mono text-xs uppercase tracking-[0.45em] text-white/40">
            RTX 3090 · Shader-Compilation…
          </p>
        </div>
      </div>
    ),
  },
);

export default function KnowledgeGraph3DPage() {
  const router = useRouter();

  // Auth-Guard: ohne Token zur Login-Seite umleiten
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (!token) router.replace('/');
    }
  }, [router]);

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-void-950">
      {/* Header-Overlay */}
      <div className="absolute top-0 left-0 right-0 z-30 flex items-center justify-between px-5 py-3 pointer-events-none">
        <div className="pointer-events-auto">
          <Link
            href="/knowledge-graph"
            className="flex items-center gap-2 rounded-xl bg-black/60 px-3 py-2 text-xs text-white/60 hover:text-white backdrop-blur-sm border border-white/10 transition-colors"
          >
            ← 2D-Graph
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <div className="font-mono text-[10px] uppercase tracking-[0.4em] text-aurora-cyan/60 hidden sm:block">
            KIDI · Vault Cortex · 3D HIGH-END
          </div>
          <div className="h-1.5 w-1.5 rounded-full bg-aurora-cyan animate-pulse" />
        </div>

        <div className="pointer-events-auto">
          <Link
            href="/control-center"
            className="flex items-center gap-2 rounded-xl bg-black/60 px-3 py-2 text-xs text-white/60 hover:text-white backdrop-blur-sm border border-white/10 transition-colors"
          >
            Hub →
          </Link>
        </div>
      </div>

      {/* Vollbild-3D-Canvas */}
      <div className="absolute inset-0">
        <VaultGraph3DHighEnd initialAutoRotate={true} initialColorMode="zone" />
      </div>
    </div>
  );
}
