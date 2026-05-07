'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  MagnifyingGlassIcon,
  DocumentTextIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';

type Zone = 'ALL' | 'PUBLIC' | 'WORKSPACE' | 'FAMILY_PRIVATE';

interface SearchResult {
  id: string;
  score: number;
  source: string;
  zone: string;
  snippet: string;
  title?: string;
  created_at?: string;
}

const ZONE_OPTIONS: { value: Zone; label: string }[] = [
  { value: 'ALL', label: '🔍 Alle Zonen' },
  { value: 'PUBLIC', label: '🌍 Public' },
  { value: 'WORKSPACE', label: '💼 Workspace' },
  { value: 'FAMILY_PRIVATE', label: '👨‍👩‍👦 Family Private' },
];

const ZONE_COLORS: Record<string, string> = {
  PUBLIC: 'bg-green-500/20 text-green-400 border-green-500/30',
  WORKSPACE: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  FAMILY_PRIVATE: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  QUARANTINE: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  SACRED: 'bg-red-500/20 text-red-400 border-red-500/30',
};

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80 ? 'text-green-400' : pct >= 50 ? 'text-yellow-400' : 'text-gray-400';
  return <span className={`text-xs font-mono ${color}`}>{pct}%</span>;
}

export default function SearchPage() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [zone, setZone] = useState<Zone>('ALL');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState('');

  const getAxios = () =>
    axios.create({
      baseURL: '/api',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token') ?? ''}`,
      },
    });

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/');
    }
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setSearched(true);

    try {
      const payload: { query: string; zone?: string } = { query: query.trim() };
      if (zone !== 'ALL') payload.zone = zone;

      const response = await getAxios().post<SearchResult[]>('/rag/search', payload);
      setResults(response.data);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? 'Suche fehlgeschlagen.');
      } else {
        setError('Unbekannter Fehler bei der Suche.');
      }
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center space-x-3">
          <button
            onClick={() => router.push('/chat')}
            className="text-gray-400 hover:text-white transition-colors text-sm"
          >
            ← Zurück
          </button>
          <h1 className="text-xl font-bold">Wissenssuche</h1>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {/* Search Form */}
        <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <form onSubmit={handleSearch} className="space-y-4">
            {/* Zone Filter */}
            <div className="flex items-center space-x-2">
              <FunnelIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <div className="flex flex-wrap gap-2">
                {ZONE_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setZone(opt.value)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                      zone === opt.value
                        ? opt.value === 'ALL'
                          ? 'bg-kirobi-600 text-white border-kirobi-500'
                          : ZONE_COLORS[opt.value] ?? 'bg-gray-600 text-white border-gray-500'
                        : 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Search Input */}
            <div className="flex space-x-2">
              <div className="relative flex-1">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Suche im Wissen der Familie..."
                  className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-kirobi-500"
                  autoFocus
                />
              </div>
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="px-6 py-3 bg-kirobi-600 hover:bg-kirobi-700 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
              >
                {loading ? (
                  <span className="flex items-center space-x-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Suche...</span>
                  </span>
                ) : (
                  'Suchen'
                )}
              </button>
            </div>
          </form>
        </section>

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Loading Skeleton */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-gray-800 rounded-xl p-5 border border-gray-700 animate-pulse">
                <div className="h-4 bg-gray-700 rounded w-3/4 mb-3" />
                <div className="h-3 bg-gray-700 rounded w-full mb-2" />
                <div className="h-3 bg-gray-700 rounded w-5/6" />
              </div>
            ))}
          </div>
        )}

        {/* Results */}
        {!loading && searched && results.length === 0 && !error && (
          <div className="text-center py-12 text-gray-500">
            <MagnifyingGlassIcon className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Keine Ergebnisse für „{query}"</p>
            <p className="text-sm mt-1">Versuche andere Suchbegriffe oder eine andere Zone.</p>
          </div>
        )}

        {!loading && results.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm text-gray-400">
              {results.length} Ergebnis{results.length !== 1 ? 'se' : ''} gefunden
            </p>
            {results.map((result) => (
              <article
                key={result.id}
                className="bg-gray-800 rounded-xl p-5 border border-gray-700 hover:border-kirobi-500/40 transition-colors"
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center space-x-2 min-w-0">
                    <DocumentTextIcon className="w-5 h-5 text-kirobi-400 flex-shrink-0" />
                    <h3 className="font-medium text-white truncate">
                      {result.title ?? result.source}
                    </h3>
                  </div>
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    <ScoreBadge score={result.score} />
                    <span
                      className={`text-xs px-2 py-0.5 rounded border ${
                        ZONE_COLORS[result.zone] ?? 'bg-gray-700 text-gray-300 border-gray-600'
                      }`}
                    >
                      {result.zone}
                    </span>
                  </div>
                </div>

                <p className="text-sm text-gray-300 leading-relaxed line-clamp-3">
                  {result.snippet}
                </p>

                <div className="flex items-center space-x-3 mt-3 text-xs text-gray-500">
                  <span className="truncate">{result.source}</span>
                  {result.created_at && (
                    <>
                      <span>·</span>
                      <span>{new Date(result.created_at).toLocaleDateString('de-DE')}</span>
                    </>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}

        {/* Empty State (before first search) */}
        {!searched && !loading && (
          <div className="text-center py-16 text-gray-600">
            <MagnifyingGlassIcon className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p className="text-lg">Durchsuche das Familienwissen</p>
            <p className="text-sm mt-1">Semantische Suche über alle Dokumente und Erfahrungen</p>
          </div>
        )}
      </main>
    </div>
  );
}
