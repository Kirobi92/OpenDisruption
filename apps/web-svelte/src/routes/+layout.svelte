<script lang="ts">
  import '../app.css';
  import AppNav from '$lib/components/AppNav.svelte';
  import type { Snippet } from 'svelte';
  import { page } from '$app/stores';
  import { base } from '$app/paths';

  let { children }: { children: Snippet } = $props();

  const isLoginPage = $derived($page.url.pathname === `${base}/login` || $page.url.pathname === `${base}/login/`);
  const isGraphPage = $derived($page.url.pathname === `${base}/graph` || $page.url.pathname.startsWith(`${base}/graph/`));
</script>

<div class="min-h-screen flex flex-col" style="background: var(--bg-void); color: var(--text-primary);">
  <AppNav />
  <main class="flex-1 {!isLoginPage && !isGraphPage ? 'pb-16 md:pb-0' : ''}">
    {@render children()}
  </main>
</div>
