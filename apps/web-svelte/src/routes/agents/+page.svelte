<script lang="ts">
  import { base } from '$app/paths';
  import { ArrowUpRight, Cpu, Shield, Zap, Sparkles } from 'lucide-svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  const token = $derived(data.session);

  let runtime = $state<{available_models: string[], default_model: string, agent_options: {id:string,label:string,description:string,category?:string,default_model?:string}[]} | null>(null);
  let control = $state<{activeTasks:number,pendingTasks:number,blockedTasks:number,deadLetterTasks:number,operatorGuidance:string[]} | null>(null);

  const CATEGORY_ACCENT: Record<string, string> = {
    core: 'from-violet-500/20 to-sky-500/10 border-violet-400/30',
    orchestrator: 'from-amber-500/20 to-orange-500/10 border-amber-400/30',
    coding: 'from-emerald-500/20 to-cyan-500/10 border-emerald-400/30',
    research: 'from-fuchsia-500/20 to-pink-500/10 border-fuchsia-400/30',
    ops: 'from-rose-500/20 to-red-500/10 border-rose-400/30',
    design: 'from-blue-500/20 to-indigo-500/10 border-blue-400/30',
  };

  $effect(() => {
    async function load() {
      try {
        const headers = { Authorization: `Bearer ${token}` };
        const [rt, ctrl] = await Promise.all([
          fetch('/api/chat/runtime/options', { headers }).then(r => r.ok ? r.json() : null),
          fetch('/api/control/status', { headers }).then(r => r.ok ? r.json() : null),
        ]);
        runtime = rt; control = ctrl;
      } catch {}
    }
    load();
  });
</script>

<svelte:head><title>Agents Hub · Kirobi</title></svelte:head>

<div class="px-4 py-6 sm:px-6 max-w-7xl mx-auto space-y-6">
  <!-- Hero -->
  <section class="rounded-3xl border border-white/10 bg-gradient-to-br from-gray-950 via-slate-900 to-gray-950 p-6">
    <span class="inline-flex items-center gap-2 rounded-full border border-violet-400/20 bg-violet-400/10 px-3 py-1 text-xs uppercase tracking-widest text-violet-200">
      <Cpu class="h-4 w-4" /> Agents Hub
    </span>
    <h1 class="mt-4 text-3xl font-bold text-white">Agenten sichtbar, nicht versteckt.</h1>
    <p class="mt-2 max-w-3xl text-sm text-gray-400">Alle lokalen Agenten laufen auf deiner RTX 3090. Wähle einen Agenten — er bringt sein passendes Modell mit.</p>
    {#if runtime}
      <div class="mt-4 flex flex-wrap gap-2">
        {#each runtime.available_models as m}
          <span class="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-200">
            <span class="h-2 w-2 rounded-full bg-emerald-400"></span>{m}
          </span>
        {/each}
      </div>
    {/if}
  </section>

  <!-- Agent Grid -->
  {#if runtime?.agent_options?.length}
    <section>
      <h2 class="mb-3 text-xs font-mono uppercase tracking-widest text-violet-300">Lokale Agenten ({runtime.agent_options.length})</h2>
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {#each runtime.agent_options as agent}
          {@const accent = CATEGORY_ACCENT[agent.category ?? 'core'] ?? CATEGORY_ACCENT.core}
          <a href="{base}/chat?agent={agent.id}" class="group rounded-2xl border bg-gradient-to-br {accent} p-4 transition hover:scale-[1.02] hover:shadow-lg">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-xs uppercase tracking-widest text-white/50">{agent.category ?? 'core'}</p>
                <p class="mt-2 text-lg font-semibold text-white">{agent.label}</p>
              </div>
              <ArrowUpRight class="h-4 w-4 text-white/50 transition group-hover:text-white" />
            </div>
            <p class="mt-2 line-clamp-2 text-xs text-white/70">{agent.description}</p>
            {#if agent.default_model}
              <div class="mt-3 inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-black/30 px-2 py-0.5 text-[10px] font-mono text-emerald-300">
                <span class="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>{agent.default_model}
              </div>
            {/if}
          </a>
        {/each}
      </div>
    </section>
  {/if}

  <!-- Runtime Pulse -->
  {#if control}
    <section class="rounded-3xl border border-white/10 bg-gray-950/70 p-5">
      <div class="flex items-center gap-2 mb-4">
        <Shield class="h-5 w-5 text-amber-300" />
        <h2 class="text-sm font-semibold text-white">Runtime Pulse</h2>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        {#each [['Active', control.activeTasks], ['Pending', control.pendingTasks], ['Blocked', control.blockedTasks], ['Dead Letter', control.deadLetterTasks]] as [label, value]}
          <div class="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs uppercase tracking-widest text-gray-500">{label}</p>
            <p class="mt-2 text-2xl font-semibold text-white">{value}</p>
          </div>
        {/each}
      </div>
    </section>
  {/if}
</div>
