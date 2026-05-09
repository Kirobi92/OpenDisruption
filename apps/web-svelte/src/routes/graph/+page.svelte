<script lang="ts">
  import { browser } from '$app/environment';
  import { base } from '$app/paths';
  import type { GraphData, GraphNode } from '$lib/graph/types.js';
  import { FilterState } from '$lib/graph/filters.svelte.js';

  let Graph3D = $state<any>(null);
  let FilterPanel = $state<any>(null);
  let NodeDetail = $state<any>(null);

  let graphData = $state<GraphData | null>(null);
  let filters = new FilterState();
  let selectedNode = $state<GraphNode | null>(null);
  let hoveredNode = $state<GraphNode | null>(null);
  let sidebarOpen = $state(true);
  let detailOpen = $state(false);
  let loading = $state(true);
  let error = $state('');

  const visibleNodeCount = $derived(
    graphData ? graphData.nodes.filter((n) => filters.isNodeVisible(n)).length : 0
  );
  const visibleEdgeCount = $derived(
    graphData ? graphData.links.filter((e) => filters.isEdgeVisible(e)).length : 0
  );

  async function loadGraph() {
    try {
      const resp = await fetch(`${base}/repo-graph.json`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      graphData = await resp.json() as GraphData;
    } catch (e) {
      error = `Graph-Daten konnten nicht geladen werden: ${e}`;
    } finally {
      loading = false;
    }
  }

  if (browser) {
    loadGraph().then(async () => {
      const [g, f, nd] = await Promise.all([
        import('$lib/components/Graph3D.svelte'),
        import('$lib/components/FilterPanel.svelte'),
        import('$lib/components/NodeDetail.svelte'),
      ]);
      Graph3D = g.default;
      FilterPanel = f.default;
      NodeDetail = nd.default;
    });
  }

  function handleNodeClick(node: GraphNode | null) {
    selectedNode = node;
    detailOpen = !!node;
  }

  function handleNodeHover(node: GraphNode | null) {
    hoveredNode = node;
  }

  async function handleLogout() {
    await fetch(`${base}/api/logout`, { method: 'POST' });
    window.location.href = `${base}/login`;
  }
</script>

<svelte:head>
  <title>Kirobi · Repo-Graph v2</title>
</svelte:head>

<div class="flex h-screen overflow-hidden" style="background: #040614;">
  <div class="flex-1 relative overflow-hidden">
    <div class="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-2 glass-raised border-b" style="border-color: var(--border-soft);">
      <div class="flex items-center gap-3">
        <span class="text-sm font-semibold text-gradient-aurora">Kirobi Graph v2</span>
        {#if graphData}
          <span class="text-xs" style="color: var(--text-muted);">
            {graphData.meta.node_count} Knoten · {graphData.meta.link_count} Kanten
          </span>
        {/if}
      </div>
      <div class="flex items-center gap-2">
        {#if hoveredNode}
          <span class="text-xs px-2 py-1 rounded" style="background: rgba(255,255,255,0.06); color: var(--text-secondary);">
            {hoveredNode.label}
          </span>
        {/if}
        <button
          onclick={() => sidebarOpen = !sidebarOpen}
          class="text-xs px-3 py-1 rounded-lg transition-colors"
          style="background: rgba(255,255,255,0.06); color: var(--text-secondary);"
        >
          {sidebarOpen ? 'Filter ←' : '→ Filter'}
        </button>
        <button
          onclick={handleLogout}
          class="text-xs px-3 py-1 rounded-lg transition-colors"
          style="background: rgba(255,255,255,0.04); color: var(--text-muted);"
        >
          Abmelden
        </button>
      </div>
    </div>

    <div class="absolute inset-0 pt-10">
      {#if loading}
        <div class="flex items-center justify-center h-full">
          <div class="text-center space-y-3">
            <div class="inline-block h-8 w-8 rounded-full border-2 border-t-transparent animate-spin" style="border-color: #5eead4; border-top-color: transparent;"></div>
            <p class="text-sm" style="color: var(--text-secondary);">Graph wird geladen…</p>
          </div>
        </div>
      {:else if error}
        <div class="flex items-center justify-center h-full">
          <div class="text-center space-y-2 max-w-sm px-4">
            <p class="text-sm text-red-400">{error}</p>
          </div>
        </div>
      {:else if graphData && Graph3D}
        <Graph3D
          graph={graphData}
          {filters}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
        />
      {/if}
    </div>

    {#if hoveredNode && !loading}
      <div
        class="absolute top-14 left-4 z-20 max-w-xs glass-raised rounded-xl p-3 pointer-events-none"
        style="border-color: var(--border-soft);"
      >
        <div class="text-sm font-semibold" style="color: var(--text-primary);">{hoveredNode.label}</div>
        <div class="text-xs mt-1 space-y-0.5">
          <div style="color: var(--text-muted);">{hoveredNode.zone} · {hoveredNode.quadrant} · {hoveredNode.spiral}</div>
          <div style="color: var(--text-muted);">{hoveredNode.dir}</div>
          {#if hoveredNode.tags.length > 0}
            <div style="color: var(--text-muted);">{hoveredNode.tags.join(', ')}</div>
          {/if}
        </div>
      </div>
    {/if}
  </div>

  {#if sidebarOpen && FilterPanel}
    <div class="w-72 glass-raised border-l overflow-hidden flex flex-col" style="border-color: var(--border-soft);">
      {#if detailOpen && selectedNode && NodeDetail}
        <div class="flex-1 overflow-hidden">
          <NodeDetail
            node={selectedNode}
            edges={graphData?.links ?? []}
            onClose={() => { detailOpen = false; selectedNode = null; }}
          />
        </div>
      {:else if graphData}
        <div class="flex-1 overflow-hidden">
          <FilterPanel
            {filters}
            graph={graphData}
            {visibleNodeCount}
            {visibleEdgeCount}
          />
        </div>
      {/if}
    </div>
  {/if}
</div>
