<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { Search, FileText, Filter } from 'lucide-svelte';

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

  const ZONE_OPTIONS = [
    { value: 'ALL' as Zone, label: '🔍 Alle Zonen' },
    { value: 'PUBLIC' as Zone, label: '🌍 Public' },
    { value: 'WORKSPACE' as Zone, label: '💼 Workspace' },
    { value: 'FAMILY_PRIVATE' as Zone, label: '👨‍👩‍👦 Family Private' },
  ];

  const ZONE_COLORS: Record<string, string> = {
    PUBLIC: 'bg-green-500/20 text-green-400 border-green-500/30',
    WORKSPACE: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    FAMILY_PRIVATE: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    QUARANTINE: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    SACRED: 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  let query = $state($page.url.searchParams.get('q') ?? '');
  let zone = $state<Zone>(($page.url.searchParams.get('zone') as Zone) ?? 'ALL');
  let results = $state<SearchResult[]>([]);
  let loading = $state(false);
  let searched = $state(false);
  let totalResults = $state(0);

  function token() {
    return typeof localStorage !== 'undefined' ? (localStorage.getItem('access_token') ?? '') : '';
  }

  async function runSearch() {
    if (!query.trim()) return;
    loading = true;
    searched = true;
    try {
      const params = new URLSearchParams({ q: query, limit: '20' });
      if (zone !== 'ALL') params.set('zone', zone);
      const res = await fetch(`/api/search?${params}`, {
        headers: { Authorization: `Bearer ${token()}` },
      });
      if (res.status === 401) { goto('/login'); return; }
      const data = await res.json();
      results = data.results ?? [];
      totalResults = data.total ?? results.length;
    } catch (e) {
      console.error(e);
      results = [];
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    if (!token()) { goto('/login'); return; }
    if (query) void runSearch();
  });
</script>

<div class="min-h-screen bg-gray-950 text-white px-4 py-8 max-w-4xl mx-auto">
  <div class="mb-8">
    <h1 class="text-3xl font-bold">Wissens-Suche</h1>
    <p class="text-gray-400 mt-1">Semantic Search über alle lokalen Daten</p>
  </div>

  <form onsubmit={(e) => { e.preventDefault(); void runSearch(); }} class="flex gap-3 mb-6">
    <div class="relative flex-1">
      <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
      <input
        bind:value={query}
        type="text"
        placeholder="Suche…"
        class="w-full pl-10 pr-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
      />
    </div>
    <select
      bind:value={zone}
      class="px-3 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white focus:outline-none"
    >
      {#each ZONE_OPTIONS as opt}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
    <button
      type="submit"
      disabled={loading}
      class="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-medium transition disabled:opacity-50"
    >
      {loading ? 'Sucht…' : 'Suchen'}
    </button>
  </form>

  {#if searched && !loading}
    <p class="text-sm text-gray-400 mb-4">{totalResults} Ergebnisse</p>
  {/if}

  <div class="space-y-3">
    {#each results as r}
      <div class="rounded-2xl border border-gray-800 bg-gray-900/80 p-4">
        <div class="flex items-start justify-between gap-3 mb-2">
          <div class="flex items-center gap-2">
            <FileText class="w-4 h-4 text-gray-400 shrink-0" />
            <p class="font-semibold text-sm">{r.title ?? r.source}</p>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <span class="text-xs font-mono {r.score >= 0.8 ? 'text-green-400' : r.score >= 0.5 ? 'text-yellow-400' : 'text-gray-400'}">{Math.round(r.score * 100)}%</span>
            <span class="text-xs border rounded-full px-2 py-0.5 {ZONE_COLORS[r.zone] ?? 'border-gray-700 text-gray-400'}">{r.zone}</span>
          </div>
        </div>
        <p class="text-sm text-gray-300 leading-relaxed">{r.snippet}</p>
        {#if r.created_at}
          <p class="text-xs text-gray-600 mt-2">{new Date(r.created_at).toLocaleDateString('de-DE')}</p>
        {/if}
      </div>
    {/each}
    {#if searched && !loading && results.length === 0}
      <div class="rounded-2xl border border-gray-800 bg-gray-900/80 p-8 text-center text-gray-400">
        Keine Ergebnisse gefunden.
      </div>
    {/if}
  </div>
</div>
