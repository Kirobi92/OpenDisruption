<script lang="ts">
  import { Mic, Square, Play, Volume2, RefreshCw, Trash2 } from 'lucide-svelte';

  let { data }: { data: any } = $props();
  const token = $derived(data.session);

  let agents = $state<any[]>([]);
  let selectedAgent = $state('');
  let recording = $state(false);
  let processing = $state(false);
  let error = $state('');
  let messages = $state<{role: 'user'|'assistant', text: string, audioUrl?: string}[]>([]);
  let mediaRecorder = $state<MediaRecorder | null>(null);
  let chunks: Blob[] = [];

  const h = () => ({ Authorization: `Bearer ${token}` });

  async function loadAgents() {
    try {
      const r = await fetch('/api/chat/runtime/options', { headers: h() });
      if (r.ok) {
        const d = await r.json();
        agents = d.agent_options ?? [];
        if (agents.length) selectedAgent = agents[0].id;
      }
    } catch {}
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = e => chunks.push(e.data);
      mediaRecorder.onstop = sendAudio;
      mediaRecorder.start();
      recording = true;
    } catch (e: any) { error = 'Mikrofon nicht verfügbar: ' + e.message; }
  }

  function stopRecording() {
    mediaRecorder?.stop();
    recording = false;
  }

  async function sendAudio() {
    if (!chunks.length) return;
    processing = true; error = '';
    try {
      const blob = new Blob(chunks, { type: 'audio/webm' });
      const fd = new FormData();
      fd.append('audio', blob, 'recording.webm');
      if (selectedAgent) fd.append('agent_id', selectedAgent);

      const r = await fetch('/api/voice/chat', { method: 'POST', headers: h(), body: fd });
      if (!r.ok) throw new Error((await r.json()).detail ?? 'Fehler');

      const d = await r.json();
      messages = [...messages, 
        { role: 'user', text: d.transcript ?? '(Sprache erkannt)' },
        { role: 'assistant', text: d.response_text, audioUrl: d.audio_url }
      ];

      if (d.audio_url) {
        new Audio(d.audio_url).play().catch(() => {});
      }
    } catch (e: any) { error = e.message; }
    finally { processing = false; }
  }

  $effect(() => { loadAgents(); });
</script>

<svelte:head><title>Voice Chat · Kirobi</title></svelte:head>

<div class="px-4 py-6 sm:px-6 max-w-3xl mx-auto space-y-6">
  <section class="rounded-3xl border border-sky-500/20 bg-gradient-to-br from-sky-900/20 via-gray-900 to-gray-950 p-6">
    <span class="inline-flex items-center gap-2 rounded-full border border-sky-400/20 bg-sky-400/10 px-3 py-1 text-xs uppercase tracking-widest text-sky-200">
      <Mic class="h-4 w-4" /> Voice Chat
    </span>
    <h1 class="mt-4 text-3xl font-bold text-white">Sprach-Assistent</h1>
    <p class="mt-2 text-sm text-gray-400">Sprich mit deinem Agenten. Lokal, privat, schnell.</p>
  </section>

  <!-- Agent Select -->
  {#if agents.length > 0}
    <select bind:value={selectedAgent} class="w-full rounded-2xl border border-white/10 bg-gray-950/70 px-4 py-2.5 text-sm text-white">
      {#each agents as agent}<option value={agent.id}>{agent.label}</option>{/each}
    </select>
  {/if}

  <!-- Conversation -->
  <div class="min-h-48 space-y-3">
    {#each messages as msg}
      <div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
        <div class="max-w-[80%] rounded-2xl px-4 py-3 {msg.role === 'user' ? 'bg-sky-600/30 border border-sky-500/30' : 'bg-white/[0.04] border border-white/10'}">
          <p class="text-sm text-white">{msg.text}</p>
          {#if msg.audioUrl}
            <audio src={msg.audioUrl} controls class="mt-2 h-8 w-full"></audio>
          {/if}
        </div>
      </div>
    {/each}
    {#if processing}
      <div class="flex justify-start">
        <div class="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3">
          <div class="flex gap-1">
            {#each [0,1,2] as i}
              <div class="h-2 w-2 rounded-full bg-sky-400 animate-bounce" style="animation-delay: {i * 150}ms"></div>
            {/each}
          </div>
        </div>
      </div>
    {/if}
  </div>

  {#if error}
    <div class="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-sm">{error}</div>
  {/if}

  <!-- Controls -->
  <div class="flex items-center justify-center gap-4">
    {#if messages.length > 0}
      <button onclick={() => messages = []} class="p-3 rounded-2xl border border-white/10 hover:bg-white/5 transition-colors text-gray-400">
        <Trash2 class="h-5 w-5" />
      </button>
    {/if}
    <button
      onclick={recording ? stopRecording : startRecording}
      disabled={processing}
      class="p-6 rounded-full transition-all {recording ? 'bg-red-600 hover:bg-red-500 scale-110 shadow-lg shadow-red-500/25' : 'bg-sky-600 hover:bg-sky-500'} disabled:opacity-50">
      {#if processing}
        <RefreshCw class="h-7 w-7 text-white animate-spin" />
      {:else if recording}
        <Square class="h-7 w-7 text-white" />
      {:else}
        <Mic class="h-7 w-7 text-white" />
      {/if}
    </button>
  </div>
  <p class="text-center text-xs text-gray-500">
    {#if recording}Aufnehmen... (nochmal klicken zum Stoppen)
    {:else if processing}Verarbeite...
    {:else}Mikrofon-Button drücken zum Sprechen{/if}
  </p>
</div>
