'use client';

import { useEffect, useState } from 'react';

interface ServiceProbe {
  name: string;
  url: string;
  ok: boolean;
  detail?: string;
}

const PROBES: { name: string; url: string }[] = [
  { name: 'web',  url: '/health' },
  { name: 'auth', url: '/api/auth/health' },
  { name: 'api',  url: '/api/health' },
];

const PARTS: { name: string; path: string; description: string; guard: string }[] = [
  {
    name: 'Kirobi PWA',
    path: '/chat',
    description: 'Familie-Chat, Login und Alltagseinstieg.',
    guard: 'JWT-Login',
  },
  {
    name: 'Stack Status',
    path: '/status',
    description: 'Diese zentrale Übersicht und Live-Probes.',
    guard: 'Reverse Proxy',
  },
  {
    name: 'Open WebUI',
    path: '/open-webui/',
    description: 'Lokales LLM-Workbench für Ollama-Modelle.',
    guard: 'LAN/Tailscale + Open WebUI Login',
  },
  {
    name: 'Flowise',
    path: '/flowise/',
    description: 'Workflow-Orchestrierung und visuelle Agent-Flows.',
    guard: 'LAN/Tailscale + Flowise Login',
  },
  {
    name: 'Qdrant Dashboard',
    path: '/qdrant/dashboard',
    description: 'Vektor-DB Diagnoseoberfläche. Nur über LAN/Tailscale erreichbar.',
    guard: 'LAN/Tailscale only',
  },
  {
    name: 'API',
    path: '/api/health',
    description: 'Backend-API hinter dem Reverse Proxy.',
    guard: 'JWT für Fach-Endpunkte',
  },
  {
    name: 'Auth',
    path: '/api/auth/health',
    description: 'Login, Sessions und Zonen-Berechtigungen.',
    guard: 'JWT-Service',
  },
  {
    name: 'Voice',
    path: '/voice/health',
    description: 'Voice/STT/TTS-Service hinter Caddy.',
    guard: 'LAN/Tailscale only',
  },
];

async function probe(p: { name: string; url: string }): Promise<ServiceProbe> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 4000);
  try {
    const res = await fetch(p.url, { signal: ctrl.signal, cache: 'no-store' });
    return { name: p.name, url: p.url, ok: res.ok, detail: `HTTP ${res.status}` };
  } catch (err: unknown) {
    return {
      name: p.name,
      url: p.url,
      ok: false,
      detail: err instanceof Error ? err.message : 'unreachable',
    };
  } finally {
    clearTimeout(timer);
  }
}

export default function StatusPage() {
  const [results, setResults] = useState<ServiceProbe[]>([]);
  const [running, setRunning] = useState(false);

  const refresh = async () => {
    setRunning(true);
    const out = await Promise.all(PROBES.map(probe));
    setResults(out);
    setRunning(false);
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, []);

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-gray-100 px-4 py-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-1">Kirobi · Stack-Status</h1>
        <p className="text-gray-400 mb-6">
          Live-Probes und zentrale Einstiegslinks für OpenDisruption über LAN oder Tailscale.
        </p>

        <button
          onClick={refresh}
          disabled={running}
          className="mb-6 px-4 py-2 rounded-lg bg-kirobi-600 hover:bg-kirobi-700 disabled:opacity-50"
        >
          {running ? 'Prüfe…' : 'Erneut prüfen'}
        </button>

        <ul className="space-y-2">
          {results.map((r) => (
            <li
              key={r.name}
              className={`flex items-center justify-between rounded-lg border px-4 py-3 ${
                r.ok
                  ? 'border-emerald-500/40 bg-emerald-500/5'
                  : 'border-red-500/40 bg-red-500/5'
              }`}
            >
              <div>
                <div className="font-medium">
                  {r.ok ? '✓' : '✗'} {r.name}
                </div>
                <div className="text-xs text-gray-400">{r.url}</div>
              </div>
              <div className="text-sm text-gray-300">{r.detail}</div>
            </li>
          ))}
          {results.length === 0 && (
            <li className="text-gray-500 italic">noch keine Daten…</li>
          )}
        </ul>

        <h2 className="text-2xl font-semibold mt-10 mb-4">Alle Teile</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {PARTS.map((part) => (
            <a
              key={part.name}
              href={part.path}
              className="block rounded-xl border border-gray-700 bg-gray-800/60 p-4 hover:border-kirobi-500 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="font-semibold text-lg">{part.name}</div>
                  <div className="text-sm text-gray-400 mt-1">{part.description}</div>
                </div>
                <span className="shrink-0 rounded-full border border-gray-600 px-2 py-1 text-xs text-gray-300">
                  {part.guard}
                </span>
              </div>
              <div className="mt-3 text-xs text-kirobi-300">{part.path}</div>
            </a>
          ))}
        </div>

        <p className="mt-8 text-xs text-gray-500">
          Sicherster Remote-Zugriff: Tailscale aktivieren und diese Seite über die
          Tailscale-IP bzw. MagicDNS öffnen. Die Docker-Ports der Backends bleiben
          auf <code>127.0.0.1</code>; nur Caddy hört auf LAN/Tailscale.
        </p>
      </div>
    </main>
  );
}
