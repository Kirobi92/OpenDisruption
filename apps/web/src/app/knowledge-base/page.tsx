'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  CircleStackIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  ArrowUpRightIcon,
  CloudArrowUpIcon,
} from '@heroicons/react/24/outline';

interface UploadedFile {
  id: string;
  original_filename: string;
  zone: string;
  file_size: number;
  created_at: string;
  metadata?: {
    ingest_status?: string;
    preview?: string;
    char_count?: number;
  };
}

interface SearchResult {
  id: string;
  title?: string;
  zone: string;
  snippet: string;
  score: number;
}

interface SearchResponse {
  results: SearchResult[];
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function KnowledgeBasePage() {
  const router = useRouter();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  const api = axios.create({
    baseURL: '/api',
    headers: {
      Authorization: `Bearer ${typeof window !== 'undefined' ? localStorage.getItem('access_token') ?? '' : ''}`,
    },
  });

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/');
      return;
    }
    void api.get<UploadedFile[]>('/uploads').then((response) => setFiles(response.data ?? []));
  }, [router]);

  const zoneCounts = useMemo(() => {
    return files.reduce<Record<string, number>>((acc, file) => {
      acc[file.zone] = (acc[file.zone] ?? 0) + 1;
      return acc;
    }, {});
  }, [files]);

  const runSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const response = await api.post<SearchResponse>('/rag/search', { query: query.trim() });
      setResults(response.data.results ?? []);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-80px)] px-4 py-6 sm:px-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <section className="rounded-[2rem] border border-white/10 bg-gradient-to-br from-slate-900/90 via-gray-900 to-slate-950 p-6 shadow-2xl shadow-sky-950/30">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-sky-400/20 bg-sky-400/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-sky-200">
                <CircleStackIcon className="h-4 w-4" />
                Knowledge Base
              </span>
              <h1 className="mt-4 text-3xl font-bold tracking-tight text-white">Deine Wissensdatenbank auf einen Blick.</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-gray-400">
                Uploads, Suchzugriff und Graph-Einstieg laufen hier zusammen. Du siehst sofort, wie viel Wissen lokal im System steckt und springst direkt in den passenden Flow.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {['PUBLIC', 'WORKSPACE', 'FAMILY_PRIVATE'].map((zone) => (
                <div key={zone} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-500">{zone}</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{zoneCounts[zone] ?? 0}</p>
                </div>
              ))}
              <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Total</p>
                <p className="mt-2 text-2xl font-semibold text-white">{files.length}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5">
            <div className="flex items-center gap-3">
              <MagnifyingGlassIcon className="h-5 w-5 text-kirobi-300" />
              <h2 className="text-xl font-semibold text-white">Live-Suche</h2>
            </div>
            <div className="mt-4 flex gap-3">
              <input
                type="text"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') void runSearch();
                }}
                placeholder="Wissen durchsuchen ..."
                className="flex-1 rounded-2xl border border-white/10 bg-gray-900 px-4 py-3 text-white outline-none ring-0 placeholder:text-gray-500"
              />
              <button
                type="button"
                onClick={() => void runSearch()}
                className="rounded-2xl bg-kirobi-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-kirobi-500"
              >
                {searching ? 'Suche…' : 'Suchen'}
              </button>
            </div>
            <div className="mt-5 space-y-3">
              {results.map((result) => (
                <div key={result.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-white">{result.title ?? result.id}</p>
                    <span className="rounded-full border border-white/10 px-2 py-0.5 text-xs text-gray-400">{result.zone}</span>
                  </div>
                  <p className="mt-2 text-sm text-gray-400">{result.snippet}</p>
                </div>
              ))}
              {!searching && results.length === 0 && (
                <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-4 text-sm text-gray-500">
                  Noch keine Live-Suche gestartet. Nutze alternativ die volle Suchoberfläche.
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <section className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5">
              <div className="flex items-center gap-3">
                <CloudArrowUpIcon className="h-5 w-5 text-emerald-300" />
                <h2 className="text-xl font-semibold text-white">Letzte Wissenseinträge</h2>
              </div>
              <div className="mt-4 space-y-3">
                {files.slice(0, 6).map((file) => (
                  <div key={file.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-white">{file.original_filename}</p>
                      <span className="rounded-full border border-white/10 px-2 py-0.5 text-xs text-gray-400">{file.zone}</span>
                    </div>
                    <p className="mt-2 text-xs text-gray-500">{formatBytes(file.file_size)} · {new Date(file.created_at).toLocaleString('de-DE')}</p>
                    {file.metadata?.preview && <p className="mt-2 text-sm text-gray-400">{file.metadata.preview}</p>}
                  </div>
                ))}
              </div>
            </section>

            <section className="grid gap-3 sm:grid-cols-2">
              <Link href="/upload" className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5 transition hover:border-kirobi-500/30">
                <p className="text-sm font-semibold text-white">Mehr Wissen einspeisen</p>
                <p className="mt-2 text-sm text-gray-400">Upload, Schnellnotiz und lokale Ingest-Pfade öffnen.</p>
                <ArrowUpRightIcon className="mt-4 h-5 w-5 text-kirobi-300" />
              </Link>
              <Link href="/knowledge-graph" className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5 transition hover:border-kirobi-500/30">
                <p className="text-sm font-semibold text-white">Knowledge Graph</p>
                <p className="mt-2 text-sm text-gray-400">Visueller Einstieg in die aktuelle Wissenslandschaft.</p>
                <SparklesIcon className="mt-4 h-5 w-5 text-violet-300" />
              </Link>
            </section>
          </div>
        </section>
      </div>
    </div>
  );
}
