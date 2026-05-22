<script lang="ts">
  import { onMount } from 'svelte';
  import { RefreshCw, CheckCircle, XCircle, ExternalLink } from 'lucide-svelte';

  interface ServiceProbe {
    name: string;
    url: string;
    ok: boolean;
    detail?: string;
  }

  const PROBES = [
    { name: 'web', url: '/health' },
    { name: 'auth', url: '/api/auth/health' },
    { name: 'api', url: '/api/health' },
  ];

  const PARTS = [
    { name: 'Kirobi PWA', path: '/chat', description: 'Familien-Chat, Login und Alltags-Einstieg.', guard: 'JWT-Login' },
    { name: 'Stack Status', path: '/status', description: 'Diese zentrale Übersicht und Live-Probes.', guard: 'Reverse Proxy' },
    { name: 'Open WebUI', path: '/open-webui/', description: 'Lokales LLM-Workbench für Ollama-Modelle.', guard: 'LAN/Tailscale + Open WebUI Login' },
    { name: 'Flowise', path: '/flowise/', description: 'Workflow-Orchestrierung und visuelle Agent-Flows.', guard: 'LAN/Tailscale + Flowise Login' },
    { name: 'Qdrant Dashboard', path: '/qdrant/dashboard', description: 'Vektor-DB Diagnoseoberfläche.', guard: 'LAN/Tailscale only' },
    { name: 'API', path: '/api/health', description: 'Backend-API hinter dem Reverse Proxy.', guard: 'JWT für Fach-Endpunkte' },
    { name: 'Auth', path: '/api/auth/health', description: 'Login, Sessions und Zonen-Berechtigungen.', guard: 'JWT-Service' },
    { name: 'Voice', path: '/voice/health', description: 'Voice/STT/TTS-Service hinter Caddy.', guard: 'LAN/Tailscale only' },
  ];

  let results = $state<ServiceProbe[]>([]);
  let running = $state(false);

  async function runProbes() {
    running = true;
    const checks = await Promise.all(
      PROBES.map(async (p) => {
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), 4000);
        try {
          const res = await fetch(p.url, { signal: ctrl.signal, cache: 'no-store' });
          return { name: p.name, url: p.url, ok: res.ok, detail: `HTTP ${res.status}` };
        } catch (err) {
          return { name: p.name, url: p.url, ok: false, detail: err instanceof Error ? err.message : 'unreachable' };
        } finally {
          clearTimeout(timer);
        }
      })
    );
    results = checks;
    running = false;
  }

  onMount(() => { void runProbes(); });
</script>

<div class="min-h-screen bg-gray-950 text-white px-4 py-8 max-w-4xl mx-auto">
  <div class="flex items-center justify-between mb-8">
    <div>
      <h1 class="text-3xl font-bold">Stack Status</h1>
      <p class="text-gray-400 mt-1">Live-Probes und Service-Übersicht</p>
    </div>
    <button
      onclick={runProbes}
      disabled={running}
      class="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl text-sm transition disabled:opacity-50"
    >
      <RefreshCw class="w-4 h-4 {running ? 'animate-spin' : ''}" />
      {running ? 'Prüft…' : 'Neu prüfen'}
    </button>
  </div>

  {#if results.length > 0}
    <div class="grid grid-cols-3 gap-3 mb-8">
      {#each results as r}
        <div class="rounded-2xl border {r.ok ? 'border-emerald-500/30 bg-emerald-500/10' : 'border-red-500/30 bg-red-500/10'} p-4">
          <div class="flex items-center gap-2 mb-1">
            {#if r.ok}
              <CheckCircle class="w-4 h-4 text-emerald-400" />
            {:else}
              <XCircle class="w-4 h-4 text-red-400" />
            {/if}
            <span class="font-semibold">{r.name}</span>
          </div>
          <p class="text-xs text-gray-400">{r.detail}</p>
        </div>
      {/each}
    </div>
  {/if}

  <div class="space-y-3">
    {#each PARTS as part}
      <a
        href={part.path}
        class="flex items-center justify-between rounded-2xl border border-gray-800 bg-gray-900/80 p-4 hover:border-gray-600 transition group"
      >
        <div>
          <p class="font-semibold">{part.name}</p>
          <p class="text-sm text-gray-400 mt-0.5">{part.description}</p>
          <p class="text-xs text-gray-600 mt-1">Guard: {part.guard}</p>
        </div>
        <ExternalLink class="w-4 h-4 text-gray-500 group-hover:text-gray-300 transition" />
      </a>
    {/each}
  </div>
</div>
