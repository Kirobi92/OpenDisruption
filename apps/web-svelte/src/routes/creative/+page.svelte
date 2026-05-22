<script lang="ts">
  import { Image, Music, Film, Sparkles, RefreshCw, Download, CheckCircle, AlertTriangle, Play } from 'lucide-svelte';

  let { data }: { data: any } = $props();
  const token = $derived(data.session);

  type Tab = 'image' | 'music' | 'video';
  let tab = $state<Tab>('image');

  // Image
  let imgPrompt = $state('');
  let imgModel = $state('sdxl-turbo');
  let imgWidth = $state(1024);
  let imgHeight = $state(1024);
  let imgLoading = $state(false);
  let imgError = $state('');
  let imgResult = $state<{id: string, url: string} | null>(null);

  // Music
  let musicPrompt = $state('');
  let musicGenre = $state('');
  let musicDuration = $state(30);
  let musicLoading = $state(false);
  let musicError = $state('');
  let musicResult = $state<{id: string, url?: string} | null>(null);

  // Video
  let videoPrompt = $state('');
  let videoRes = $state('720p');
  let videoDur = $state(5);
  let videoLoading = $state(false);
  let videoError = $state('');
  let videoResult = $state<{id: string, status: string} | null>(null);

  const h = () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' });

  async function generateImage() {
    imgLoading = true; imgError = ''; imgResult = null;
    try {
      const r = await fetch('/api/image-generation/generate', {
        method: 'POST', headers: h(),
        body: JSON.stringify({ prompt: imgPrompt, model_id: imgModel, width: imgWidth, height: imgHeight, zone: 'WORKSPACE' })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Fehler');
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
      if (!r.ok) throw new Error(d.detail || 'Fehler');
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
      if (!r.ok) throw new Error(d.detail || 'Fehler');
      videoResult = { id: d.id, status: d.status };
    } catch (e: any) { videoError = e.message; }
    finally { videoLoading = false; }
  }

  const TABS: { id: Tab; label: string; icon: any }[] = [
    { id: 'image', label: 'Bild', icon: Image },
    { id: 'music', label: 'Musik', icon: Music },
    { id: 'video', label: 'Video', icon: Film },
  ];
</script>

<svelte:head><title>Creative · Kirobi</title></svelte:head>

<div class="px-4 py-6 sm:px-6 max-w-5xl mx-auto space-y-6">
  <section class="rounded-3xl border border-fuchsia-500/20 bg-gradient-to-br from-fuchsia-900/30 via-gray-900 to-gray-950 p-6">
    <span class="inline-flex items-center gap-2 rounded-full border border-fuchsia-400/20 bg-fuchsia-400/10 px-3 py-1 text-xs uppercase tracking-widest text-fuchsia-200">
      <Sparkles class="h-4 w-4" /> Creative AI
    </span>
    <h1 class="mt-4 text-3xl font-bold text-white">Generative AI Studio</h1>
    <p class="mt-2 text-sm text-gray-400">Bild · Musik · Video — alles lokal auf deiner RTX 3090.</p>
  </section>

  <!-- Tabs -->
  <div class="flex gap-2">
    {#each TABS as t}
      <button onclick={() => tab = t.id}
        class="flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-colors
               {tab === t.id ? 'bg-fuchsia-500/20 border border-fuchsia-400/30 text-fuchsia-200' : 'border border-white/10 text-gray-400 hover:text-white'}">
        <t.icon class="h-4 w-4" />{t.label}
      </button>
    {/each}
  </div>

  <!-- Image Tab -->
  {#if tab === 'image'}
    <div class="rounded-3xl border border-white/10 bg-gray-950/70 p-5 space-y-4">
      <textarea bind:value={imgPrompt} placeholder="Beschreibe das Bild..." rows={3}
        class="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-fuchsia-500/50"></textarea>
      <div class="flex flex-wrap gap-3">
        <select bind:value={imgModel} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white">
          <option value="sdxl-turbo">SDXL Turbo</option>
          <option value="sdxl">SDXL</option>
          <option value="sd15">SD 1.5</option>
        </select>
        <select bind:value={imgWidth} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white">
          <option value={512}>512px</option>
          <option value={768}>768px</option>
          <option value={1024}>1024px</option>
        </select>
        <span class="self-center text-gray-500">×</span>
        <select bind:value={imgHeight} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white">
          <option value={512}>512px</option>
          <option value={768}>768px</option>
          <option value={1024}>1024px</option>
        </select>
        <button onclick={generateImage} disabled={!imgPrompt || imgLoading}
          class="ml-auto flex items-center gap-2 rounded-xl bg-fuchsia-600 px-5 py-2 text-sm font-medium text-white hover:bg-fuchsia-500 disabled:opacity-50 transition-colors">
          {#if imgLoading}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Sparkles class="h-4 w-4" />{/if}
          Generieren
        </button>
      </div>
      {#if imgError}<div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{imgError}</div>{/if}
      {#if imgResult}
        <div class="rounded-2xl border border-fuchsia-500/20 overflow-hidden">
          <img src={imgResult.url} alt="Generated" class="w-full" />
          <div class="flex justify-end p-3">
            <a href={imgResult.url} download class="flex items-center gap-2 rounded-xl border border-white/10 px-3 py-1.5 text-sm text-gray-300 hover:text-white">
              <Download class="h-4 w-4" /> Speichern
            </a>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Music Tab -->
  {#if tab === 'music'}
    <div class="rounded-3xl border border-white/10 bg-gray-950/70 p-5 space-y-4">
      <textarea bind:value={musicPrompt} placeholder="Beschreibe den Musik-Track..." rows={3}
        class="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-fuchsia-500/50"></textarea>
      <div class="flex flex-wrap gap-3">
        <input bind:value={musicGenre} placeholder="Genre (optional)" class="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none" />
        <select bind:value={musicDuration} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white">
          {#each [15, 30, 60, 120] as s}<option value={s}>{s}s</option>{/each}
        </select>
        <button onclick={generateMusic} disabled={!musicPrompt || musicLoading}
          class="ml-auto flex items-center gap-2 rounded-xl bg-fuchsia-600 px-5 py-2 text-sm font-medium text-white hover:bg-fuchsia-500 disabled:opacity-50 transition-colors">
          {#if musicLoading}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Music class="h-4 w-4" />{/if}
          Komponieren
        </button>
      </div>
      {#if musicError}<div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{musicError}</div>{/if}
      {#if musicResult?.url}
        <div class="rounded-2xl border border-fuchsia-500/20 p-4 space-y-2">
          <audio src={musicResult.url} controls class="w-full"></audio>
          <a href={musicResult.url} download class="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white">
            <Download class="h-4 w-4" /> Download
          </a>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Video Tab -->
  {#if tab === 'video'}
    <div class="rounded-3xl border border-white/10 bg-gray-950/70 p-5 space-y-4">
      <textarea bind:value={videoPrompt} placeholder="Beschreibe die Video-Szene..." rows={3}
        class="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-fuchsia-500/50"></textarea>
      <div class="flex flex-wrap gap-3">
        <select bind:value={videoRes} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white">
          <option value="480p">480p</option>
          <option value="720p">720p</option>
          <option value="1080p">1080p</option>
        </select>
        <select bind:value={videoDur} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white">
          {#each [3, 5, 10, 15] as s}<option value={s}>{s}s</option>{/each}
        </select>
        <button onclick={generateVideo} disabled={!videoPrompt || videoLoading}
          class="ml-auto flex items-center gap-2 rounded-xl bg-fuchsia-600 px-5 py-2 text-sm font-medium text-white hover:bg-fuchsia-500 disabled:opacity-50 transition-colors">
          {#if videoLoading}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Film class="h-4 w-4" />{/if}
          Rendern
        </button>
      </div>
      {#if videoError}<div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{videoError}</div>{/if}
      {#if videoResult}
        <div class="rounded-2xl border border-white/10 p-4 flex items-center gap-3">
          <CheckCircle class="h-5 w-5 text-emerald-400" />
          <div>
            <p class="text-sm text-white">Job gestartet · ID: {videoResult.id}</p>
            <p class="text-xs text-gray-500">Status: {videoResult.status} — Render dauert je nach Länge mehrere Minuten.</p>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>
