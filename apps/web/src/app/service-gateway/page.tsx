'use client';

import { useEffect, useMemo } from 'react';
import Link from 'next/link';
import { ArrowTopRightOnSquareIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { useClientSearchParams } from '@/lib/use-client-search-params';

const TARGETS: Record<string, { path: string; embeddable: boolean; label: string }> = {
  'open-webui': { path: '/open-webui/', embeddable: true, label: 'Open WebUI' },
  flowise: { path: '/flowise/', embeddable: true, label: 'Flowise' },
  qdrant: { path: '/qdrant/dashboard/', embeddable: false, label: 'Qdrant' },
};

export default function ServiceGatewayPage() {
  const searchParams = useClientSearchParams();
  const target = searchParams.get('target') ?? '';
  const embed = searchParams.get('embed') === '1';

  const config = TARGETS[target];
  const targetUrl = useMemo(() => {
    if (!config || typeof window === 'undefined') return '';
    return new URL(config.path, window.location.origin).toString();
  }, [config]);

  useEffect(() => {
    if (!config || !targetUrl) return;
    if (embed && !config.embeddable) return;
    window.location.replace(targetUrl);
  }, [config, targetUrl, embed]);

  if (!config) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950 px-6 text-white">
        <div className="max-w-md rounded-3xl border border-red-500/20 bg-red-500/10 p-6 text-center">
          <p className="text-lg font-semibold">Unbekanntes Service-Ziel</p>
          <p className="mt-2 text-sm text-red-100">Der angeforderte Workbench-Dienst ist nicht registriert.</p>
          <Link href="/workbench" className="mt-4 inline-flex rounded-xl bg-white/10 px-4 py-2 text-sm">
            Zurück zur Workbench
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 px-6 text-white">
      <div className="max-w-lg rounded-3xl border border-gray-800 bg-gray-900/90 p-6 shadow-2xl">
        <div className="flex items-center gap-3">
          <ExclamationTriangleIcon className="h-6 w-6 text-amber-400" />
          <div>
            <p className="text-lg font-semibold">{config.label} wird geöffnet</p>
            <p className="text-sm text-gray-400">{targetUrl}</p>
          </div>
        </div>
        <p className="mt-4 text-sm leading-6 text-gray-300">
          Falls dein Browser die automatische Weiterleitung oder Einbettung blockiert, öffne den Dienst direkt in einem neuen Tab.
        </p>
        {embed && !config.embeddable ? (
          <p className="mt-3 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
            Dieser Dienst setzt Sicherheitsheader gegen iFrame-Einbettung. Er wird deshalb nur direkt geöffnet.
          </p>
        ) : null}
        <div className="mt-5 flex flex-wrap gap-3">
          <a
            href={targetUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-xl bg-kirobi-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-kirobi-500"
          >
            <ArrowTopRightOnSquareIcon className="h-4 w-4" />
            Direkt öffnen
          </a>
          <Link
            href="/workbench"
            className="inline-flex items-center rounded-xl border border-gray-700 bg-gray-950 px-4 py-2.5 text-sm text-gray-200"
          >
            Zur Workbench
          </Link>
        </div>
      </div>
    </div>
  );
}
