'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ArrowTopRightOnSquareIcon,
  CheckCircleIcon,
  CommandLineIcon,
  ExclamationTriangleIcon,
  RectangleGroupIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { RUNTIME_PROBES, RUNTIME_SURFACES } from '@/lib/runtime-surfaces';
import { useClientSearchParams } from '@/lib/use-client-search-params';

type ProbeStatus = 'online' | 'offline' | 'unknown';

interface ProbeResult {
  status: ProbeStatus;
  detail: string;
}

export default function WorkbenchPage() {
  const router = useRouter();
  const searchParams = useClientSearchParams();
  const [selectedSurfaceId, setSelectedSurfaceId] = useState('open-webui');
  const [probes, setProbes] = useState<Record<string, ProbeResult>>({});

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/');
      return;
    }
    const requested = searchParams.get('surface');
    if (requested && RUNTIME_SURFACES.some((surface) => surface.id === requested && surface.kind === 'workbench')) {
      setSelectedSurfaceId(requested);
    }
  }, [router, searchParams]);

  useEffect(() => {
    void Promise.all(
      RUNTIME_PROBES.map(async (probe) => {
        try {
          const response = await fetch(probe.path, { cache: 'no-store' });
          return [probe.id, { status: response.ok ? 'online' : 'offline', detail: `HTTP ${response.status}` }] as const;
        } catch (error: unknown) {
          return [probe.id, { status: 'offline', detail: error instanceof Error ? error.message : 'unreachable' }] as const;
        }
      })
    ).then((entries) => setProbes(Object.fromEntries(entries)));
  }, []);

  const workbenchSurfaces = useMemo(
    () => RUNTIME_SURFACES.filter((surface) => surface.kind === 'workbench'),
    []
  );

  const selectedSurface =
    workbenchSurfaces.find((surface) => surface.id === selectedSurfaceId) ?? workbenchSurfaces[0];
  const embeddedPath = `${selectedSurface.directPath}${selectedSurface.directPath.includes('?') ? '&' : '?'}embed=1`;
  const embeddingBlocked = selectedSurface.id === 'qdrant';

  const statusTone = (status: ProbeStatus) => {
    if (status === 'online') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100';
    if (status === 'offline') return 'border-red-500/30 bg-red-500/10 text-red-100';
    return 'border-amber-500/30 bg-amber-500/10 text-amber-100';
  };

  const statusIcon = (status: ProbeStatus) => {
    if (status === 'online') return <CheckCircleIcon className="h-4 w-4 text-emerald-400" />;
    if (status === 'offline') return <XCircleIcon className="h-4 w-4 text-red-400" />;
    return <ExclamationTriangleIcon className="h-4 w-4 text-amber-400" />;
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <main className="mx-auto flex max-w-7xl flex-col gap-6 px-4 pb-24 pt-6 md:px-6">
        <section className="rounded-3xl border border-gray-800 bg-gradient-to-br from-gray-900 via-gray-900 to-gray-950 p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <span className="inline-flex w-fit items-center gap-2 rounded-full border border-gray-700 bg-gray-900 px-3 py-1 text-xs font-medium text-gray-200">
                <RectangleGroupIcon className="h-4 w-4 text-kirobi-300" />
                Embedded Workbench
              </span>
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Service-UIs direkt im Control Plane.</h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-gray-400">
                  Statt Kontextwechseln springst du zwischen Open WebUI, Flowise und Qdrant
                  innerhalb der OpenDisruption-Shell. Wenn ein Service Framing blockiert,
                  bleibt der Direktlink als Fallback sichtbar.
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/control-center"
                className="inline-flex items-center gap-2 rounded-xl border border-gray-700 bg-gray-900 px-4 py-2.5 text-sm font-medium text-gray-100 transition hover:border-kirobi-500/40"
              >
                <CommandLineIcon className="h-4 w-4" />
                Zum Control Center
              </Link>
              <a
                href={selectedSurface.directPath}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-kirobi-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-kirobi-500"
              >
                <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                Direkt öffnen
              </a>
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[300px_1fr]">
          <aside className="space-y-4">
            <div className="rounded-3xl border border-gray-800 bg-gray-900/80 p-4">
              <h2 className="text-lg font-semibold">Workbench-Flächen</h2>
              <div className="mt-4 space-y-2">
                {workbenchSurfaces.map((surface) => (
                  <button
                    key={surface.id}
                    type="button"
                    onClick={() => setSelectedSurfaceId(surface.id)}
                    className={`w-full rounded-2xl border p-4 text-left transition ${
                      selectedSurface.id === surface.id
                        ? 'border-kirobi-500/40 bg-kirobi-500/10'
                        : 'border-gray-800 bg-gray-950/60 hover:border-gray-700'
                    }`}
                  >
                    <span className="inline-flex rounded-full border border-gray-700 bg-gray-900 px-2 py-0.5 text-[11px] uppercase tracking-wide text-gray-300">
                      {surface.badge}
                    </span>
                    <p className="mt-3 text-sm font-semibold text-white">{surface.label}</p>
                    <p className="mt-2 text-sm text-gray-400">{surface.summary}</p>
                    <p className="mt-3 text-xs text-gray-500">{surface.guard}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-gray-800 bg-gray-900/80 p-4">
              <h2 className="text-lg font-semibold">Runtime</h2>
              <div className="mt-4 space-y-2">
                {RUNTIME_PROBES.map((probe) => {
                  const result = probes[probe.id] ?? { status: 'unknown' as ProbeStatus, detail: 'wird geprüft' };
                  return (
                    <div key={probe.id} className={`rounded-2xl border px-3 py-2 text-sm ${statusTone(result.status)}`}>
                      <div className="flex items-center gap-2">
                        {statusIcon(result.status)}
                        <span className="font-medium capitalize">{probe.id}</span>
                      </div>
                      <p className="mt-1 text-xs opacity-80">{result.detail}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </aside>

          <section className="space-y-4">
            <div className="rounded-3xl border border-gray-800 bg-gray-900/80 p-5">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-gray-500">{selectedSurface.badge}</p>
                  <h2 className="mt-2 text-2xl font-semibold">{selectedSurface.label}</h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-gray-400">{selectedSurface.summary}</p>
                </div>
                <div className="rounded-2xl border border-gray-800 bg-gray-950/60 px-4 py-3 text-sm text-gray-400">
                  <p className="font-medium text-white">Guard</p>
                  <p className="mt-1">{selectedSurface.guard}</p>
                </div>
              </div>
            </div>

            <div className="overflow-hidden rounded-3xl border border-gray-800 bg-gray-900/80">
              <div className="flex items-center justify-between border-b border-gray-800 px-4 py-3">
                <div>
                  <p className="text-sm font-semibold text-white">Embedded view</p>
                  <p className="text-xs text-gray-500">{embeddedPath}</p>
                </div>
                <a
                  href={selectedSurface.directPath}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-200 transition hover:border-kirobi-500/40"
                >
                  <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                  Neuer Tab
                </a>
              </div>
              <div className="h-[68vh] min-h-[540px] bg-black">
                {embeddingBlocked ? (
                  <div className="flex h-full items-center justify-center p-8">
                    <div className="max-w-md rounded-3xl border border-amber-500/30 bg-amber-500/10 p-6 text-center text-amber-100">
                      <p className="text-lg font-semibold">Direktstart erforderlich</p>
                      <p className="mt-3 text-sm leading-6">
                        Qdrant blockiert Einbettung per Sicherheitsheader. Öffne die Oberfläche direkt im neuen Tab über den Button oben.
                      </p>
                    </div>
                  </div>
                ) : (
                  <iframe
                    key={selectedSurface.id}
                    src={embeddedPath}
                    title={selectedSurface.label}
                    className="h-full w-full"
                  />
                )}
              </div>
            </div>
          </section>
        </section>
      </main>
    </div>
  );
}
