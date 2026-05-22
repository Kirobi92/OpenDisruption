<script lang="ts">
  import { Mic, Plus, Trash2, RefreshCw, Download, Square, User } from 'lucide-svelte';

  let { data }: { data: any } = $props();
  const token = $derived(data.session);

  let profiles = $state<any[]>([]);
  let selectedProfile = $state<string | null>(null);
  let newProfileName = $state('');
  let generating = $state(false);
  let genPrompt = $state('');
  let genResult = $state<{id: string, url: string} | null>(null);
  let error = $state('');
  let loadingProfiles = $state(true);
  let recording = $state(false);
  let chunks: Blob[] = [];
  let mediaRecorder: MediaRecorder | null = null;

  const h = () => ({ Authorization: `Bearer ${token}` });

  async function loadProfiles() {
    loadingProfiles = true;
    try {
      const r = await fetch('/api/voice/profiles', { headers: h() });
      if (r.ok) profiles = await r.json();
    } catch {} finally { loadingProfiles = false; }
  }

  async function createProfile() {
    if (!newProfileName.trim()) return;
    try {
      const r = await fetch('/api/voice/profiles', {
        method: 'POST', headers: { ...h(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newProfileName })
      });
      if (r.ok) { newProfileName = ''; await loadProfiles(); }
    } catch (e: any) { error = e.message; }
  }

  async function deleteProfile(id: string) {
    await fetch(`/api/voice/profiles/${id}`, { method: 'DELETE', headers: h() });
    if (selectedProfile === id) selectedProfile = null;
    await loadProfiles();
  }

  async function generate() {
    if (!genPrompt || !selectedProfile) return;
    generating = true; error = ''; genResult = null;
    try {
      const r = await fetch('/api/voice/generate', {
        method: 'POST', headers: { ...h(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: genPrompt, profile_id: selectedProfile, zone: 'WORKSPACE' })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail ?? 'Fehler');
      genResult = { id: d.id, url: d.url ?? `/api/voice/${d.id}/download` };
    } catch (e: any) { error = e.message; }
    finally { generating = false; }
  }

  async function startSample() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = e => chunks.push(e.data);
      mediaRecorder.onstop = uploadSample;
      mediaRecorder.start();
      recording = true;
    } catch (e: any) { error = 'Mikrofon: ' + e.message; }
  }

  function stopSample() {
    mediaRecorder?.stop();
    recording = false;
  }

  async function uploadSample() {
    if (!selectedProfile || !chunks.length) return;
    const blob = new Blob(chunks, { type: 'audio/webm' });
    const fd = new FormData();
    fd.append('audio', blob, 'sample.webm');
    const r = await fetch(`/api/voice/profiles/${selectedProfile}/samples`, { method: 'POST', headers: h(), body: fd });
    if (!r.ok) error = 'Sample-Upload fehlgeschlagen';
    else await loadProfiles();
  }

  $effect(() => { loadProfiles(); });
</script>

<svelte:head><title>Voice Studio · Kirobi</title></svelte:head>

