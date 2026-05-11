'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  FolderOpenIcon,
  PencilSquareIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

type ConfigFileSummary = {
  id: string;
  label: string;
  path: string;
  editable: boolean;
  description: string;
  warning?: string;
  obfuscated: boolean;
};

type ConfigFilePayload = ConfigFileSummary & {
  exists: boolean;
  content: string;
};

type DiffLine = {
  lineNumber: number;
  original: string;
  updated: string;
};

function buildPreview(original: string, updated: string): DiffLine[] {
  const originalLines = original.split('\n');
  const updatedLines = updated.split('\n');
  const maxLength = Math.max(originalLines.length, updatedLines.length);
  const preview: DiffLine[] = [];

  for (let index = 0; index < maxLength; index += 1) {
    const before = originalLines[index] ?? '';
    const after = updatedLines[index] ?? '';
    if (before !== after) {
      preview.push({ lineNumber: index + 1, original: before, updated: after });
    }
  }

  return preview;
}

export default function ConfigPage() {
  const [files, setFiles] = useState<ConfigFileSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<ConfigFilePayload | null>(null);
  const [originalContent, setOriginalContent] = useState('');
  const [draftContent, setDraftContent] = useState('');
  const [loadingList, setLoadingList] = useState(true);
  const [loadingFile, setLoadingFile] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadFile = useCallback(async (fileId: string) => {
    setLoadingFile(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`/api/config?file=${encodeURIComponent(fileId)}`, { cache: 'no-store' });
      const payload = (await response.json()) as ConfigFilePayload & { error?: string };
      if (!response.ok) {
        throw new Error(payload.error ?? 'Datei konnte nicht geladen werden.');
      }
      setSelectedId(fileId);
      setSelectedFile(payload);
      setOriginalContent(payload.content);
      setDraftContent(payload.content);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Datei konnte nicht geladen werden.');
    } finally {
      setLoadingFile(false);
    }
  }, []);

  const loadFiles = useCallback(async () => {
    setLoadingList(true);
    setError(null);

    try {
      const response = await fetch('/api/config', { cache: 'no-store' });
      const payload = (await response.json()) as { files?: ConfigFileSummary[]; error?: string };
      if (!response.ok) {
        throw new Error(payload.error ?? 'Dateiliste konnte nicht geladen werden.');
      }
      const nextFiles = payload.files ?? [];
      setFiles(nextFiles);
      const nextSelectedId = selectedId ?? nextFiles[0]?.id ?? null;
      if (nextSelectedId) {
        await loadFile(nextSelectedId);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Dateiliste konnte nicht geladen werden.');
    } finally {
      setLoadingList(false);
    }
  }, [loadFile, selectedId]);

  useEffect(() => {
    void loadFiles();
  }, [loadFiles]);

  const dirty = selectedFile?.editable ? draftContent !== originalContent : false;
  const diffPreview = useMemo(() => buildPreview(originalContent, draftContent), [originalContent, draftContent]);

  const handleSave = useCallback(async () => {
    if (!selectedFile?.editable || !dirty) return;

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: selectedFile.id, content: draftContent }),
      });
      const payload = (await response.json()) as {
        error?: string;
        details?: string;
        message?: string;
        file?: ConfigFilePayload;
      };
      if (!response.ok) {
        throw new Error(payload.details ? `${payload.error}\n${payload.details}` : payload.error ?? 'Speichern fehlgeschlagen.');
      }
      if (payload.file) {
        setSelectedFile(payload.file);
        setOriginalContent(payload.file.content);
        setDraftContent(payload.file.content);
      }
      setSuccess(payload.message ?? 'Datei gespeichert.');
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Speichern fehlgeschlagen.');
    } finally {
      setSaving(false);
    }
  }, [dirty, draftContent, selectedFile]);

  return (
    <>
      <header className="sticky top-0 z-10 border-b border-gray-700/60 bg-gray-900/80 px-6 py-4 backdrop-blur">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-base font-semibold text-white">Config</h1>
            <p className="mt-0.5 text-xs text-gray-500">Allowlist-basierter Editor für Compose, Hermes, Caddy und sichere Referenzdateien.</p>
          </div>
          <div className="flex items-center gap-3 flex-wrap justify-end">
            {selectedFile?.editable && dirty && (
              <span className="rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-400">
                Ungespeicherte Änderungen
              </span>
            )}
            <button
              onClick={() => void loadFiles()}
              disabled={loadingList || loadingFile}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-xs font-medium text-gray-300 transition-all hover:border-gray-600 hover:text-white disabled:opacity-50"
            >
              <ArrowPathIcon className={`h-4 w-4 ${loadingList || loadingFile ? 'animate-spin' : ''}`} />
              Neu laden
            </button>
            <button
              onClick={() => void handleSave()}
              disabled={!selectedFile?.editable || !dirty || saving}
              className="inline-flex items-center gap-2 rounded-lg border border-kirobi-500/30 bg-kirobi-500/10 px-3 py-2 text-xs font-medium text-kirobi-300 transition-all hover:border-kirobi-400/40 hover:text-white disabled:cursor-not-allowed disabled:border-gray-700 disabled:bg-gray-800 disabled:text-gray-600"
            >
              <PencilSquareIcon className="h-4 w-4" />
              {saving ? 'Speichert...' : 'Speichern'}
            </button>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 p-6 xl:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="card space-y-4">
          <div className="flex items-center gap-2">
            <FolderOpenIcon className="h-5 w-5 text-kirobi-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-300">Dateibaum</h2>
          </div>

          <div className="space-y-2">
            {files.map((file) => {
              const active = file.id === selectedId;
              return (
                <button
                  key={file.id}
                  onClick={() => void loadFile(file.id)}
                  className={`w-full rounded-xl border p-3 text-left transition-all ${
                    active
                      ? 'border-kirobi-500/30 bg-kirobi-500/10'
                      : 'border-gray-700/60 bg-gray-900/50 hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-white">{file.label}</p>
                      <p className="mt-1 text-xs text-gray-500">{file.description}</p>
                    </div>
                    <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${file.editable ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-700 text-gray-400'}`}>
                      {file.editable ? 'edit' : 'read'}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </aside>

        <section className="space-y-6">
          {error && (
            <div className="card border border-red-500/30 bg-red-500/5">
              <div className="flex items-start gap-3">
                <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0 text-red-400" />
                <p className="whitespace-pre-wrap text-sm text-red-300">{error}</p>
              </div>
            </div>
          )}

          {success && (
            <div className="card border border-emerald-500/30 bg-emerald-500/5">
              <div className="flex items-start gap-3">
                <CheckCircleIcon className="h-5 w-5 flex-shrink-0 text-emerald-400" />
                <p className="text-sm text-emerald-300">{success}</p>
              </div>
            </div>
          )}

          <div className="card space-y-4">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <h2 className="text-lg font-semibold text-white">{selectedFile?.label ?? 'Datei auswählen'}</h2>
                <p className="mt-1 text-xs font-mono text-gray-500">{selectedFile?.path ?? 'Keine Datei geladen'}</p>
              </div>
              {selectedFile && (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${selectedFile.editable ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-700 text-gray-400'}`}>
                    {selectedFile.editable ? 'Editierbar' : 'Nur Ansicht'}
                  </span>
                  {selectedFile.obfuscated && (
                    <span className="rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-400">
                      Werte maskiert
                    </span>
                  )}
                </div>
              )}
            </div>

            {selectedFile?.warning && (
              <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-sm text-amber-300">
                {selectedFile.warning}
              </div>
            )}

            {loadingFile ? (
              <div className="rounded-xl border border-gray-700/60 bg-gray-900/60 p-6 text-sm text-gray-500">Datei wird geladen ...</div>
            ) : selectedFile && !selectedFile.exists ? (
              <div className="rounded-xl border border-gray-700/60 bg-gray-900/60 p-6 text-sm text-gray-500">
                Diese Datei existiert aktuell nicht auf dem Dateisystem.
              </div>
            ) : selectedFile?.editable ? (
              <textarea
                value={draftContent}
                onChange={(event) => setDraftContent(event.target.value)}
                spellCheck={false}
                className="min-h-[28rem] w-full rounded-xl border border-gray-700/60 bg-gray-950/80 p-4 font-mono text-sm text-gray-100 focus:border-kirobi-500/40 focus:outline-none"
              />
            ) : (
              <pre className="max-h-[40rem] overflow-auto whitespace-pre-wrap rounded-xl border border-gray-700/60 bg-gray-950/80 p-4 font-mono text-sm text-gray-100">
                {draftContent || 'Keine Daten verfügbar.'}
              </pre>
            )}
          </div>

          <div className="card space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-300">Diff / Vorschau</h2>
                <p className="mt-1 text-xs text-gray-500">Vor dem Speichern werden alle geänderten Zeilen gegenüber dem Original gezeigt.</p>
              </div>
              <span className="rounded-full border border-gray-700/60 bg-gray-900/60 px-3 py-1 text-xs font-mono text-gray-400">
                {diffPreview.length} Änderungen
              </span>
            </div>

            {!dirty ? (
              <div className="rounded-xl border border-gray-700/60 bg-gray-900/60 p-4 text-sm text-gray-500">
                Keine ungespeicherten Änderungen vorhanden.
              </div>
            ) : (
              <div className="space-y-3">
                {diffPreview.slice(0, 80).map((line) => (
                  <div key={`${line.lineNumber}-${line.original}-${line.updated}`} className="grid gap-3 rounded-xl border border-gray-700/60 bg-gray-900/60 p-3 lg:grid-cols-2">
                    <div>
                      <p className="mb-2 text-[11px] uppercase tracking-wider text-red-300">Vorher · Zeile {line.lineNumber}</p>
                      <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-red-500/5 p-3 font-mono text-xs text-red-100">{line.original || '∅'}</pre>
                    </div>
                    <div>
                      <p className="mb-2 text-[11px] uppercase tracking-wider text-emerald-300">Nachher · Zeile {line.lineNumber}</p>
                      <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-emerald-500/5 p-3 font-mono text-xs text-emerald-100">{line.updated || '∅'}</pre>
                    </div>
                  </div>
                ))}
                {diffPreview.length > 80 && (
                  <div className="rounded-xl border border-gray-700/60 bg-gray-900/60 px-4 py-3 text-xs text-gray-500">
                    Weitere {diffPreview.length - 80} Änderungen werden aus Platzgründen nicht angezeigt.
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="card flex items-start gap-3 text-sm text-gray-400">
            <ShieldCheckIcon className="h-5 w-5 flex-shrink-0 text-kirobi-400" />
            <p>
              Nur allowlistete Dateien sind sichtbar. <code className="font-mono text-gray-300">.env</code> wird ausschließlich maskiert angezeigt, um Tokens und Passwörter nicht offenzulegen.
            </p>
          </div>
        </section>
      </div>
    </>
  );
}
