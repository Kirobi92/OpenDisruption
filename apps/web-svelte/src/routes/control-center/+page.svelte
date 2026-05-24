<script lang="ts">
  import { base } from '$app/paths';
  import {
    CheckCircle, XCircle, AlertTriangle, RefreshCw,
    ArrowUpRight, MessageCircle, Upload, Search, Zap, Sparkles
  } from 'lucide-svelte';

  let { data }: { data: any } = $props();
  const token = $derived(data.session);

  const RUNTIME_PROBES = [
    { id: 'api', path: '/api/health' },
    { id: 'auth', path: '/api/auth/health' },
    { id: 'telegram', path: '/telegram/health' },
    { id: 'voice', path: '/voice/health' },
  ];

  let control = $state<any>(null);
  let activity = $state<any[]>([]);
  let probes = $state<Record<string, {status: string, detail: string}>>({});
  let loading = $state(true);
  let error = $state('');
  let refreshing = $state(false);

  async function refresh() {
    if (!token) return;
    refreshing = true; error = '';
    try {
      const h = { Authorization: `Bearer ${token}` };
      const [ctrl, act, probeResults] = await Promise.all([
        fetch('/api/control/status', { headers: h }).then(r => r.ok ? r.json() : null),
        fetch('/api/dashboard/activity?limit=6', { headers: h }).then(r => r.ok ? r.json() : { items: [] }),
        Promise.all(RUNTIME_PROBES.map(async p => {
          try {
            const r = await fetch(p.path, { cache: 'no-store' });
            return [p.id, { status: r.ok ? 'online' : 'offline', detail: `HTTP ${r.status}` }];
          } catch { return [p.id, { status: 'offline', detail: 'unreachable' }]; }
        })),
      ]);
      control = ctrl; activity = act?.items ?? [];
      probes = Object.fromEntries(probeResults);
    } catch (e: any) { error = e.message; }
    finally { loading = false; refreshing = false; }
  }

  function statusColor(s: string) {
    if (s === 'online') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200';
    if (s === 'offline') return 'border-red-500/30 bg-red-500/10 text-red-200';
    return 'border-amber-500/30 bg-amber-500/10 text-amber-200';
  }

  const QUICK_LINKS = [
    { href: `${base}/chat?new=1`, label: 'Neuer Chat', icon: MessageCircle },
    { href: `${base}/search`, label: 'Suche', icon: Search },
    { href: `${base}/upload`, label: 'Upload', icon: Upload },
    { href: `${base}/agents`, label: 'Agenten', icon: Sparkles },
  ];

  $effect(() => {
    refresh();
    const iv = setInterval(refresh, 30000);
    return () => clearInterval(iv);
  });
</script>

<svelte:head><title>Control Center · Kirobi</title></svelte:head>

<div class="px-4 py-4 sm:px-6 sm:py-6 max-w-7xl mx-auto space-y-4 sm:space-y-6 pb-20 md:pb-0">
  <!-- Hero -->
  <section class="rounded-3xl border border-aurora-cyan/20 bg-gradient-to-br from-aurora-cyan/10 via-gray-900 to-gray-950 p-4 sm:p-6">
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <span class="inline-flex items-center gap-2 rounded-full border border-aurora-cyan/30 bg-aurora-cyan/10 px-3 py-1 text-xs uppercase tracking-widest text-aurora-cyan">
          <Zap class="h-4 w-4 flex-shrink-0" /> Agentic Control Center
        </span>
        <h1 class="mt-3 text-2xl md:text-3xl font-bold text-white">OpenDisruption</h1>
        <p class="mt-1 text-sm text-gray-400">Lokale Intelligenz, sichere Räume. Alles in deiner Hand.</p>
      </div>
      <button onclick={refresh} disabled={refreshing} class="flex-shrink-0 p-2 rounded-xl border border-white/10 hover:bg-white/5 transition-colors disabled:opacity-50 min-h-[44px] min-w-[44px] flex items-center justify-center">
        <RefreshCw class="h-4 w-4 {refreshing ? 'animate-spin' : ''}" />
      </button>
    </div>

    {#if control}
      <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        {#each [['Active', control.activeTasks, 'text-emerald-300'], ['Pending', control.pendingTasks, 'text-amber-300'], ['Blocked', control.blockedTasks, 'text-red-300'], ['Dead Letter', control.deadLetterTasks, 'text-red-400']] as [label, value, color]}
          <div class="rounded-2xl border border-white/10 bg-black/20 p-3 sm:p-4">
            <p class="text-xs uppercase tracking-widest text-gray-500">{label}</p>
            <p class="mt-1 text-3xl md:text-4xl font-semibold {color}">{value ?? 0}</p>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <!-- Quick Links -->
  <section class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
    {#each QUICK_LINKS as link}
      <a href={link.href} class="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-aurora-cyan/30 transition-colors min-h-[56px]">
        <link.icon class="h-5 w-5 text-aurora-cyan flex-shrink-0" />
        <span class="text-sm font-medium text-white">{link.label}</span>
        <ArrowUpRight class="h-4 w-4 text-gray-500 ml-auto flex-shrink-0" />
      </a>
    {/each}
  </section>

  <div class="grid gap-4 sm:gap-6 grid-cols-1 xl:grid-cols-2">
    <!-- Runtime Probes -->
    <section class="rounded-3xl border border-white/10 bg-gray-950/70 p-4 sm:p-5">
      <h2 class="text-sm font-semibold text-white mb-4">Service Health</h2>
      <div class="space-y-2">
        {#each RUNTIME_PROBES as probe}
          {@const result = probes[probe.id] ?? { status: 'unknown', detail: 'prüfe...' }}
          <div class="flex items-center gap-3 rounded-2xl border px-3 py-3 {statusColor(result.status)}">
            {#if result.status === 'online'}<CheckCircle class="h-4 w-4 text-emerald-400 flex-shrink-0" />
            {:else if result.status === 'offline'}<XCircle class="h-4 w-4 text-red-400 flex-shrink-0" />
            {:else}<AlertTriangle class="h-4 w-4 text-amber-400 flex-shrink-0" />{/if}
            <span class="font-medium capitalize text-sm">{probe.id}</span>
            <span class="ml-auto text-xs opacity-70">{result.detail}</span>
          </div>
        {/each}
      </div>
    </section>

    <!-- Recent Activity -->
    <section class="rounded-3xl border border-white/10 bg-gray-950/70 p-4 sm:p-5">
      <h2 class="text-sm font-semibold text-white mb-4">Letzte Aktivität</h2>
      {#if activity.length === 0}
        <p class="text-gray-500 text-sm text-center py-4">Noch keine Aktivität.</p>
      {:else}
        <div class="space-y-2">
          {#each activity as item}
            <div class="rounded-2xl border border-white/10 bg-white/[0.02] px-3 py-2.5">
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs text-gray-300 truncate">{item.summary}</span>
                <span class="text-[10px] text-gray-500 flex-shrink-0">{new Date(item.created_at).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              <p class="text-[10px] text-gray-500 mt-0.5">{item.surface} · {item.actor}</p>
            </div>
          {/each}
        </div>
      {/if}
    </section>
  </div>

  {#if error}
    <div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-red-300 text-sm">{error}</div>
  {/if}
</div>
