'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  CloudArrowUpIcon,
  DocumentTextIcon,
  PhotoIcon,
  DocumentIcon,
  TrashIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';

type Zone = 'PUBLIC' | 'WORKSPACE' | 'FAMILY_PRIVATE';

interface UploadedFile {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  zone: Zone;
  created_at: string;
}

interface UploadProgress {
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
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [selectedZone, setSelectedZone] = useState<Zone>('WORKSPACE');
  const [isDragging, setIsDragging] = useState(false);
  const [uploads, setUploads] = useState<UploadProgress[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    loadFiles();
  }, []);

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
    const progressEntry: UploadProgress = {
      filename: file.name,
      progress: 0,
      status: 'uploading',
    };
    setUploads((prev) => [...prev, progressEntry]);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('zone', selectedZone);

    try {
      await getAxios().post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          const percent = event.total
            ? Math.round((event.loaded * 100) / event.total)
            : 0;
          setUploads((prev) =>
            prev.map((u) =>
              u.filename === file.name ? { ...u, progress: percent } : u
            )
          );
        },
      });

      setUploads((prev) =>
        prev.map((u) =>
          u.filename === file.name ? { ...u, progress: 100, status: 'done' } : u
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
          u.filename === file.name ? { ...u, status: 'error', error: msg } : u
        )
      );
    }
  };

  const handleFiles = (fileList: FileList) => {
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

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center space-x-3">
          <button
            onClick={() => router.push('/chat')}
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
            {(Object.keys(ZONE_LABELS) as Zone[]).map((zone) => (
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
            PDF, Bilder, Dokumente — Zone: {ZONE_LABELS[selectedZone]}
          </p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleInputChange}
            className="hidden"
            accept="image/*,application/pdf,.doc,.docx,.txt,.md"
          />
        </section>

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
              {uploads.map((upload, idx) => (
                <div key={idx} className="space-y-1">
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
                  </div>
                  <div className="flex items-center space-x-1 flex-shrink-0">
                    <a
                      href={`/api/uploads/${file.id}/download`}
                      className="p-1.5 text-gray-400 hover:text-white transition-colors"
                      title="Herunterladen"
                    >
                      <ArrowDownTrayIcon className="w-4 h-4" />
                    </a>
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
