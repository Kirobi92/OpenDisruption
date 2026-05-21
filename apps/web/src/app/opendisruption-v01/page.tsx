import fs from 'node:fs/promises';
import path from 'node:path';
import Link from 'next/link';
import {
  BoltIcon,
  CircleStackIcon,
  CpuChipIcon,
  FolderIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

export const dynamic = 'force-dynamic';

type DemoManifest = {
  version: string;
  name: string;
  tagline: string;
  dataRoot: string;
  demoUser: string;
  stats: {
    totalFolders: number;
    ordnerInfoFiles: number;
    demoUserFiles: number;
  };
  pillars: Array<{ title: string; description: string }>;
  frontendRoutes: Array<{ surface: string; label: string; path: string }>;
  highlights: Array<{ title: string; path: string; description: string }>;
  seedFiles: string[];
  nextSteps: string[];
};

const DATA_ROOT = '/Datenspeicher/OpenDisruption_Datenstruktur';
const DEMO_ROOT = path.join(DATA_ROOT, 'OpenDisruption-v0.1');
const MANIFEST_PATH = path.join(DEMO_ROOT, 'manifest.json');

async function loadManifest(): Promise<DemoManifest | null> {
  try {
    const raw = await fs.readFile(MANIFEST_PATH, 'utf-8');
    return JSON.parse(raw) as DemoManifest;
  } catch {
    return null;
  }
}

async function loadSeedPreviews(paths: string[]) {
  const items = await Promise.all(
    paths.slice(0, 5).map(async (filePath) => {
      try {
        const content = await fs.readFile(filePath, 'utf-8');
        const preview = content
          .split('\n')
          .filter((line) => line.trim() && !line.startsWith('#'))
          .slice(0, 3)
          .join(' ')
          .trim();
        return { filePath, preview: preview || 'Demo-Inhalt vorhanden.' };
      } catch {
        return { filePath, preview: 'Datei vorhanden, Vorschau aktuell nicht lesbar.' };
      }
    })
  );

  return items;
}

export default async function OpenDisruptionV01Page() {
  const manifest = await loadManifest();

  if (!manifest) {
    return (
      <div className="px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-5xl rounded-[2rem] border border-amber-500/20 bg-amber-500/10 p-6 text-amber-100">
          <h1 className="text-2xl font-semibold">OpenDisruption v0.1 Demo nicht vorbereitet</h1>
          <p className="mt-3 text-sm text-amber-50/80">
            Fuehre zuerst <code className="rounded bg-black/20 px-1.5 py-0.5">bash infra/scripts/bootstrap-v01-demo.sh</code> aus.
          </p>
        </div>
      </div>
    );
  }

  const seedPreviews = await loadSeedPreviews(manifest.seedFiles);
  const statCards = [
    { label: 'Ordner gesamt', value: manifest.stats.totalFolders, icon: FolderIcon },
    { label: 'ORDNERINFO', value: manifest.stats.ordnerInfoFiles, icon: CircleStackIcon },
    { label: 'Demo-Dateien', value: manifest.stats.demoUserFiles, icon: SparklesIcon },
    { label: 'Frontends', value: manifest.frontendRoutes.length, icon: BoltIcon },
  ];

  return (
    <div className="min-h-[calc(100vh-80px)] px-4 py-6 sm:px-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <section className="rounded-[2rem] border border-white/10 bg-gradient-to-br from-slate-900/90 via-gray-900 to-slate-950 p-6 shadow-2xl shadow-cyan-950/30">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <span className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-cyan-200">
                <CpuChipIcon className="h-4 w-4" />
                {manifest.name}
              </span>
              <h1 className="mt-4 text-4xl font-bold tracking-tight text-white">
                Die erste echte sichtbare <span className="text-cyan-300">OpenDisruption v{manifest.version}</span> Demo.
              </h1>
              <p className="mt-4 text-sm leading-7 text-gray-300">{manifest.tagline}</p>
              <div className="mt-5 flex flex-wrap gap-3 text-xs text-gray-400">
                <span className="rounded-full border border-white/10 px-3 py-1">Datenwurzel: {manifest.dataRoot}</span>
                <span className="rounded-full border border-white/10 px-3 py-1">Demo User: {manifest.demoUser}</span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:w-[420px]">
              {statCards.map(({ label, value, icon: Icon }) => (
                <div key={label} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <Icon className="h-5 w-5 text-cyan-300" />
                  <p className="mt-3 text-xs uppercase tracking-[0.2em] text-gray-500">{label}</p>
                  <p className="mt-1 text-2xl font-semibold text-white">{value}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5">
            <h2 className="text-xl font-semibold text-white">Kernpfeiler der v0.1-Demo</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {manifest.pillars.map((pillar) => (
                <div key={pillar.title} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-sm font-semibold text-white">{pillar.title}</p>
                  <p className="mt-2 text-sm leading-6 text-gray-400">{pillar.description}</p>
                </div>
              ))}
            </div>

            <h3 className="mt-6 text-sm font-semibold uppercase tracking-[0.24em] text-gray-500">Demo-Frontends</h3>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {manifest.frontendRoutes.map((route) => (
                <Link
                  key={`${route.surface}-${route.path}`}
                  href={route.path}
                  className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-4 transition hover:border-cyan-400/30 hover:bg-cyan-500/15"
                >
                  <p className="text-sm font-semibold text-white">{route.label}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.2em] text-cyan-200">{route.surface}</p>
                  <p className="mt-3 text-sm text-gray-300">{route.path}</p>
                </Link>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <section className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5">
              <h2 className="text-xl font-semibold text-white">Demobereiche</h2>
              <div className="mt-4 space-y-3">
                {manifest.highlights.map((item) => (
                  <div key={item.path} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <p className="text-sm font-semibold text-white">{item.title}</p>
                    <p className="mt-2 text-sm text-gray-400">{item.description}</p>
                    <p className="mt-3 rounded-xl bg-black/20 px-3 py-2 font-mono text-xs text-gray-300">{item.path}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5">
              <h2 className="text-xl font-semibold text-white">Naechste Ausbaustufe</h2>
              <ul className="mt-4 space-y-3 text-sm text-gray-300">
                {manifest.nextSteps.map((step) => (
                  <li key={step} className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
                    {step}
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5">
          <h2 className="text-xl font-semibold text-white">Beispielinhalte aus der Demo</h2>
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {seedPreviews.map((item) => (
              <div key={item.filePath} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="font-mono text-xs text-cyan-200">{item.filePath}</p>
                <p className="mt-3 text-sm leading-6 text-gray-300">{item.preview}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
