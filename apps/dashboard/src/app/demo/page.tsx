import fs from 'node:fs/promises';
import path from 'node:path';
import Link from 'next/link';

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
  frontendRoutes: Array<{ surface: string; label: string; path: string }>;
  highlights: Array<{ title: string; path: string; description: string }>;
  nextSteps: string[];
};

const DATA_ROOT = '/Datenspeicher/OpenDisruption_Datenstruktur';
const MANIFEST_PATH = path.join(DATA_ROOT, 'OpenDisruption-v0.1', 'manifest.json');

async function loadManifest(): Promise<DemoManifest | null> {
  try {
    const raw = await fs.readFile(MANIFEST_PATH, 'utf-8');
    return JSON.parse(raw) as DemoManifest;
  } catch {
    return null;
  }
}

export default async function DemoPage() {
  const manifest = await loadManifest();

  if (!manifest) {
    return (
      <div className="p-6">
        <div className="card border-amber-500/20 bg-amber-500/10 text-amber-100">
          <h1 className="text-2xl font-semibold">v0.1 Demo noch nicht vorbereitet</h1>
          <p className="mt-3 text-sm text-amber-50/80">
            Fuehre <code className="rounded bg-black/20 px-1.5 py-0.5">bash infra/scripts/bootstrap-v01-demo.sh</code> aus und lade dann diese Seite neu.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <section className="card border-cyan-500/20 bg-gradient-to-br from-cyan-500/10 via-gray-900 to-gray-950">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs uppercase tracking-[0.24em] text-cyan-300">Demo Control View</p>
              <h1 className="mt-3 text-3xl font-bold text-white">{manifest.name}</h1>
              <p className="mt-3 text-sm leading-6 text-gray-300">{manifest.tagline}</p>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Ordner</p>
                <p className="mt-2 text-2xl font-semibold text-white">{manifest.stats.totalFolders}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.2em] text-gray-500">ORDNERINFO</p>
                <p className="mt-2 text-2xl font-semibold text-white">{manifest.stats.ordnerInfoFiles}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Demo User</p>
                <p className="mt-2 text-2xl font-semibold text-white">{manifest.stats.demoUserFiles}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <div className="card">
            <h2 className="text-xl font-semibold text-white">Operator-Sicht auf die Demo</h2>
            <div className="mt-4 space-y-3">
              {manifest.highlights.map((item) => (
                <div key={item.path} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-white">{item.title}</p>
                      <p className="mt-2 text-sm text-gray-400">{item.description}</p>
                    </div>
                  </div>
                  <p className="mt-3 rounded-xl bg-black/20 px-3 py-2 font-mono text-xs text-gray-300">{item.path}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <section className="card">
              <h2 className="text-xl font-semibold text-white">Frontends</h2>
              <div className="mt-4 grid gap-3">
                {manifest.frontendRoutes.map((route) => (
                  <Link
                    key={`${route.surface}-${route.path}`}
                    href={route.path}
                    className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-4 transition hover:border-cyan-400/30"
                  >
                    <p className="text-sm font-semibold text-white">{route.label}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.2em] text-cyan-200">{route.surface}</p>
                    <p className="mt-3 text-sm text-gray-300">{route.path}</p>
                  </Link>
                ))}
              </div>
            </section>

            <section className="card">
              <h2 className="text-xl font-semibold text-white">Naechste Schritte</h2>
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
      </div>
    </div>
  );
}
