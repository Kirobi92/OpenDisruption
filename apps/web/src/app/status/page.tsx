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
      <div className="max-w-xl mx-auto">
        <h1 className="text-3xl font-bold mb-1">Kirobi · Stack-Status</h1>
        <p className="text-gray-400 mb-6">
          Live-Probes der Service-Stack hinter dem Reverse-Proxy.
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

        <p className="mt-8 text-xs text-gray-500">
          Erreichbar unter <code>kirobi.local</code> oder der LAN-IP des Hosts.
        </p>
      </div>
    </main>
  );
}
