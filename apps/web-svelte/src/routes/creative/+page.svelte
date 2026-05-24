<script lang="ts">
  import {
    Image, Music, Film, Clapperboard,
    RefreshCw, Download, CheckCircle, Sparkles, Play
  } from 'lucide-svelte';

  let { data }: { data: any } = $props();
  const token = $derived(data.session);

  type Tab = 'image' | 'music' | 'video' | 'lipsync';
  let tab = $state<Tab>('image');

  // ── Image ──────────────────────────────────────────
  let imgPrompt = $state('');
  let imgModel  = $state('sdxl-turbo');
  let imgWidth  = $state(1024);
  let imgHeight = $state(1024);
  let imgLoading = $state(false);
  let imgError   = $state('');
  let imgResult  = $state<{ id: string; url: string } | null>(null);

  // ── Music ──────────────────────────────────────────
  let musicPrompt   = $state('');
  let musicGenre    = $state('');
  let musicDuration = $state(30);
  let musicLoading  = $state(false);
  let musicError    = $state('');
  let musicResult   = $state<{ id: string; url?: string } | null>(null);

  // ── Video ──────────────────────────────────────────
  let videoPrompt  = $state('');
  let videoRes     = $state('720p');
  let videoDur     = $state(5);
  let videoLoading = $state(false);
  let videoError   = $state('');
  let videoResult  = $state<{ id: string; status: string } | null>(null);

  // ── LipSync ────────────────────────────────────────
  let lipText    = $state('');
  let lipProfile = $state('');
  let lipLoading = $state(false);
  let lipError   = $state('');
  let lipResult  = $state<any>(null);
  let profiles   = $state<any[]>([]);

  // ── Helpers ────────────────────────────────────────
  const h = () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' });

  async function loadProfiles() {
    try {
      const r = await fetch('/api/voice/profiles', { headers: { Authorization: `Bearer ${token}` } });
      if (r.ok) profiles = await r.json();
    } catch {}
  }

  $effect(() => { if (tab === 'lipsync') loadProfiles(); });

  async function generateImage() {
    imgLoading = true; imgError = ''; imgResult = null;
    try {
      const r = await fetch('/api/image-generation/generate', {
        method: 'POST', headers: h(),
        body: JSON.stringify({ prompt: imgPrompt, model_id: imgModel, width: imgWidth, height: imgHeight, zone: 'WORKSPACE' })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail ?? 'Fehler');
      imgResult = { id: d.id, url: d.url ?? `/api/image-generation/${d.id}/download` };
    } catch (e: any) { imgError = e.message; }
    finally { imgLoading = false; }
  }

  async function generateMusic() {
    musicLoading = true; musicError = ''; musicResult = null;
    try {
      const r = await fetch('/api/music-generation/generate', {
        method: 'POST', headers: h(),
        body: JSON.stringify({ prompt: musicPrompt, genre: musicGenre, duration_seconds: musicDuration, zone: 'WORKSPACE' })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail ?? 'Fehler');
      musicResult = { id: d.id, url: d.url ?? `/api/music-generation/${d.id}/download` };
    } catch (e: any) { musicError = e.message; }
    finally { musicLoading = false; }
  }

  async function generateVideo() {
    videoLoading = true; videoError = ''; videoResult = null;
    try {
      const r = await fetch('/api/video-generation/generate', {
        method: 'POST', headers: h(),
        body: JSON.stringify({ prompt: videoPrompt, resolution: videoRes, duration_seconds: videoDur, zone: 'WORKSPACE' })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail ?? 'Fehler');
      videoResult = { id: d.id, status: d.status };
    } catch (e: any) { videoError = e.message; }
    finally { videoLoading = false; }
  }

  async function generateLipSync() {
    lipLoading = true; lipError = ''; lipResult = null;
    try {
      const r = await fetch('/api/voice/lipsync', {
        method: 'POST', headers: h(),
        body: JSON.stringify({ text: lipText, profile_id: lipProfile, zone: 'WORKSPACE' })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail ?? 'Fehler');
      lipResult = d;
    } catch (e: any) { lipError = e.message; }
    finally { lipLoading = false; }
  }

  const TABS: { id: Tab; label: string; icon: any }[] = [
    { id: 'image',   label: 'Bild',    icon: Image        },
    { id: 'music',   label: 'Musik',   icon: Music        },
    { id: 'video',   label: 'Video',   icon: Film         },
    { id: 'lipsync', label: 'LipSync', icon: Clapperboard },
  ];
</script>

<svelte:head><title>Kreativ-Studio · Kirobi</title></svelte:head>

<!-- Wrapper: kein horizontales Scrollen, volle Höhe auf Mobile -->
<div class="flex flex-col min-h-[calc(100vh-56px)] md:min-h-[calc(100vh-52px)]">

  <!-- Header – kompakt auf Mobile -->
  <div class="px-4 pt-5 pb-3 md:px-6 md:pt-7">
    <div class="flex items-center gap-2">
      <Sparkles class="h-5 w-5 text-fuchsia-400 shrink-0" />
      <h1 class="text-xl font-bold text-white tracking-tight">Kreativ-Studio</h1>
    </div>
    <p class="mt-0.5 text-xs text-gray-500">Lokal · RTX 3090 · Kein Cloud-Upload</p>
  </div>

  <!-- Tab-Bar – scrollbar auf sehr kleinen Screens -->
  <div class="px-4 md:px-6">
    <div class="flex gap-1.5 overflow-x-auto pb-1 no-scrollbar">
      {#each TABS as t}
        <button
          onclick={() => tab = t.id}
          class="flex items-center gap-1.5 whitespace-nowrap rounded-xl px-4 py-2 text-sm font-medium border transition-colors shrink-0
                 {tab === t.id
                   ? 'bg-fuchsia-500/20 border-fuchsia-400/30 text-fuchsia-200'
                   : 'border-white/10 text-gray-400 hover:text-white hover:border-white/20'}"
        >
          <t.icon class="h-4 w-4" />{t.label}
        </button>
      {/each}
    </div>
  </div>

  <!-- Tab-Content -->
  <div class="flex-1 px-4 py-4 md:px-6 md:py-5">

    <!-- ── BILD ─────────────────────────────────────── -->
    {#if tab === 'image'}
      <div class="space-y-3">
        <textarea
          bind:value={imgPrompt}
          placeholder="Beschreibe das Bild… z.B. 'Futuristische Stadt bei Nacht, Cyberpunk-Stil'"
          rows={4}
          class="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-fuchsia-500/40"
        ></textarea>

        <!-- Controls -->
        <div class="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:gap-2">
          <select bind:value={imgModel} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2.5 text-sm text-white col-span-2 sm:col-auto">
            <option value="sdxl-turbo">SDXL Turbo (schnell)</option>
            <option value="sdxl">SDXL (Qualität)</option>
            <option value="sd15">SD 1.5 (leicht)</option>
          </select>
          <select bind:value={imgWidth} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2.5 text-sm text-white">
            <option value={512}>512 px</option>
            <option value={768}>768 px</option>
            <option value={1024}>1024 px</option>
          </select>
          <select bind:value={imgHeight} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2.5 text-sm text-white">
            <option value={512}>512 px</option>
            <option value={768}>768 px</option>
            <option value={1024}>1024 px</option>
          </select>
        </div>

        <button
          onclick={generateImage}
          disabled={!imgPrompt || imgLoading}
          class="w-full flex items-center justify-center gap-2 rounded-2xl bg-fuchsia-600 py-3 text-sm font-semibold text-white hover:bg-fuchsia-500 disabled:opacity-40 transition-colors"
        >
          {#if imgLoading}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Sparkles class="h-4 w-4" />{/if}
          {imgLoading ? 'Generiere…' : 'Bild generieren'}
        </button>

        {#if imgError}
          <div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{imgError}</div>
        {/if}
        {#if imgResult}
          <div class="rounded-2xl border border-fuchsia-500/20 overflow-hidden">
            <img src={imgResult.url} alt="Generiertes Bild" class="w-full" />
            <div class="flex justify-end p-3 bg-black/20">
              <a href={imgResult.url} download class="flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-1.5 text-xs text-gray-300 hover:text-white">
                <Download class="h-3.5 w-3.5" /> Speichern
              </a>
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- ── MUSIK ─────────────────────────────────────── -->
    {#if tab === 'music'}
      <div class="space-y-3">
        <textarea
          bind:value={musicPrompt}
          placeholder="Beschreibe den Track… z.B. 'Entspannter Lo-Fi Hip-Hop, Regen im Hintergrund'"
          rows={4}
          class="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-fuchsia-500/40"
        ></textarea>

        <div class="grid grid-cols-2 gap-2">
          <input
            bind:value={musicGenre}
            placeholder="Genre (optional)"
            class="rounded-xl border border-white/10 bg-black/30 px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none col-span-1"
          />
          <select bind:value={musicDuration} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2.5 text-sm text-white">
            {#each [15, 30, 60, 120] as s}<option value={s}>{s} Sek.</option>{/each}
          </select>
        </div>

        <button
          onclick={generateMusic}
          disabled={!musicPrompt || musicLoading}
          class="w-full flex items-center justify-center gap-2 rounded-2xl bg-fuchsia-600 py-3 text-sm font-semibold text-white hover:bg-fuchsia-500 disabled:opacity-40 transition-colors"
        >
          {#if musicLoading}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Music class="h-4 w-4" />{/if}
          {musicLoading ? 'Komponiere…' : 'Musik komponieren'}
        </button>

        {#if musicError}
          <div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{musicError}</div>
        {/if}
        {#if musicResult?.url}
          <div class="rounded-2xl border border-fuchsia-500/20 bg-black/20 p-4 space-y-3">
            <audio src={musicResult.url} controls class="w-full"></audio>
            <a href={musicResult.url} download class="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white">
              <Download class="h-3.5 w-3.5" /> Download
            </a>
          </div>
        {/if}
        {#if musicResult && !musicResult.url}
          <div class="flex items-center gap-3 rounded-2xl border border-white/10 p-4">
            <CheckCircle class="h-5 w-5 text-emerald-400 shrink-0" />
            <div>
              <p class="text-sm text-white">Job gestartet · ID: {musicResult.id}</p>
              <p class="text-xs text-gray-500">Musik wird generiert — dauert ca. 1–2 Min.</p>
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- ── VIDEO ─────────────────────────────────────── -->
    {#if tab === 'video'}
      <div class="space-y-3">
        <textarea
          bind:value={videoPrompt}
          placeholder="Beschreibe die Video-Szene… z.B. 'Zeitlupe Wasserfall im Wald, 4K'"
          rows={4}
          class="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-fuchsia-500/40"
        ></textarea>

        <div class="grid grid-cols-2 gap-2">
          <select bind:value={videoRes} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2.5 text-sm text-white">
            <option value="480p">480p</option>
            <option value="720p">720p (Standard)</option>
            <option value="1080p">1080p (HD)</option>
          </select>
          <select bind:value={videoDur} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2.5 text-sm text-white">
            {#each [3, 5, 10, 15] as s}<option value={s}>{s} Sek.</option>{/each}
          </select>
        </div>

        <button
          onclick={generateVideo}
          disabled={!videoPrompt || videoLoading}
          class="w-full flex items-center justify-center gap-2 rounded-2xl bg-fuchsia-600 py-3 text-sm font-semibold text-white hover:bg-fuchsia-500 disabled:opacity-40 transition-colors"
        >
          {#if videoLoading}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Film class="h-4 w-4" />{/if}
          {videoLoading ? 'Rendere…' : 'Video rendern'}
        </button>

        {#if videoError}
          <div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{videoError}</div>
        {/if}
        {#if videoResult}
          <div class="flex items-start gap-3 rounded-2xl border border-white/10 p-4">
            <CheckCircle class="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <p class="text-sm text-white font-medium">Job gestartet · ID: {videoResult.id}</p>
              <p class="text-xs text-gray-500 mt-0.5">Status: {videoResult.status} — Render dauert je nach Länge mehrere Minuten.</p>
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- ── LIPSYNC ─────────────────────────────────────── -->
    {#if tab === 'lipsync'}
      <div class="space-y-3">
        <textarea
          bind:value={lipText}
          placeholder="Text für LipSync-Avatar… z.B. 'Willkommen bei OpenDisruption!'"
          rows={4}
          class="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-fuchsia-500/40"
        ></textarea>

        {#if profiles.length > 0}
          <select bind:value={lipProfile} class="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-2.5 text-sm text-white">
            <option value="">Voice-Profil wählen…</option>
            {#each profiles as p}<option value={p.id}>{p.name}</option>{/each}
          </select>
        {:else}
          <p class="text-xs text-gray-500 px-1">Keine Voice-Profile vorhanden — erst im Voice-Studio ein Profil anlegen.</p>
        {/if}

        <button
          onclick={generateLipSync}
          disabled={!lipText || lipLoading}
          class="w-full flex items-center justify-center gap-2 rounded-2xl bg-fuchsia-600 py-3 text-sm font-semibold text-white hover:bg-fuchsia-500 disabled:opacity-40 transition-colors"
        >
          {#if lipLoading}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Clapperboard class="h-4 w-4" />{/if}
          {lipLoading ? 'Generiere…' : 'LipSync generieren'}
        </button>

        {#if lipError}
          <div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{lipError}</div>
        {/if}
        {#if lipResult}
          <div class="rounded-2xl border border-fuchsia-500/20 bg-black/20 p-4 space-y-2">
            {#if lipResult.video_url}
              <video src={lipResult.video_url} controls class="w-full rounded-xl"><track kind="captions" /></video>
            {/if}
            <p class="text-xs text-gray-500">Job: {lipResult.id}</p>
          </div>
        {/if}
      </div>
    {/if}

  </div>
</div>
