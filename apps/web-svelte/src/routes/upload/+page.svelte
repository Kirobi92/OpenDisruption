<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { CloudUpload, FileText, Image, File as FileIcon, Trash2 } from 'lucide-svelte';

  type Zone = 'PUBLIC' | 'WORKSPACE' | 'FAMILY_PRIVATE';

  interface UploadedFile {
    id: string;
    filename: string;
    original_filename: string;
    file_size: number;
    mime_type: string;
    zone: Zone;
    processed?: boolean;
    created_at: string;
  }

  const ZONE_LABELS: Record<Zone, string> = {
    PUBLIC: '🌍 Public',
    WORKSPACE: '💼 Workspace',
    FAMILY_PRIVATE: '👨‍👩‍👦 Family Private',
  };

  const ZONE_COLORS: Record<Zone, string> = {
    PUBLIC: 'bg-green-500/20 text-green-400 border-green-500/30',
    WORKSPACE: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    FAMILY_PRIVATE: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  };

  let selectedZone = $state<Zone>(($page.url.searchParams.get('zone') as Zone) ?? 'WORKSPACE');
  let files = $state<UploadedFile[]>([]);
  let uploading = $state(false);
  let dragOver = $state(false);
  let textMode = $state($page.url.searchParams.get('mode') === 'text');
  let textContent = $state('');
  let textTitle = $state('');

  function token() {
    return typeof localStorage !== 'undefined' ? (localStorage.getItem('access_token') ?? '') : '';
  }

  function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  async function loadFiles() {
    try {
      const res = await fetch('/api/uploads', {
        headers: { Authorization: `Bearer ${token()}` },
      });
      if (res.status === 401) { goto('/login'); return; }
      files = await res.json();
    } catch (e) { console.error(e); }
  }

  async function uploadFile(file: File) {
    uploading = true;
    const fd = new FormData();
    fd.append('file', file);
    fd.append('zone', selectedZone);
    if (selectedZone === 'FAMILY_PRIVATE') {
      const note = window.prompt('FAMILY_PRIVATE-Upload bleibt lokal. Kurze Freigabe-Notiz:',
        'Bewusst lokal für FAMILY_PRIVATE-Suche freigegeben');
      if (!note?.trim()) { uploading = false; return; }
      fd.append('human_approved', 'true');
      fd.append('approval_note', note.trim());
    }
    try {
      await fetch('/api/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token()}` },
        body: fd,
      });
      await loadFiles();
    } catch (e) { console.error(e); alert('Upload fehlgeschlagen'); }
    finally { uploading = false; }
  }

  async function uploadText() {
    if (!textContent.trim()) return;
    uploading = true;
    try {
      await fetch('/api/upload/text', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: textContent, title: textTitle || 'Schnellnotiz', zone: selectedZone }),
      });
      textContent = '';
      textTitle = '';
      await loadFiles();
    } catch (e) { console.error(e); alert('Upload fehlgeschlagen'); }
    finally { uploading = false; }
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    dragOver = false;
    const file = e.dataTransfer?.files[0];
    if (file) void uploadFile(file);
  }

  onMount(() => {
    if (!token()) { goto('/login'); return; }
    void loadFiles();
  });
</script>

<div class="min-h-screen bg-gray-950 text-white px-4 py-8 max-w-4xl mx-auto">
  <div class="mb-8">
    <h1 class="text-3xl font-bold">Upload</h1>
    <p class="text-gray-400 mt-1">Dateien und Texte in den lokalen Wissenspfad</p>
  </div>

  <!-- Zone selector -->
  <div class="flex gap-2 mb-6">
    {#each Object.entries(ZONE_LABELS) as [z, label]}
      <button
        onclick={() => selectedZone = z as Zone}
        class="px-3 py-1.5 text-sm rounded-lg border transition {selectedZone === z ? ZONE_COLORS[z as Zone] : 'border-gray-700 bg-gray-900 text-gray-400 hover:border-gray-600'}"
      >{label}</button>
    {/each}
  </div>

  <!-- Mode toggle -->
  <div class="flex gap-2 mb-6">
    <button onclick={() => textMode = false} class="px-4 py-2 rounded-xl text-sm {!textMode ? 'bg-blue-600' : 'bg-gray-800 hover:bg-gray-700'} transition">Datei</button>
    <button onclick={() => textMode = true} class="px-4 py-2 rounded-xl text-sm {textMode ? 'bg-blue-600' : 'bg-gray-800 hover:bg-gray-700'} transition">Schnellnotiz</button>
  </div>

  {#if textMode}
    <div class="rounded-2xl border border-gray-800 bg-gray-900/80 p-5 mb-6">
      <input
        bind:value={textTitle}
        type="text"
        placeholder="Titel (optional)"
        class="w-full mb-3 px-4 py-2 bg-gray-950 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
      />
      <textarea
        bind:value={textContent}
        placeholder="Inhalt hier eingeben…"
        rows="6"
        class="w-full px-4 py-2 bg-gray-950 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm resize-none"
      ></textarea>
      <button
        onclick={uploadText}
        disabled={uploading || !textContent.trim()}
        class="mt-3 px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm font-medium transition disabled:opacity-50"
      >{uploading ? 'Speichert…' : 'Speichern'}</button>
    </div>
  {:else}
    <!-- Drop zone -->
    <div
      role="button"
      tabindex="0"
      ondragover={(e) => { e.preventDefault(); dragOver = true; }}
      ondragleave={() => dragOver = false}
      ondrop={handleDrop}
      onclick={() => document.getElementById('file-input')?.click()}
      onkeydown={(e) => e.key === 'Enter' && document.getElementById('file-input')?.click()}
      class="rounded-2xl border-2 border-dashed {dragOver ? 'border-blue-400 bg-blue-500/10' : 'border-gray-700 bg-gray-900/40 hover:border-gray-600'} p-12 text-center cursor-pointer transition mb-6"
    >
      <CloudUpload class="w-10 h-10 text-gray-500 mx-auto mb-3" />
      <p class="text-gray-300 font-medium">Datei hier ablegen oder klicken</p>
      <p class="text-sm text-gray-500 mt-1">PDF, Bild, Text, Dokument</p>
      {#if uploading}<p class="text-blue-400 text-sm mt-2">Wird hochgeladen…</p>{/if}
    </div>
    <input
      id="file-input"
      type="file"
      class="hidden"
      onchange={(e) => { const f = (e.target as HTMLInputElement).files?.[0]; if (f) void uploadFile(f); }}
    />
  {/if}

  <!-- Files list -->
  {#if files.length > 0}
    <h2 class="text-lg font-semibold mb-3">Vorhandene Uploads ({files.length})</h2>
    <div class="space-y-2">
      {#each files as f}
        <div class="flex items-center gap-3 rounded-xl border border-gray-800 bg-gray-900/80 p-3">
          {#if f.mime_type?.startsWith('image/')}
            <Image class="w-6 h-6 text-blue-400 shrink-0" />
          {:else if f.mime_type === 'application/pdf'}
            <FileText class="w-6 h-6 text-red-400 shrink-0" />
          {:else}
            <FileIcon class="w-6 h-6 text-gray-400 shrink-0" />
          {/if}
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium truncate">{f.original_filename}</p>
            <p class="text-xs text-gray-500">{formatBytes(f.file_size)} · {new Date(f.created_at).toLocaleDateString('de-DE')}</p>
          </div>
          <span class="text-xs border rounded-full px-2 py-0.5 shrink-0 {ZONE_COLORS[f.zone]}">{ZONE_LABELS[f.zone]}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>
