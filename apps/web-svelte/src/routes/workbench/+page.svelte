<script lang="ts">
  import { CheckCircle, XCircle, AlertTriangle, ExternalLink, ArrowUpRight, RefreshCw } from 'lucide-svelte';
  import { page } from '$app/stores';

  let { data }: { data: any } = $props();
  const token = $derived(data.session);

  type ProbeStatus = 'online' | 'offline' | 'unknown';
  interface ProbeResult { status: ProbeStatus; detail: string; }

  const SURFACES = [
    { id: 'knowledge-base', label: 'Knowledge Base', path: '/knowledge-base', directPath: '/knowledge-base', summary: 'Uploads, Wissenssuche, Graph-Einstieg', badge: 'Native', embeddable: false },
    { id: 'chat', label: 'Chat', path: '/chat', directPath: '/chat', summary: 'Direkter Einstieg in lokale Gespräche', badge: 'Native', embeddable: false },
    { id: 'open-webui', label: 'Open WebUI', path: '?surface=open-webui', directPath: '/open-webui/', summary: 'LLM-Workbench für tiefe Modellinteraktion', badge: 'Workbench', embeddable: true },
    { id: 'flowise', label: 'Flowise', path: '?surface=flowise', directPath: '/flowise/', summary: 'Visuelle Flow- und Agent-Orchestrierung', badge: 'Workbench', embeddable: true },
    { id: 'qdrant', label: 'Qdrant', path: '?surface=qdrant', directPath: '/qdrant/dashboard/', summary: 'Vektor-DB-Diagnostik und Collection-Checks', badge: 'Workbench', embeddable: false },
  ];

  const PROBES = [
    { id: 'api', path: '/api/health' },
    { id: 'auth', path: '/api/auth/health' },
    { id: 'telegram', path: '/telegram/health' },
    { id: 'voice', path: '/voice/health' },
  ];

  let probes = $state<Record<string, ProbeResult>>({});
  let probingDone = $state(false);

  let activeSurface = $derived($page.url.searchParams.get('surface') ?? '');
  let surfaceConfig = $derived(SURFACES.find(s => s.id === activeSurface));

  async function runProbes() {
    const results = await Promise.all(PROBES.map(async p => {
      try {
        const r = await fetch(p.path, { cache: 'no-store' });
        return [p.id, { status: r.ok ? 'online' : 'offline', detail: `HTTP ${r.status}` }];
      } catch { return [p.id, { status: 'offline', detail: 'unreachable' }]; }
    }));
    probes = Object.fromEntries(results);
    probingDone = true;
  }

  const BADGE_COLOR: Record<string, string> = {
    Native: 'bg-emerald-500/10 border-emerald-400/30 text-emerald-200',
    Workbench: 'bg-blue-500/10 border-blue-400/30 text-blue-200',
    Ops: 'bg-amber-500/10 border-amber-400/30 text-amber-200',
  };

  $effect(() => { runProbes(); });
</script>

<svelte:head><title>Workbench · Kirobi</title></svelte:head>

<div class="px-4 py-6 sm:px-6 max-w-7xl mx-auto space-y-6">
  {#if !activeSurface}
    <!-- Overview -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">Workbench</h1>
      <button onclick={runProbes} class="p-2 rounded-xl border border-white/10 hover:bg-white/5 transition-colors">
        <RefreshCw class="h-4 w-4 {!probingDone ? 'animate-spin' : ''}" />
      </button>
    </div>

    <!-- Probes -->
    <section class="rounded-3xl border border-white/10 bg-gray-950/70 p-5">
      <h2 class="text-sm font-semibold text-white mb-4">Runtime Health</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
        {#each PROBES as probe}
          {@const r = probes[probe.id]}
          <div class="flex items-center gap-2 rounded-2xl border px-3 py-2.5
            {!r ? 'border-white/10 bg-white/[0.02]' : r.status === 'online' ? 'border-emerald-500/30 bg-emerald-500/10' : 'border-red-500/30 bg-red-500/10'}">
            {#if !r}
              <div class="h-3 w-3 rounded-full bg-gray-600 animate-pulse flex-shrink-0"></div>
            {:else if r.status === 'online'}
              <CheckCircle class="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
            {:else}
              <XCircle class="h-3.5 w-3.5 text-red-400 flex-shrink-0" />
            {/if}
            <span class="text-xs font-medium text-white">{probe.id}</span>
          </div>
        {/each}
      </div>
    </section>

    <!-- Surfaces Grid -->
    <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {#each SURFACES as surface}
        <div class="rounded-2xl border border-white/10 bg-gray-950/70 p-4 space-y-3">
          <div class="flex items-start justify-between">
            <div>
              <span class="inline-flex text-[10px] border rounded-full px-2 py-0.5 {BADGE_COLOR[surface.badge] ?? BADGE_COLOR.Native}">{surface.badge}</span>
              <p class="mt-2 font-semibold text-white">{surface.label}</p>
              <p class="mt-1 text-xs text-gray-500">{surface.summary}</p>
            </div>
          </div>
          <div class="flex gap-2">
            {#if surface.embeddable}
              <a href={surface.path} class="flex-1 flex items-center justify-center gap-1.5 rounded-xl bg-white/[0.05] border border-white/10 py-2 text-xs text-white hover:bg-white/10 transition-colors">
                Einbetten <ArrowUpRight class="h-3 w-3" />
              </a>
            {/if}
            <a href={surface.directPath} target="_blank" class="flex-1 flex items-center justify-center gap-1.5 rounded-xl bg-white/[0.05] border border-white/10 py-2 text-xs text-white hover:bg-white/10 transition-colors">
              Öffnen <ExternalLink class="h-3 w-3" />
            </a>
          </div>
        </div>
      {/each}
    </section>

  {:else if surfaceConfig?.embeddable}
    <!-- Embedded View -->
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-bold text-white">{surfaceConfig.label}</h1>
      <div class="flex gap-2">
        <a href={surfaceConfig.directPath} target="_blank" class="flex items-center gap-2 text-sm text-gray-400 hover:text-white">
          <ExternalLink class="h-4 w-4" /> Neues Tab
        </a>
        <a href="/workbench" class="text-sm text-gray-500 hover:text-white">← Zurück</a>
      </div>
    </div>
    <iframe src={surfaceConfig.directPath} class="w-full h-[calc(100vh-160px)] rounded-2xl border border-white/10" title={surfaceConfig.label}></iframe>
  {:else if activeSurface}
    <div class="rounded-3xl border border-amber-500/20 bg-amber-500/10 p-6 text-center space-y-4">
      <AlertTriangle class="h-8 w-8 text-amber-400 mx-auto" />
      <p class="text-sm text-amber-200">Dieser Service kann nicht eingebettet werden.</p>
      {#if surfaceConfig}
        <a href={surfaceConfig.directPath} target="_blank" class="inline-flex items-center gap-2 rounded-xl bg-amber-600 px-5 py-2.5 text-sm text-white hover:bg-amber-500">
          <ExternalLink class="h-4 w-4" /> In neuem Tab öffnen
        </a>
      {/if}
      <a href="/workbench" class="block text-sm text-gray-500 hover:text-white mt-2">← Zurück</a>
    </div>
  {/if}
</div>
