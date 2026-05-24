<script lang="ts">
  import { Database, Search, Upload, ArrowUpRight, RefreshCw } from 'lucide-svelte';
  import { base } from '$app/paths';

  let { data }: { data: any } = $props();
  const token = $derived(data.session);

  let query = $state('');
  let zone = $state<'ALL'|'PUBLIC'|'WORKSPACE'|'FAMILY_PRIVATE'>('ALL');
  let results = $state<any[]>([]);
  let files = $state<any[]>([]);
  let searching = $state(false);
  let loadingFiles = $state(false);
  let error = $state('');

  const h = () => ({ Authorization: `Bearer ${token}` });

  async function search() {
    if (!query.trim()) return;
    searching = true; error = '';
    try {
      const params = new URLSearchParams({ q: query, limit: '10' });
      if (zone !== 'ALL') params.set('zone', zone);
      const r = await fetch(`/api/retrieval/search?${params}`, { headers: h() });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Fehler');
      results = d.results ?? d;
    } catch (e: any) { error = e.message; }
    finally { searching = false; }
  }

  async function loadFiles() {
    loadingFiles = true;
    try {
      const r = await fetch('/api/files?limit=20', { headers: h() });
      if (r.ok) files = (await r.json()).items ?? [];
    } catch {} finally { loadingFiles = false; }
  }

  $effect(() => { loadFiles(); });

  function formatSize(b: number) {
    if (b < 1024) return `${b} B`;
    if (b < 1024*1024) return `${(b/1024).toFixed(1)} KB`;
    return `${(b/1024/1024).toFixed(1)} MB`;
  }
</script>

<svelte:head><title>Knowledge Base · Kirobi</title></svelte:head>

<div class="px-4 py-4 sm:px-6 sm:py-6 max-w-7xl mx-auto space-y-4 sm:space-y-6 pb-20 md:pb-0">
  <section class="rounded-3xl border border-cyan-500/20 bg-gradient-to-br from-cyan-900/20 via-gray-900 to-gray-950 p-4 sm:p-6">
    <span class="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs uppercase tracking-widest text-cyan-200">
      <Database class="h-4 w-4" /> Knowledge Base
    </span>
    <h1 class="mt-3 text-2xl md:text-3xl font-bold text-white">Wissens-Datenbank</h1>
    <p class="mt-1 text-sm text-gray-400">RAG-Suche über alle hochgeladenen Dokumente und Embedding-Räume.</p>
  </section>

  <!-- Search -->
  <div class="rounded-3xl border border-white/10 bg-gray-950/70 p-4 sm:p-5 space-y-3">
    <!-- Search input row -->
    <div class="flex gap-2">
      <div class="relative flex-1 min-w-0">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
        <input bind:value={query} onkeydown={e => e.key === 'Enter' && search()} placeholder="Semantische Suche..."
          class="w-full rounded-2xl border border-white/10 bg-black/30 pl-10 pr-4 py-3 text-base text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50"
          style="font-size: 16px;" />
      </div>
      <button onclick={search} disabled={!query.trim() || searching}
        class="flex-shrink-0 flex items-center justify-center rounded-2xl bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 disabled:opacity-50 transition-colors min-h-[44px] min-w-[44px]">
        {#if searching}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Search class="h-4 w-4" />{/if}
      </button>
    </div>

    <!-- Zone filter chips: horizontal scroll -->
    <div class="flex gap-2 overflow-x-auto pb-1" style="scrollbar-width: thin;">
      {#each ['ALL','PUBLIC','WORKSPACE','FAMILY_PRIVATE'] as z}
        <button
          onclick={() => zone = z as any}
          class="flex-shrink-0 px-3 py-1.5 rounded-full border text-xs transition-colors min-h-[36px] whitespace-nowrap {zone === z ? 'border-cyan-500/50 bg-cyan-500/10 text-cyan-300' : 'border-white/10 text-gray-400 hover:text-white'}"
        >{z}</button>
      {/each}
    </div>

    {#if error}<div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{error}</div>{/if}

    {#if results.length > 0}
      <div class="space-y-2">
        {#each results as r}
          <div class="rounded-2xl border border-white/10 bg-black/20 p-4">
            <div class="flex items-start justify-between gap-2 mb-2">
              <span class="text-xs font-mono text-cyan-300 truncate">{r.source ?? r.id}</span>
              <div class="flex gap-2 flex-shrink-0">
                <span class="inline-flex rounded-full border border-white/15 px-2 py-0.5 text-[10px] text-gray-400">{r.zone}</span>
                <span class="inline-flex rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-300">{(r.score * 100).toFixed(0)}%</span>
              </div>
            </div>
            <p class="text-sm text-gray-300 leading-relaxed">{r.snippet}</p>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Files -->
  <div class="rounded-3xl border border-white/10 bg-gray-950/70 p-4 sm:p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white">Hochgeladene Dokumente</h2>
      <a href="{base}/upload" class="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-xs text-gray-300 hover:text-white transition-colors min-h-[36px]">
        <Upload class="h-3.5 w-3.5" /> Upload
      </a>
    </div>
    {#if loadingFiles}
      <p class="text-gray-500 text-sm">Lade...</p>
    {:else if files.length === 0}
      <p class="text-gray-500 text-sm text-center py-4">Keine Dokumente vorhanden.</p>
    {:else}
      <div class="space-y-2">
        {#each files as f}
          <div class="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-2.5 gap-2">
            <div class="min-w-0">
              <p class="text-sm text-white truncate">{f.original_filename ?? f.filename}</p>
              <p class="text-xs text-gray-500">{f.zone} · {formatSize(f.file_size)}</p>
            </div>
            <span class="text-xs text-gray-600 flex-shrink-0">{new Date(f.created_at).toLocaleDateString('de-DE')}</span>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
