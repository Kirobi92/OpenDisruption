<script lang="ts">
  import { enhance } from '$app/forms';
  import type { ActionData } from './$types';

  let { form }: { form: ActionData } = $props();

  let loading = $state(false);
  let username = $state('');
  let password = $state('');
</script>

<svelte:head>
  <title>Kirobi · Anmelden</title>
</svelte:head>

<main class="relative min-h-screen overflow-hidden" style="background: linear-gradient(135deg, #040614 0%, #0b0f24 50%, #040614 100%);">
  <div class="pointer-events-none absolute inset-0 z-0" aria-hidden="true">
    <div
      class="absolute top-1/4 left-1/4 w-96 h-96 rounded-full opacity-10"
      style="background: radial-gradient(circle, #5eead4 0%, transparent 70%); filter: blur(60px);"
    ></div>
    <div
      class="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full opacity-10"
      style="background: radial-gradient(circle, #a78bfa 0%, transparent 70%); filter: blur(60px);"
    ></div>
    <div
      class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full opacity-5"
      style="background: radial-gradient(circle, #e879f9 0%, transparent 70%); filter: blur(40px);"
    ></div>
  </div>

  <div class="relative z-10 flex min-h-screen items-center justify-center px-4 py-10">
    <div class="w-full max-w-md space-y-7">
      <div class="text-center">
        <div
          class="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl glass-raised"
        >
          <span class="text-2xl font-bold text-gradient-aurora">K</span>
        </div>
        <h1 class="text-4xl font-semibold">
          <span class="text-gradient-aurora">Kirobi</span>
        </h1>
        <p class="mt-2 text-sm" style="color: var(--text-secondary);">
          Graph-Ansicht v2 · Lokale Intelligenz, sichere Räume.
        </p>
      </div>

      <form
        method="POST"
        class="glass-raised rounded-3xl p-7 space-y-5"
        use:enhance={() => {
          loading = true;
          return async ({ update }) => {
            loading = false;
            await update();
          };
        }}
      >
        {#if form?.error}
          <div
            class="rounded-xl border px-4 py-3 text-sm text-red-300"
            style="border-color: rgba(248, 113, 113, 0.3); background: rgba(239, 68, 68, 0.1);"
            role="alert"
          >
            {form.error}
          </div>
        {/if}

        <div class="space-y-4">
          <div>
            <label for="username" class="mb-2 block text-xs font-medium uppercase" style="letter-spacing: 0.18em; color: var(--text-secondary);">
              Benutzername
            </label>
            <input
              id="username"
              name="username"
              type="text"
              required
              autocomplete="username"
              bind:value={username}
              placeholder="sven, samira oder sineo"
              class="w-full rounded-xl border px-4 py-3 outline-none transition-all duration-300"
              style="border-color: var(--border-soft); background: rgba(4,6,20,0.7); color: var(--text-primary);"
            />
          </div>
          <div>
            <label for="password" class="mb-2 block text-xs font-medium uppercase" style="letter-spacing: 0.18em; color: var(--text-secondary);">
              Passwort
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              autocomplete="current-password"
              bind:value={password}
              placeholder="••••••••"
              class="w-full rounded-xl border px-4 py-3 outline-none transition-all duration-300"
              style="border-color: var(--border-soft); background: rgba(4,6,20,0.7); color: var(--text-primary);"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          class="group relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-2xl px-4 py-3.5 text-sm font-semibold transition-all duration-300"
          style="background: linear-gradient(110deg, #5eead4 0%, #a78bfa 50%, #e879f9 100%); color: #040614; opacity: {loading ? 0.6 : 1}; cursor: {loading ? 'not-allowed' : 'pointer'};"
        >
          <span class="relative">{loading ? 'Anmelden…' : 'Anmelden'}</span>
          {#if !loading}
            <svg class="relative h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fill-rule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clip-rule="evenodd" />
            </svg>
          {/if}
        </button>

        <p class="text-center text-xs" style="color: var(--text-muted);">
          Erstmaliges Einloggen? Standard-Passwort verwenden und dann ändern.
        </p>
      </form>

      <div class="flex items-center justify-center gap-2 text-xs uppercase" style="letter-spacing: 0.22em; color: var(--text-muted);">
        <span class="inline-block h-1.5 w-1.5 rounded-full animate-breathe" style="background: #5eead4;"></span>
        Lokal · Privat · Souverän
      </div>
    </div>
  </div>
</main>
