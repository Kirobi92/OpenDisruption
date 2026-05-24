<script lang="ts">
  import type { PageData } from './$types';
  import { base } from '$app/paths';
  import { MessageCircle, Plus, LogOut, Mic, StopCircle, Paperclip, Send, Settings2, ChevronRight } from 'lucide-svelte';

  let { data }: { data: PageData } = $props();

  interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    created_at: string;
    model_used?: string | null;
    metadata?: {
      agent?: string;
      reasoning_mode?: string;
      reasoning_label?: string;
      visible_reasoning_summary?: string[];
      source_trace?: string[];
    } | null;
  }

  interface Conversation {
    id: string;
    title: string | null;
    zone: string;
    created_at: string;
    updated_at: string;
  }

  type Zone = 'PUBLIC' | 'WORKSPACE' | 'FAMILY_PRIVATE';

  const ZONE_LABELS: Record<Zone, string> = {
    PUBLIC: '🌍 Public',
    WORKSPACE: '💼 Workspace',
    FAMILY_PRIVATE: '👨‍👩‍👦 Family',
  };

  const ZONE_COLORS: Record<Zone, string> = {
    PUBLIC: 'bg-green-500/20 text-green-300 border-green-500/30',
    WORKSPACE: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    FAMILY_PRIVATE: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  };

  let conversations = $state<Conversation[]>([]);
  let activeConversation = $state<Conversation | null>(null);
  let messages = $state<Message[]>([]);
  let input = $state('');
  let loading = $state(false);
  let sidebarOpen = $state(false);
  let selectedZone = $state<Zone>('FAMILY_PRIVATE');
  let availableZones = $state<Zone[]>(['WORKSPACE', 'FAMILY_PRIVATE', 'PUBLIC']);
  let runtimeOptions = $state({ available_models: [] as string[], default_model: 'llama3.1:8b', agent_options: [] as {id:string,label:string}[], reasoning_modes: [] as {id:string,label:string}[], source_modes: [] as {id:string,label:string}[], voice: { available: false } });
  let selectedModel = $state('');
  let selectedAgent = $state('kirobi');
  let reasoningMode = $state('normal');
  let sourceModes = $state<string[]>(['local']);
  let showReasoning = $state(true);
  let settingsOpen = $state(false);
  let recording = $state(false);
  let transcribing = $state(false);
  let messagesEnd: HTMLDivElement | undefined = $state();

  let mediaRecorder: MediaRecorder | null = null;
  let mediaStream: MediaStream | null = null;
  let audioChunks: Blob[] = [];

  const token = $derived(data.session);

  async function apiFetch(path: string, options: RequestInit = {}) {
    const res = await fetch(`/api${path}`, {
      ...options,
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json', ...(options.headers ?? {}) },
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    return res.json();
  }

  async function init() {
    try {
      const [perms, convs, rt] = await Promise.all([
        apiFetch('/auth/me/permissions'),
        apiFetch('/conversations'),
        apiFetch('/chat/runtime/options'),
      ]);
      const writable = (perms.zones ?? []).filter((z: {zone: string, can_write: boolean}) => z.can_write && ZONE_LABELS[z.zone as Zone]).map((z: {zone: Zone}) => z.zone as Zone);
      if (writable.length > 0) availableZones = writable;
      conversations = convs;
      runtimeOptions = rt;
      selectedModel = rt.default_model || '';
      if (convs.length > 0) await selectConversation(convs[0]);
    } catch (e) { console.error(e); }
  }

  async function selectConversation(conv: Conversation) {
    activeConversation = conv;
    sidebarOpen = false;
    try {
      messages = await apiFetch(`/conversations/${conv.id}/messages`);
      setTimeout(() => messagesEnd?.scrollIntoView({ block: 'nearest' }), 50);
    } catch (e) { console.error(e); }
  }

  async function createNew() {
    try {
      const conv = await apiFetch('/conversations', {
        method: 'POST',
        body: JSON.stringify({ title: `${ZONE_LABELS[selectedZone]} Gespräch`, zone: selectedZone }),
      });
      conversations = [conv, ...conversations];
      activeConversation = conv;
      messages = [];
      sidebarOpen = false;
    } catch (e) { console.error(e); }
  }

  async function sendMessage(e: Event) {
    e.preventDefault();
    if (!input.trim() || !activeConversation || loading) return;
    const content = input;
    input = '';
    loading = true;
    messages = [...messages, { id: 'tmp-' + Date.now(), role: 'user', content, created_at: new Date().toISOString() }];
    setTimeout(() => messagesEnd?.scrollIntoView({ block: 'nearest' }), 50);
    try {
      await apiFetch(`/conversations/${activeConversation.id}/messages`, {
        method: 'POST',
        body: JSON.stringify({ content, model: selectedModel || undefined, agent: selectedAgent, reasoning_mode: reasoningMode, source_modes: sourceModes, show_reasoning: showReasoning }),
      });
      messages = await apiFetch(`/conversations/${activeConversation.id}/messages`);
    } catch (e) { console.error(e); }
    finally { loading = false; setTimeout(() => messagesEnd?.scrollIntoView({ block: 'nearest' }), 100); }
  }

  async function toggleVoice() {
    if (recording && mediaRecorder) {
      mediaRecorder.stop();
      recording = false;
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStream = stream;
      audioChunks = [];
      const mr = new MediaRecorder(stream);
      mediaRecorder = mr;
      mr.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
      mr.onstop = async () => {
        transcribing = true;
        try {
          const blob = new Blob(audioChunks, { type: mr.mimeType || 'audio/webm' });
          const fd = new FormData();
          fd.append('audio_file', blob, 'voice.webm');
          fd.append('language', 'de');
          const res = await fetch('/voice/stt/transcribe', { method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: fd });
          if (res.ok) {
            const p = await res.json();
            const t = p.text || p.transcription || '';
            if (t) input = input ? `${input} ${t}` : t;
          }
        } finally {
          mediaStream?.getTracks().forEach(t => t.stop());
          mediaStream = null; audioChunks = []; transcribing = false; recording = false;
        }
      };
      mr.start();
      recording = true;
    } catch { alert('Mikrofonzugriff nicht verfügbar'); }
  }

  $effect(() => { init(); });
  $effect(() => { return () => { mediaStream?.getTracks().forEach(t => t.stop()); }; });
</script>

<svelte:head><title>Chat · Kirobi</title></svelte:head>

<div class="flex bg-gray-950 text-white overflow-hidden" style="height: calc(100dvh - 3.5rem);">
  <!-- Sidebar -->
  <div class="
    {sidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0
    fixed md:static inset-y-0 left-0 z-50 w-72 md:w-64
    bg-gray-900 border-r border-white/10
    transition-transform duration-300 flex flex-col
  ">
    <div class="p-4 border-b border-white/10 space-y-3">
      <p class="font-semibold text-sm">{data.user?.display_name ?? 'Kirobi'}</p>
      <button onclick={createNew} class="w-full flex items-center justify-center gap-2 px-3 py-3 bg-aurora-cyan/15 hover:bg-aurora-cyan/25 text-aurora-cyan rounded-lg text-sm transition-colors min-h-[44px]">
        <Plus class="w-4 h-4" /> Neues Gespräch
      </button>
      <div class="flex flex-wrap gap-1.5">
        {#each availableZones as zone}
          <button onclick={() => selectedZone = zone} class="rounded-full border px-2 py-1 text-xs transition-colors min-h-[36px] {selectedZone === zone ? ZONE_COLORS[zone] : 'border-white/10 text-gray-400'}">
            {ZONE_LABELS[zone]}
          </button>
        {/each}
      </div>
    </div>
    <div class="flex-1 overflow-y-auto p-2">
      {#each conversations as conv}
        <button onclick={() => selectConversation(conv)} class="w-full text-left px-3 py-3 rounded-lg mb-1 transition-colors min-h-[44px] {activeConversation?.id === conv.id ? 'bg-aurora-cyan/15 text-aurora-cyan' : 'hover:bg-white/5 text-gray-300'}">
          <div class="flex items-center gap-2">
            <MessageCircle class="w-4 h-4 flex-shrink-0" />
            <span class="truncate text-sm">{conv.title || 'Gespräch'}</span>
          </div>
          <p class="text-xs text-gray-500 mt-0.5">{new Date(conv.updated_at).toLocaleDateString('de-DE')} · {conv.zone}</p>
        </button>
      {/each}
    </div>
    <div class="p-4 border-t border-white/10">
      <a href="{base}/login" class="w-full flex items-center justify-center gap-2 px-3 py-3 bg-red-600/20 hover:bg-red-600/30 text-red-300 rounded-lg text-sm transition-colors min-h-[44px]">
        <LogOut class="w-4 h-4" /> Abmelden
      </a>
    </div>
  </div>

  <!-- Chat area -->
  <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
    <!-- Header -->
    <div class="border-b border-white/10 bg-gray-900/50 px-4 py-2 flex items-center gap-2 flex-shrink-0">
      <button onclick={() => sidebarOpen = !sidebarOpen} class="md:hidden text-gray-400 hover:text-white p-2 min-h-[44px] min-w-[44px] flex items-center justify-center">
        <MessageCircle class="w-5 h-5" />
      </button>
      {#if activeConversation}
        <span class="rounded-full border px-2 py-0.5 text-xs {ZONE_COLORS[activeConversation.zone as Zone] ?? 'border-white/10 text-gray-300'}">
          {ZONE_LABELS[activeConversation.zone as Zone] ?? activeConversation.zone}
        </span>
        <span class="text-xs text-gray-400 truncate hidden sm:inline">{selectedModel || runtimeOptions.default_model}</span>
        <span class="text-xs text-gray-500 truncate hidden sm:inline">{runtimeOptions.agent_options.find(a => a.id === selectedAgent)?.label ?? selectedAgent}</span>
      {/if}
      <button onclick={() => settingsOpen = !settingsOpen} class="ml-auto flex items-center gap-1 px-2 py-1 rounded-lg border text-xs transition-colors min-h-[44px] min-w-[44px] justify-center {settingsOpen ? 'border-aurora-cyan/40 text-aurora-cyan' : 'border-white/10 text-gray-400 hover:text-white'}">
        <Settings2 class="w-3.5 h-3.5" />
      </button>
    </div>

    {#if settingsOpen}
      <div class="border-b border-white/10 bg-gray-900 px-4 py-3 grid grid-cols-1 md:grid-cols-4 gap-3 flex-shrink-0">
        <label class="space-y-1">
          <span class="text-[10px] uppercase tracking-wider text-gray-500">Agent</span>
          <select bind:value={selectedAgent} class="w-full rounded-lg border border-white/10 bg-gray-950 px-2 py-2 text-base text-white" style="font-size: 16px;">
            {#each runtimeOptions.agent_options as a}<option value={a.id}>{a.label}</option>{/each}
          </select>
        </label>
        <label class="space-y-1">
          <span class="text-[10px] uppercase tracking-wider text-gray-500">Modell</span>
          <select bind:value={selectedModel} class="w-full rounded-lg border border-white/10 bg-gray-950 px-2 py-2 text-base text-white" style="font-size: 16px;">
            {#each (runtimeOptions.available_models.length > 0 ? runtimeOptions.available_models : [runtimeOptions.default_model]) as m}<option value={m}>{m}</option>{/each}
          </select>
        </label>
        <div class="space-y-1">
          <span class="text-[10px] uppercase tracking-wider text-gray-500">Denkgrad</span>
          <div class="flex flex-wrap gap-1">
            {#each runtimeOptions.reasoning_modes as mode}
              <button onclick={() => reasoningMode = mode.id} class="px-2 py-1.5 rounded border text-[10px] transition-colors min-h-[36px] {reasoningMode === mode.id ? 'border-aurora-violet/60 bg-aurora-violet/15 text-aurora-violet' : 'border-white/10 text-gray-400'}">{mode.label}</button>
            {/each}
          </div>
        </div>
        <label class="flex items-center gap-2 text-sm text-gray-300 min-h-[44px]">
          <input type="checkbox" bind:checked={showReasoning} class="rounded border-white/20 w-5 h-5" />
          Reasoning anzeigen
        </label>
      </div>
    {/if}

    <!-- Messages -->
    <div class="flex-1 overflow-y-auto px-4 py-4 space-y-3 pb-4">
      {#if !activeConversation}
        <div class="h-full flex items-center justify-center text-gray-500">
          <div class="text-center px-4">
            <MessageCircle class="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p class="text-sm">Wähle ein Gespräch oder starte ein neues</p>
          </div>
        </div>
      {:else if messages.length === 0}
        <div class="h-full flex items-center justify-center text-gray-500">
          <div class="text-center px-4">
            <p class="text-lg mb-2">Hallo {data.user?.display_name ?? ''}! 👋</p>
            <p class="text-sm">Wie kann ich dir helfen?</p>
          </div>
        </div>
      {:else}
        {#each messages as msg}
          <div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
            <div class="max-w-[85%] p-3 rounded-2xl text-sm {msg.role === 'user' ? 'bg-aurora-cyan/20 text-white' : 'bg-white/5 text-gray-100'}">
              <p class="whitespace-pre-wrap break-words">{msg.content}</p>
              {#if msg.role === 'assistant' && msg.metadata?.visible_reasoning_summary?.length && showReasoning}
                <div class="mt-2 pt-2 border-t border-white/10 space-y-1">
                  {#each msg.metadata.visible_reasoning_summary as s}
                    <p class="text-[10px] text-gray-400">• {s}</p>
                  {/each}
                </div>
              {/if}
              <p class="text-[10px] text-gray-500 mt-1.5">{new Date(msg.created_at).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}</p>
            </div>
          </div>
        {/each}
        {#if loading}
          <div class="flex justify-start">
            <div class="bg-white/5 p-3 rounded-2xl">
              <div class="flex gap-1">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0ms"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:150ms"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:300ms"></div>
              </div>
            </div>
          </div>
        {/if}
        <div bind:this={messagesEnd}></div>
      {/if}
    </div>

    <!-- Input -->
    {#if activeConversation}
      <div class="border-t border-white/10 px-3 py-3 flex-shrink-0" style="padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 0.75rem);">
        <form onsubmit={sendMessage} class="flex items-end gap-2">
          <button type="button" onclick={toggleVoice} disabled={transcribing} class="flex-shrink-0 p-2.5 rounded-xl transition-colors disabled:opacity-50 min-h-[44px] min-w-[44px] flex items-center justify-center {recording ? 'bg-red-600 hover:bg-red-700' : 'bg-white/5 hover:bg-white/10'}">
            {#if recording}<StopCircle class="w-5 h-5" />{:else}<Mic class="w-5 h-5" />{/if}
          </button>
          <textarea
            bind:value={input}
            onkeydown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(e); } }}
            placeholder={transcribing ? 'Transkribiere...' : 'Schreibe eine Nachricht…'}
            disabled={loading || transcribing}
            rows={1}
            class="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-base text-white resize-none focus:outline-none focus:border-aurora-cyan/40 placeholder-gray-600"
            style="font-size: 16px; min-height: 44px; max-height: 120px; overflow-y: auto;"
          ></textarea>
          <button type="submit" disabled={loading || !input.trim()} class="flex-shrink-0 p-2.5 bg-aurora-cyan/20 hover:bg-aurora-cyan/30 text-aurora-cyan rounded-xl transition-colors disabled:opacity-30 min-h-[44px] min-w-[44px] flex items-center justify-center">
            <Send class="w-5 h-5" />
          </button>
        </form>
      </div>
    {/if}
  </div>

  {#if sidebarOpen}
    <button onclick={() => sidebarOpen = false} class="md:hidden fixed inset-0 bg-black/60 z-40" aria-label="Sidebar schließen"></button>
  {/if}
</div>
