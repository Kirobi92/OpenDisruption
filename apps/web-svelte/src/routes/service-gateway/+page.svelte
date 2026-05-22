<script lang="ts">
  import { page } from '$app/stores';
  import { ExternalLink, AlertTriangle } from 'lucide-svelte';

  const TARGETS: Record<string, { path: string; embeddable: boolean; label: string }> = {
    'open-webui': { path: '/open-webui/', embeddable: true, label: 'Open WebUI' },
    flowise: { path: '/flowise/', embeddable: true, label: 'Flowise' },
    qdrant: { path: '/qdrant/dashboard/', embeddable: false, label: 'Qdrant' },
  };

  const ALL_TARGETS = Object.entries(TARGETS);

  let target = $derived($page.url.searchParams.get('target') ?? '');
  let config = $derived(TARGETS[target]);
</script>

<svelte:head><title>Service Gateway · Kirobi</title></svelte:head>

<div class="px-4 py-6 sm:px-6 max-w-7xl mx-auto space-y-6">
  {#if !target}
    <h1 class="text-2xl font-bold text-white">Service Gateway</h1>
    <div class="grid gap-4 sm:grid-cols-3">
      {#each ALL_TARGETS as [id, svc]}
        <a href="?target={id}" class="rounded-2xl border border-white/10 bg-gray-950/70 p-5 hover:border-violet-500/30 transition-colors">
          <p class="font-semibold text-white">{svc.label}</p>
          <p class="mt-1 text-xs text-gray-500">{svc.embeddable ? 'Einbettbar' : 'Externer Link'} · {svc.path}</p>
        </a>
      {/each}
    </div>
  {:else if !config}
    <div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-red-300">
      Unbekannter Service: {target}
    </div>
  {:else if config.embeddable}
    <div class="flex items-center justify-between mb-3">
      <h1 class="text-xl font-bold text-white">{config.label}</h1>
      <a href={config.path} target="_blank" class="flex items-center gap-2 text-sm text-gray-400 hover:text-white">
        <ExternalLink class="h-4 w-4" /> Neues Tab
      </a>
    </div>
    <iframe src={config.path} class="w-full h-[calc(100vh-160px)] rounded-2xl border border-white/10" title={config.label}></iframe>
  {:else}
    <div class="rounded-3xl border border-amber-500/20 bg-amber-500/10 p-6 text-center space-y-4">
      <AlertTriangle class="h-8 w-8 text-amber-400 mx-auto" />
      <h2 class="text-lg font-semibold text-white">{config.label}</h2>
      <p class="text-sm text-amber-200">Dieser Service kann nicht eingebettet werden.</p>
      <a href={config.path} target="_blank" class="inline-flex items-center gap-2 rounded-xl bg-amber-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-amber-500 transition-colors">
        <ExternalLink class="h-4 w-4" /> In neuem Tab öffnen
      </a>
    </div>
  {/if}
</div>
