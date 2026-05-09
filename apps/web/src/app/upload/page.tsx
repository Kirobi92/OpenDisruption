'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  CloudArrowUpIcon,
  DocumentTextIcon,
  PhotoIcon,
  DocumentIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import { useClientSearchParams } from '@/lib/use-client-search-params';

type Zone = 'PUBLIC' | 'WORKSPACE' | 'FAMILY_PRIVATE';

interface UploadedFile {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  zone: Zone;
  processed?: boolean;
  metadata?: {
    ingest_status?: string;
    searchable?: boolean;
    preview?: string;
    kind?: string;
    char_count?: number;
    human_approved?: boolean;
    approval_note?: string | null;
  };
  created_at: string;
}

interface Permission {
  zone: Zone | 'SACRED' | 'QUARANTINE';
  can_read: boolean;
  can_write: boolean;
}

interface PermissionsResponse {
  user_id: string;
  username: string;
  zones: Permission[];
}

interface UploadProgress {
  id: string;
  filename: string;
  progress: number;
  status: 'uploading' | 'done' | 'error';
  error?: string;
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

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function FileTypeIcon({ mimeType }: { mimeType: string }) {
  if (mimeType.startsWith('image/')) return <PhotoIcon className="w-8 h-8 text-blue-400" />;
  if (mimeType === 'application/pdf') return <DocumentTextIcon className="w-8 h-8 text-red-400" />;
  return <DocumentIcon className="w-8 h-8 text-gray-400" />;
}

export default function UploadPage() {
  const router = useRouter();
  const searchParams = useClientSearchParams();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [selectedZone, setSelectedZone] = useState<Zone>('WORKSPACE');
  const [availableZones, setAvailableZones] = useState<Zone[]>(['PUBLIC', 'WORKSPACE', 'FAMILY_PRIVATE']);
  const [isDragging, setIsDragging] = useState(false);
  const [uploads, setUploads] = useState<UploadProgress[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(true);
  const [textTitle, setTextTitle] = useState('');
  const [textContent, setTextContent] = useState('');
  const [textSaving, setTextSaving] = useState(false);
  const [textError, setTextError] = useState('');
  const [downloadError, setDownloadError] = useState('');
  const [familyApproval, setFamilyApproval] = useState(false);
  const [approvalNote, setApprovalNote] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textNoteRef = useRef<HTMLTextAreaElement>(null);

  const getAxios = () =>
    axios.create({
      baseURL: '/api',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token') ?? ''}`,
      },
    });

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/');
      return;
    }
    loadPermissions();
    loadFiles();
  }, [router]);

  useEffect(() => {
    const zoneParam = searchParams.get('zone');
    if (zoneParam === 'PUBLIC' || zoneParam === 'WORKSPACE' || zoneParam === 'FAMILY_PRIVATE') {
      setSelectedZone(zoneParam);
    }
    if (searchParams.get('mode') === 'text') {
      window.setTimeout(() => textNoteRef.current?.focus(), 50);
    }
  }, [searchParams]);

  const loadPermissions = async () => {
    try {
      const response = await getAxios().get<PermissionsResponse>('/auth/me/permissions');
      const writable = response.data.zones
        .filter((permission) => permission.can_write && ZONE_LABELS[permission.zone as Zone])
        .map((permission) => permission.zone as Zone);
      if (writable.length > 0) {
        setAvailableZones(writable);
        if (!writable.includes(selectedZone)) {
          setSelectedZone(writable[0]);
        }
      }
    } catch {
      // Supported MVP zones remain available as fallback.
    }
  };

  const loadFiles = async () => {
    setLoadingFiles(true);
    try {
      const response = await getAxios().get<UploadedFile[]>('/uploads');
      setFiles(response.data);
    } catch {
      // Endpoint may not exist yet
    } finally {
      setLoadingFiles(false);
    }
  };

  const uploadFile = async (file: File) => {
    const uploadId = `${file.name}-${file.size}-${file.lastModified}-${crypto.randomUUID()}`;
    const progressEntry: UploadProgress = {
      id: uploadId,
      filename: file.name,
      progress: 0,
      status: 'uploading',
    };
    setUploads((prev) => [...prev, progressEntry]);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('zone', selectedZone);
    if (selectedZone === 'FAMILY_PRIVATE') {
      formData.append('human_approved', String(familyApproval));
      formData.append('approval_note', approvalNote.trim());
    }

    try {
      await getAxios().post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          const percent = event.total
            ? Math.round((event.loaded * 100) / event.total)
            : 0;
          setUploads((prev) =>
            prev.map((u) =>
              u.id === uploadId ? { ...u, progress: percent } : u
            )
          );
        },
      });

      setUploads((prev) =>
        prev.map((u) =>
          u.id === uploadId ? { ...u, progress: 100, status: 'done' } : u
        )
      );
      await loadFiles();
    } catch (err: unknown) {
      const msg =
        axios.isAxiosError(err)
          ? (err.response?.data?.detail ?? 'Upload fehlgeschlagen')
          : 'Unbekannter Fehler';
      setUploads((prev) =>
        prev.map((u) =>
          u.id === uploadId ? { ...u, status: 'error', error: msg } : u
        )
      );
    }
  };

  const handleFiles = (fileList: FileList) => {
    if (selectedZone === 'FAMILY_PRIVATE' && (!familyApproval || !approvalNote.trim())) {
      setUploads((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          filename: 'FAMILY_PRIVATE',
          progress: 0,
          status: 'error',
          error: 'Bitte FAMILY_PRIVATE-Freigabe bestätigen und eine Notiz eingeben.',
        },
      ]);
      return;
    }
    Array.from(fileList).forEach(uploadFile);
  };

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [selectedZone]
  );

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  const clearDoneUploads = () => {
    setUploads((prev) => prev.filter((u) => u.status === 'uploading'));
  };

  const saveTextNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textContent.trim()) return;

    setTextSaving(true);
    setTextError('');
    try {
      await getAxios().post('/uploads/text', {
        title: textTitle.trim() || 'Schnellnotiz',
        content: textContent.trim(),
        zone: selectedZone,
        human_approved: selectedZone === 'FAMILY_PRIVATE' ? familyApproval : false,
        approval_note: selectedZone === 'FAMILY_PRIVATE' ? approvalNote.trim() : null,
      });
      setTextTitle('');
      setTextContent('');
      await loadFiles();
    } catch (err: unknown) {
      const msg =
        axios.isAxiosError(err)
          ? (err.response?.data?.detail ?? 'Text konnte nicht gespeichert werden')
          : 'Unbekannter Fehler';
      setTextError(msg);
    } finally {
      setTextSaving(false);
    }
  };

  const downloadFile = async (file: UploadedFile) => {
    setDownloadError('');
    try {
      const downloadEndpoint = `/api/uploads/${file.id}/download`;
      const response = await axios.get<Blob>(downloadEndpoint, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') ?? ''}`,
        },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = file.original_filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      const msg =
        axios.isAxiosError(err)
          ? (err.response?.data?.detail ?? 'Download fehlgeschlagen')
          : 'Download fehlgeschlagen';
      setDownloadError(msg);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center space-x-3">
          <button
            onClick={() => router.push('/control-center')}
            className="text-gray-400 hover:text-white transition-colors text-sm"
          >
            ← Zurück
          </button>
          <h1 className="text-xl font-bold">Datei-Upload</h1>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {/* Zone Selector */}
        <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-sm font-medium text-gray-400 mb-3">Zone auswählen</h2>
          <div className="flex flex-wrap gap-2">
            {availableZones.map((zone) => (
              <button
                key={zone}
                onClick={() => setSelectedZone(zone)}
                className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                  selectedZone === zone
                    ? ZONE_COLORS[zone]
                    : 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'
                }`}
              >
                {ZONE_LABELS[zone]}
              </button>
            ))}
          </div>
          <p className="mt-3 text-xs text-gray-500">
            SACRED und QUARANTINE bleiben im MVP gesperrt und werden im Backend explizit verweigert.
          </p>
          {searchParams.get('mode') === 'text' && (
            <p className="mt-2 text-xs text-kirobi-300">
              Deeplink aktiv: Schnellnotiz-Modus für unterwegs.
            </p>
          )}
          {selectedZone === 'FAMILY_PRIVATE' && (
            <div className="mt-4 space-y-3 rounded-lg border border-purple-500/30 bg-purple-500/10 p-4 text-sm">
              <p className="text-purple-100">
                FAMILY_PRIVATE-Ingest bleibt lokal und braucht eine explizite Freigabe.
              </p>
              <label className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={familyApproval}
                  onChange={(e) => setFamilyApproval(e.target.checked)}
                  className="mt-1"
                />
                <span>Ich bestätige diesen lokalen FAMILY_PRIVATE-Ingest bewusst.</span>
              </label>
              <textarea
                value={approvalNote}
                onChange={(e) => setApprovalNote(e.target.value)}
                placeholder="Kurze Freigabe-Notiz"
                rows={3}
                className="w-full rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-400"
              />
            </div>
          )}
        </section>

        {/* Drop Zone */}
        <section
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-kirobi-500 bg-kirobi-500/10'
              : 'border-gray-600 hover:border-kirobi-500/50 hover:bg-gray-800/50'
          }`}
        >
          <CloudArrowUpIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-medium text-gray-300">
            Dateien hier ablegen oder klicken
          </p>
          <p className="text-sm text-gray-500 mt-1">
            PDF, TXT oder Markdown — Zone: {ZONE_LABELS[selectedZone]}
          </p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleInputChange}
            className="hidden"
            accept="application/pdf,.txt,.md,text/plain,text/markdown"
          />
        </section>

        <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Schnellnotiz speichern</h2>
            <p className="text-sm text-gray-400 mt-1">
              Text landet lokal in der gewählten Zone und wird direkt im MVP-Suchpfad sichtbar.
            </p>
          </div>

          {textError && (
            <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {textError}
            </div>
          )}

          <form onSubmit={saveTextNote} className="space-y-4">
            <input
              type="text"
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              placeholder="Titel (optional)"
              className="w-full rounded-lg border border-gray-600 bg-gray-700 px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-kirobi-500"
            />
            <textarea
              ref={textNoteRef}
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              placeholder="Text hier einfügen …"
              rows={5}
              className="w-full rounded-lg border border-gray-600 bg-gray-700 px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-kirobi-500"
            />
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-gray-500">
                Zone: {ZONE_LABELS[selectedZone]} · suchbar nach dem Speichern
              </p>
              <button
                type="submit"
                disabled={textSaving || !textContent.trim() || (selectedZone === 'FAMILY_PRIVATE' && (!familyApproval || !approvalNote.trim()))}
                className="rounded-lg bg-kirobi-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-kirobi-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {textSaving ? 'Speichert…' : 'Notiz speichern'}
              </button>
            </div>
          </form>
        </section>

        {downloadError && (
          <section className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {downloadError}
          </section>
        )}

        {/* Upload Progress */}
        {uploads.length > 0 && (
          <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Uploads</h2>
              <button
                onClick={clearDoneUploads}
                className="text-xs text-gray-400 hover:text-white transition-colors"
              >
                Erledigte ausblenden
              </button>
            </div>
            <div className="space-y-3">
              {uploads.map((upload) => (
                <div key={upload.id} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="truncate text-gray-300 max-w-[70%]">{upload.filename}</span>
                    <span
                      className={
                        upload.status === 'done'
                          ? 'text-green-400'
                          : upload.status === 'error'
                          ? 'text-red-400'
                          : 'text-gray-400'
                      }
                    >
                      {upload.status === 'done'
                        ? '✓ Fertig'
                        : upload.status === 'error'
                        ? '✗ Fehler'
                        : `${upload.progress}%`}
                    </span>
                  </div>
                  {upload.status === 'error' && upload.error && (
                    <p className="text-xs text-red-400">{upload.error}</p>
                  )}
                  {upload.status === 'uploading' && (
                    <div className="w-full bg-gray-700 rounded-full h-1.5">
                      <div
                        className="bg-kirobi-500 h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${upload.progress}%` }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* File List */}
        <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Hochgeladene Dateien</h2>
            <button
              onClick={loadFiles}
              className="text-xs text-gray-400 hover:text-white transition-colors"
            >
              Aktualisieren
            </button>
          </div>

          {loadingFiles ? (
            <p className="text-gray-400 text-sm">Laden...</p>
          ) : files.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <DocumentIcon className="w-10 h-10 mx-auto mb-2 opacity-40" />
              <p className="text-sm">Noch keine Dateien hochgeladen</p>
            </div>
          ) : (
            <div className="space-y-2">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center space-x-4 p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  <FileTypeIcon mimeType={file.mime_type} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.original_filename}</p>
                    <div className="flex items-center space-x-2 mt-0.5">
                      <span className="text-xs text-gray-400">{formatBytes(file.file_size)}</span>
                      <span className="text-gray-600">·</span>
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded border ${
                          ZONE_COLORS[file.zone] ?? 'bg-gray-600 text-gray-300 border-gray-500'
                        }`}
                      >
                        {ZONE_LABELS[file.zone] ?? file.zone}
                      </span>
                      <span className="text-gray-600">·</span>
                      <span className="text-xs text-gray-400">
                        {new Date(file.created_at).toLocaleDateString('de-DE')}
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs">
                      <span
                        className={`rounded border px-1.5 py-0.5 ${
                          file.processed
                            ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                            : 'border-amber-500/30 bg-amber-500/10 text-amber-300'
                        }`}
                      >
                        {file.metadata?.ingest_status ?? (file.processed ? 'local-search-ready' : 'metadata-only')}
                      </span>
                      {file.metadata?.kind && (
                        <span className="rounded border border-gray-600 bg-gray-800 px-1.5 py-0.5 text-gray-300">
                          {file.metadata.kind}
                        </span>
                      )}
                      {file.metadata?.human_approved && (
                        <span className="rounded border border-purple-500/30 bg-purple-500/10 px-1.5 py-0.5 text-purple-200">
                          human-approved
                        </span>
                      )}
                      {typeof file.metadata?.char_count === 'number' && (
                        <span className="rounded border border-gray-600 bg-gray-800 px-1.5 py-0.5 text-gray-300">
                          {file.metadata.char_count} Zeichen
                        </span>
                      )}
                    </div>
                    {file.metadata?.approval_note && (
                      <p className="mt-2 text-xs text-purple-200">
                        Freigabe: {file.metadata.approval_note}
                      </p>
                    )}
                    {file.metadata?.preview && (
                      <p className="mt-2 line-clamp-2 text-xs text-gray-400">
                        {file.metadata.preview}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center space-x-1 flex-shrink-0">
                    <button
                      type="button"
                      onClick={() => void downloadFile(file)}
                      className="p-1.5 text-gray-400 hover:text-white transition-colors"
                      title="Herunterladen"
                    >
                      <ArrowDownTrayIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
