<script lang="ts">
  import { User, Key, Shield, LogOut, CheckCircle, XCircle, RefreshCw } from 'lucide-svelte';
  import { goto } from '$app/navigation';
  import { base } from '$app/paths';

  let { data }: { data: any } = $props();
  const token = $derived(data.session);
  const user = $derived(data.user);

  let pwOld = $state('');
  let pwNew = $state('');
  let pwConfirm = $state('');
  let pwLoading = $state(false);
  let pwSuccess = $state('');
  let pwError = $state('');

  const h = () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' });

  async function changePassword() {
    if (pwNew !== pwConfirm) { pwError = 'Passwörter stimmen nicht überein.'; return; }
    if (pwNew.length < 8) { pwError = 'Mindestens 8 Zeichen.'; return; }
    pwLoading = true; pwError = ''; pwSuccess = '';
    try {
      const r = await fetch('/api/auth/change-password', {
        method: 'POST', headers: h(),
        body: JSON.stringify({ old_password: pwOld, new_password: pwNew })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Fehler');
      pwSuccess = 'Passwort geändert.';
      pwOld = pwNew = pwConfirm = '';
    } catch (e: any) { pwError = e.message; }
    finally { pwLoading = false; }
  }

  async function logout() {
    await fetch('/api/auth/logout', { method: 'POST', headers: h() }).catch(() => {});
    await goto(`${base}/login`);
  }
</script>

<svelte:head><title>Einstellungen · Kirobi</title></svelte:head>

<div class="px-4 py-4 sm:px-6 sm:py-6 max-w-2xl mx-auto space-y-4 pb-20 md:pb-0">
  <h1 class="text-2xl font-bold text-white">Einstellungen</h1>

  <!-- Profile -->
  <section class="rounded-3xl border border-white/10 bg-gray-950/70 p-4 sm:p-5 space-y-3">
    <div class="flex items-center gap-3 mb-3">
      <User class="h-5 w-5 text-violet-400 flex-shrink-0" />
      <h2 class="text-sm font-semibold text-white">Profil</h2>
    </div>
    <div class="space-y-2">
      {#each [['Name', user?.name ?? user?.username ?? '—'], ['E-Mail', user?.email ?? '—'], ['Zone', user?.zone ?? '—']] as [label, value]}
        <div class="flex justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-2.5 gap-2">
          <span class="text-xs text-gray-500 flex-shrink-0">{label}</span>
          <span class="text-sm text-white truncate text-right">{value}</span>
        </div>
      {/each}
    </div>
  </section>

  <!-- Change Password -->
  <section class="rounded-3xl border border-white/10 bg-gray-950/70 p-4 sm:p-5 space-y-4">
    <div class="flex items-center gap-3">
      <Key class="h-5 w-5 text-amber-400 flex-shrink-0" />
      <h2 class="text-sm font-semibold text-white">Passwort ändern</h2>
    </div>
    {#each [['Aktuelles Passwort', pwOld, (v: string) => pwOld = v], ['Neues Passwort', pwNew, (v: string) => pwNew = v], ['Bestätigen', pwConfirm, (v: string) => pwConfirm = v]] as [label, val, setter]}
      <div>
        <label class="block text-xs text-gray-500 mb-1">{label}</label>
        <input type="password" value={val} oninput={e => (setter as any)((e.target as HTMLInputElement).value)}
          class="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-base text-white focus:outline-none focus:border-amber-500/50"
          style="font-size: 16px;" />
      </div>
    {/each}
    {#if pwError}<div class="flex items-center gap-2 text-sm text-red-300"><XCircle class="h-4 w-4 flex-shrink-0" />{pwError}</div>{/if}
    {#if pwSuccess}<div class="flex items-center gap-2 text-sm text-emerald-300"><CheckCircle class="h-4 w-4 flex-shrink-0" />{pwSuccess}</div>{/if}
    <button onclick={changePassword} disabled={!pwOld || !pwNew || !pwConfirm || pwLoading}
      class="w-full flex items-center justify-center gap-2 rounded-2xl bg-amber-600 px-5 py-3 text-sm font-medium text-white hover:bg-amber-500 disabled:opacity-50 transition-colors min-h-[44px]">
      {#if pwLoading}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Shield class="h-4 w-4" />{/if}
      Passwort ändern
    </button>
  </section>

  <!-- Logout -->
  <section class="rounded-3xl border border-red-500/20 bg-red-500/5 p-4 sm:p-5">
    <h2 class="text-sm font-semibold text-white mb-3">Session</h2>
    <button onclick={logout} class="w-full flex items-center justify-center gap-2 rounded-2xl border border-red-500/30 bg-red-500/10 px-5 py-3 text-sm font-medium text-red-300 hover:bg-red-500/20 transition-colors min-h-[44px]">
      <LogOut class="h-4 w-4" /> Abmelden
    </button>
  </section>
</div>
