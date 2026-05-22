<script lang="ts">
  import { Image, Film, RefreshCw, Download, CheckCircle, AlertTriangle } from 'lucide-svelte';

  let { data }: { data: any } = $props();
  const token = $derived(data.session);

  type Tab = 'image' | 'video' | 'lipsync';
  let tab = $state<Tab>('image');

  // Image
  let imgPrompt = $state(''); let imgModel = $state('sdxl-turbo');
  let imgW = $state(1024); let imgH = $state(1024);
  let imgLoading = $state(false); let imgError = $state('');
  let imgResult = $state<{id:string,url:string}|null>(null);

  // Video
  let videoPrompt = $state(''); let videoRes = $state('720p'); let videoDur = $state(5);
  let videoLoading = $state(false); let videoError = $state('');
  let videoResult = $state<{id:string,status:string}|null>(null);

  // LipSync
  let lipText = $state(''); let lipProfile = $state('');
  let lipLoading = $state(false); let lipError = $state(''); let lipResult = $state<any>(null);
  let profiles = $state<any[]>([]);

  const h = () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' });

  async function loadProfiles() {
    try {
      const r = await fetch('/api/voice/profiles', { headers: { Authorization: `Bearer ${token}` } });
      if (r.ok) profiles = await r.json();
    } catch {}
  }

  async function generateImage() {
    imgLoading = true; imgError = ''; imgResult = null;
    try {
      const r = await fetch('/api/image-generation/generate', { method: 'POST', headers: h(), body: JSON.stringify({ prompt: imgPrompt, model_id: imgModel, width: imgW, height: imgH, zone: 'WORKSPACE' }) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail ?? 'Fehler');
      imgResult = { id: d.id, url: d.url ?? `/api/image-generation/${d.id}/download` };
    } catch (e: any) { imgError = e.message; } finally { imgLoading = false; }
  }

  async function generateVideo() {
    videoLoading = true; videoError = ''; videoResult = null;
    try {
      const r = await fetch('/api/video-generation/generate', { method: 'POST', headers: h(), body: JSON.stringify({ prompt: videoPrompt, resolution: videoRes, duration_seconds: videoDur, zone: 'WORKSPACE' }) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail ?? 'Fehler');
      videoResult = { id: d.id, status: d.status };
    } catch (e: any) { videoError = e.message; } finally { videoLoading = false; }
  }

  async function generateLipSync() {
    lipLoading = true; lipError = ''; lipResult = null;
    try {
      const r = await fetch('/api/voice/lipsync', { method: 'POST', headers: h(), body: JSON.stringify({ text: lipText, profile_id: lipProfile, zone: 'WORKSPACE' }) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail ?? 'Fehler');
      lipResult = d;
    } catch (e: any) { lipError = e.message; } finally { lipLoading = false; }
  }

  $effect(() => { loadProfiles(); });

  const TABS = [
    { id: 'image' as Tab, label: 'Image', icon: Image },
    { id: 'video' as Tab, label: 'Video', icon: Film },
    { id: 'lipsync' as Tab, label: 'LipSync', icon: Image },
  ];
</script>

<svelte:head><title>Studio · Kirobi</title></svelte:head>

<div class="px-4 py-6 sm:px-6 max-w-5xl mx-auto space-y-6">
  <section class="rounded-3xl border border-rose-500/20 bg-gradient-to-br from-rose-900/20 via-gray-900 to-gray-950 p-6">
    <h1 class="text-3xl font-bold text-white">Generative AI Studio</h1>
    <p class="mt-2 text-sm text-gray-400">Image · Video · LipSync — lokal auf RTX 3090.</p>
  </section>

  <div class="flex gap-2">
    {#each TABS as t}
      <button onclick={() => tab = t.id}
        class="flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium border transition-colors
               {tab === t.id ? 'bg-rose-500/20 border-rose-400/30 text-rose-200' : 'border-white/10 text-gray-400 hover:text-white'}">
        <t.icon class="h-4 w-4" />{t.label}
      </button>
    {/each}
  </div>

  {#if tab === 'image'}
    <div class="rounded-3xl border border-white/10 bg-gray-950/70 p-5 space-y-4">
      <textarea bind:value={imgPrompt} rows={3} placeholder="Bildbeschreibung..."
        class="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none" ></textarea>
      <div class="flex flex-wrap gap-3">
        <select bind:value={imgModel} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white">
          <option value="sdxl-turbo">SDXL Turbo</option><option value="sdxl">SDXL</option><option value="sd15">SD 1.5</option>
        </select>
        <button onclick={generateImage} disabled={!imgPrompt || imgLoading}
          class="ml-auto flex items-center gap-2 rounded-xl bg-rose-600 px-5 py-2 text-sm text-white hover:bg-rose-500 disabled:opacity-50">
          {#if imgLoading}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Image class="h-4 w-4" />{/if} Generieren
        </button>
      </div>
      {#if imgError}<div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{imgError}</div>{/if}
      {#if imgResult}<img src={imgResult.url} alt="Generated" class="w-full rounded-2xl border border-white/10" />{/if}
    </div>
  {/if}

  {#if tab === 'video'}
    <div class="rounded-3xl border border-white/10 bg-gray-950/70 p-5 space-y-4">
      <textarea bind:value={videoPrompt} rows={3} placeholder="Video-Beschreibung..."
        class="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none" ></textarea>
      <div class="flex flex-wrap gap-3">
        <select bind:value={videoRes} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white">
          <option value="480p">480p</option><option value="720p">720p</option><option value="1080p">1080p</option>
        </select>
        <select bind:value={videoDur} class="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white">
          {#each [3,5,10,15] as s}<option value={s}>{s}s</option>{/each}
        </select>
        <button onclick={generateVideo} disabled={!videoPrompt || videoLoading}
          class="ml-auto flex items-center gap-2 rounded-xl bg-rose-600 px-5 py-2 text-sm text-white hover:bg-rose-500 disabled:opacity-50">
          {#if videoLoading}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Film class="h-4 w-4" />{/if} Rendern
        </button>
      </div>
      {#if videoError}<div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{videoError}</div>{/if}
      {#if videoResult}<div class="flex items-center gap-3 rounded-2xl border border-white/10 p-4"><CheckCircle class="h-5 w-5 text-emerald-400" /><p class="text-sm text-white">Job: {videoResult.id} · {videoResult.status}</p></div>{/if}
    </div>
  {/if}

  {#if tab === 'lipsync'}
    <div class="rounded-3xl border border-white/10 bg-gray-950/70 p-5 space-y-4">
      <textarea bind:value={lipText} rows={3} placeholder="Text für LipSync..."
        class="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none" ></textarea>
      {#if profiles.length > 0}
        <select bind:value={lipProfile} class="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-2.5 text-sm text-white">
          <option value="">Voice-Profil wählen...</option>
          {#each profiles as p}<option value={p.id}>{p.name}</option>{/each}
        </select>
      {/if}
      <button onclick={generateLipSync} disabled={!lipText || lipLoading}
        class="flex items-center gap-2 rounded-xl bg-rose-600 px-5 py-2 text-sm text-white hover:bg-rose-500 disabled:opacity-50">
        {#if lipLoading}<RefreshCw class="h-4 w-4 animate-spin" />{:else}<Film class="h-4 w-4" />{/if} LipSync generieren
      </button>
      {#if lipError}<div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{lipError}</div>{/if}
      {#if lipResult}
        <div class="rounded-2xl border border-rose-500/20 p-4">
          {#if lipResult.video_url}<video src={lipResult.video_url} controls class="w-full rounded-xl"><track kind="captions" /></video>{/if}
          <p class="text-xs text-gray-500 mt-2">Job: {lipResult.id}</p>
        </div>
      {/if}
    </div>
  {/if}
</div>