<div class="px-4 py-6 sm:px-6 max-w-5xl mx-auto space-y-6">
  <section class="rounded-3xl border border-purple-500/20 bg-gradient-to-br from-purple-900/20 via-gray-900 to-gray-950 p-6">
    <span class="inline-flex items-center gap-2 rounded-full border border-purple-400/20 bg-purple-400/10 px-3 py-1 text-xs uppercase tracking-widest text-purple-200">
      <Mic class="h-4 w-4" /> Voice Studio
    </span>
    <h1 class="mt-4 text-3xl font-bold text-white">Voice Studio</h1>
    <p class="mt-2 text-sm text-gray-400">Voice-Profile, Sampling und Sprachsynthese — lokal auf RTX 3090.</p>
  </section>

  <div class="grid gap-6 xl:grid-cols-2">
    <!-- Profiles -->
    <section class="rounded-3xl border border-white/10 bg-gray-950/70 p-5 space-y-4">
      <h2 class="text-sm font-semibold text-white">Voice Profile</h2>
      <div class="flex gap-2">
        <input bind:value={newProfileName} placeholder="Neues Profil..." onkeydown={e => e.key === 'Enter' && createProfile()}
          class="flex-1 rounded-2xl border border-white/10 bg-black/30 px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none" />
        <button onclick={createProfile} disabled={!newProfileName.trim()}
          class="p-2 rounded-2xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 transition-colors">
          <Plus class="h-4 w-4 text-white" />
        </button>
      </div>
      {#if loadingProfiles}
        <p class="text-gray-500 text-sm">Lade...</p>
      {:else if profiles.length === 0}
        <p class="text-gray-500 text-sm text-center py-2">Noch keine Profile.</p>
      {:else}
        <div class="space-y-2">
          {#each profiles as profile}
            <div class="flex items-center gap-3 rounded-2xl border px-3 py-2.5 cursor-pointer transition-colors
                        {selectedProfile === profile.id ? 'border-purple-400/30 bg-purple-500/10' : 'border-white/10 hover:border-white/20'}"
              role="button" tabindex="0" onclick={() => selectedProfile = profile.id} onkeydown={e => e.key === 'Enter' && (selectedProfile = profile.id)}>
              <User class="h-4 w-4 text-purple-300 flex-shrink-0" />
              <div class="flex-1 min-w-0">
                <p class="text-sm text-white truncate">{profile.name}</p>
                <p class="text-xs text-gray-500">{profile.sample_count ?? 0} Samples</p>
              </div>
              <button onclick={e => { e.stopPropagation(); deleteProfile(profile.id); }} class="p-1 rounded text-gray-500 hover:text-red-400 transition-colors">
                <Trash2 class="h-3.5 w-3.5" />
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </section>

    <!-- Generate / Sample -->
    <div class="space-y-4">
      <!-- Sample Recording -->
      {#if selectedProfile}
        <section class="rounded-3xl border border-white/10 bg-gray-950/70 p-5 space-y-3">
          <h2 class="text-sm font-semibold text-white">Sample aufnehmen</h2>
          <div class="flex items-center justify-center">
            <button onclick={recording ? stopSample : startSample}
              class="p-5 rounded-full transition-all {recording ? 'bg-red-600 hover:bg-red-500 scale-110' : 'bg-gray-700 hover:bg-gray-600'}">
              {#if recording}<Square class="h-6 w-6 text-white" />{:else}<Mic class="h-6 w-6 text-white" />{/if}
            </button>
          </div>
          <p class="text-center text-xs text-gray-500">{recording ? 'Aufnehmen...' : 'Klicken zum Aufnehmen'}</p>
        </section>
      {/if}

      <!-- TTS Generate -->
      <section class="rounded-3xl border border-white/10 bg-gray-950/70 p-5 space-y-4">
        <h2 class="text-sm font-semibold text-white">Sprache generieren</h2>
        <textarea bind:value={genPrompt} placeholder="Text für Sprachsynthese..." rows={4}
          class="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none" ></textarea>
        {#if !selectedProfile}
          <p class="text-xs text-amber-300">← Profil auswählen</p>
        {/if}
        <button onclick={generate} disabled={!genPrompt || !selectedProfile || generating}
          class="flex items-center gap-2 rounded-2xl bg-purple-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-purple-500 disabled:opacity-50 transition-colors">
          {#if generating}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Mic class="h-4 w-4" />{/if}
          Generieren
        </button>
        {#if genResult}
          <div class="rounded-2xl border border-purple-500/20 p-3 space-y-2">
            <audio src={genResult.url} controls class="w-full"></audio>
            <a href={genResult.url} download class="inline-flex items-center gap-2 text-xs text-gray-400 hover:text-white">
              <Download class="h-3.5 w-3.5" /> Download
            </a>
          </div>
        {/if}
      </section>
    </div>
  </div>

  {#if error}
    <div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{error}</div>
  {/if}
</div>
