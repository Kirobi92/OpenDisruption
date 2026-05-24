<script lang="ts">
  import { CodeSquare, Terminal, Sparkles, ArrowUpRight } from 'lucide-svelte';
  import { base } from '$app/paths';

  const VSCODE_URI = 'vscode://file/home/sven/OpenDisruption';
  const TOOLS = [
    { id: 'vscode', label: 'VS Code', description: 'Repository direkt in VS Code öffnen.', href: VSCODE_URI, icon: CodeSquare, accent: 'from-blue-500/20 to-sky-500/10 border-blue-400/30' },
    { id: 'graph', label: 'Knowledge Graph', description: '3D Wissens-Graph — alle Chunks, Embeddings, Relationen.', href: `${base}/graph`, icon: Sparkles, accent: 'from-violet-500/20 to-purple-500/10 border-violet-400/30' },
    { id: 'workbench', label: 'Workbench', description: 'Service-Übersicht und Embedded-Tools.', href: `${base}/workbench`, icon: Terminal, accent: 'from-emerald-500/20 to-cyan-500/10 border-emerald-400/30' },
    { id: 'knowledge-base', label: 'Knowledge Base', description: 'RAG-Suche und Upload-Verwaltung.', href: `${base}/knowledge-base`, icon: CodeSquare, accent: 'from-amber-500/20 to-orange-500/10 border-amber-400/30' },
  ];
</script>

<svelte:head><title>Developer Studio · Kirobi</title></svelte:head>

<div class="px-4 py-4 sm:px-6 sm:py-6 max-w-7xl mx-auto space-y-4 sm:space-y-6 pb-20 md:pb-0">
  <section class="rounded-3xl border border-emerald-500/20 bg-gradient-to-br from-emerald-900/20 via-gray-900 to-gray-950 p-4 sm:p-6">
    <span class="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs uppercase tracking-widest text-emerald-200">
      <CodeSquare class="h-4 w-4" /> Developer Studio
    </span>
    <h1 class="mt-3 text-2xl md:text-3xl font-bold text-white">Dev-Tools</h1>
    <p class="mt-1 text-sm text-gray-400">Direktzugang zu allen Entwickler-Werkzeugen im OpenDisruption-Stack.</p>
  </section>

  <div class="grid gap-4 grid-cols-1 sm:grid-cols-2">
    {#each TOOLS as tool}
      <a href={tool.href} class="group rounded-2xl border bg-gradient-to-br {tool.accent} p-5 transition hover:scale-[1.02] hover:shadow-lg min-h-[100px]">
        <div class="flex items-start justify-between">
          <svelte:component this={tool.icon} class="h-6 w-6 text-white/70 group-hover:text-white transition" />
          <ArrowUpRight class="h-4 w-4 text-white/40 group-hover:text-white transition" />
        </div>
        <p class="mt-4 text-base font-semibold text-white">{tool.label}</p>
        <p class="mt-1 text-xs text-white/60">{tool.description}</p>
      </a>
    {/each}
  </div>
</div>
