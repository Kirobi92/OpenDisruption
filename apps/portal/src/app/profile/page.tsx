'use client';

import { motion } from 'framer-motion';
import { Check, CloudUpload, Download, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';

import { BottomNav } from '@/components/layout/BottomNav';
import { Header } from '@/components/layout/Header';
import { useAuth, useRequireAuth } from '@/lib/auth';
import { uploadFile } from '@/lib/api';

const focusAreas = ['Technologie', 'Musik', 'Kreativität', 'Business', 'Familie', 'Lernen', 'Sport', 'Kunst', 'Reisen', 'Kochen'];
const communicationOptions = ['Professionell', 'Locker & Freundlich', 'Kreativ', 'Direkt & Präzise'] as const;
const avatarClasses = ['from-kirobi-400 to-aurora-cyan', 'from-aurora-magenta to-aurora-violet', 'from-aurora-violet to-purple-600'] as const;
const providers = [
  { id: 'chatgpt', name: 'ChatGPT', logo: '⚡', accept: '.json' },
  { id: 'perplexity', name: 'Perplexity', logo: '🔍', accept: '.json' },
  { id: 'gemini', name: 'Gemini', logo: '✨', accept: '.zip' },
  { id: 'deepseek', name: 'DeepSeek', logo: '🌊', accept: '.json' },
] as const;

type ProviderId = (typeof providers)[number]['id'];

type ImportState = {
  file?: File;
  message: string;
};

export default function ProfilePage() {
  const { user } = useAuth();
  const { isLoading, isAuthenticated } = useRequireAuth();
  const [avatarIndex, setAvatarIndex] = useState(0);
  const [displayName, setDisplayName] = useState(user?.displayName ?? '');
  const [email, setEmail] = useState('');
  const [bio, setBio] = useState('');
  const [communicationStyle, setCommunicationStyle] = useState<(typeof communicationOptions)[number]>('Locker & Freundlich');
  const [language, setLanguage] = useState<'DE' | 'EN'>('DE');
  const [selectedFocusAreas, setSelectedFocusAreas] = useState<string[]>(['Technologie', 'Kreativität']);
  const [memorySettings, setMemorySettings] = useState({
    goals: true,
    preferences: true,
    communication: true,
    importantDates: false,
    projectProgress: true,
  });
  const [importStates, setImportStates] = useState<Record<ProviderId, ImportState>>({
    chatgpt: { message: 'Noch keine Datei ausgewählt' },
    perplexity: { message: 'Noch keine Datei ausgewählt' },
    gemini: { message: 'Noch keine Datei ausgewählt' },
    deepseek: { message: 'Noch keine Datei ausgewählt' },
  });
  const [isImporting, setIsImporting] = useState(false);
  const [toastVisible, setToastVisible] = useState(false);

  const inputRefs = {
    chatgpt: useRef<HTMLInputElement | null>(null),
    perplexity: useRef<HTMLInputElement | null>(null),
    gemini: useRef<HTMLInputElement | null>(null),
    deepseek: useRef<HTMLInputElement | null>(null),
  };

  useEffect(() => {
    const stored = window.localStorage.getItem('kirobi.portal.profile');
    if (!stored) {
      return;
    }

    const parsed = JSON.parse(stored) as {
      avatarIndex?: number;
      displayName?: string;
      email?: string;
      bio?: string;
      communicationStyle?: (typeof communicationOptions)[number];
      language?: 'DE' | 'EN';
      selectedFocusAreas?: string[];
      memorySettings?: typeof memorySettings;
    };

    setAvatarIndex(parsed.avatarIndex ?? 0);
    setDisplayName(parsed.displayName ?? user?.displayName ?? '');
    setEmail(parsed.email ?? '');
    setBio(parsed.bio ?? '');
    setCommunicationStyle(parsed.communicationStyle ?? 'Locker & Freundlich');
    setLanguage(parsed.language ?? 'DE');
    setSelectedFocusAreas(parsed.selectedFocusAreas ?? ['Technologie', 'Kreativität']);
    setMemorySettings(parsed.memorySettings ?? memorySettings);
  }, [user?.displayName]);

  useEffect(() => {
    if (!user?.displayName && !displayName) {
      return;
    }
    setDisplayName((current) => current || user?.displayName || '');
  }, [displayName, user?.displayName]);

  const initials = useMemo(() => (displayName || user?.displayName || 'KI').slice(0, 2).toUpperCase(), [displayName, user?.displayName]);

  const toggleFocusArea = (area: string) => {
    setSelectedFocusAreas((current) =>
      current.includes(area) ? current.filter((item) => item !== area) : [...current, area],
    );
  };

  const handleFileSelection = async (provider: ProviderId, file: File) => {
    if (provider === 'gemini') {
      setImportStates((current) => ({
        ...current,
        [provider]: { file, message: 'Takeout erkannt – Import bereit.' },
      }));
      return;
    }

    try {
      const parsed = JSON.parse(await file.text()) as unknown;
      const total = Array.isArray(parsed)
        ? parsed.length
        : typeof parsed === 'object' && parsed !== null
          ? Array.isArray((parsed as Record<string, unknown>).conversations)
            ? ((parsed as Record<string, unknown>).conversations as unknown[]).length
            : Array.isArray((parsed as Record<string, unknown>).data)
              ? ((parsed as Record<string, unknown>).data as unknown[]).length
              : Object.keys(parsed as Record<string, unknown>).length
          : 0;

      setImportStates((current) => ({
        ...current,
        [provider]: {
          file,
          message: `${total} Gespräche gefunden`,
        },
      }));
    } catch {
      setImportStates((current) => ({
        ...current,
        [provider]: {
          file,
          message: 'Datei erkannt – bereit für den Import.',
        },
      }));
    }
  };

  const handleImport = async () => {
    setIsImporting(true);
    try {
      const selected = Object.entries(importStates).filter(([, state]) => state.file) as Array<[ProviderId, ImportState]>;
      for (const [, state] of selected) {
        if (state.file) {
          await uploadFile(state.file, 'WORKSPACE');
        }
      }
      setToastVisible(true);
      window.setTimeout(() => setToastVisible(false), 2400);
    } finally {
      setIsImporting(false);
    }
  };

  const handleSave = () => {
    window.localStorage.setItem(
      'kirobi.portal.profile',
      JSON.stringify({
        avatarIndex,
        displayName,
        email,
        bio,
        communicationStyle,
        language,
        selectedFocusAreas,
        memorySettings,
      }),
    );
    setToastVisible(true);
    window.setTimeout(() => setToastVisible(false), 2400);
  };

  if (isLoading || !isAuthenticated) {
    return <div className="min-h-screen bg-void" />;
  }

  return (
    <div className="min-h-screen pb-24 md:pb-8">
      <Header title="Profil" />
      <main className="mx-auto max-w-7xl px-4 pb-10 pt-20 md:px-6">
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="glass rounded-[2rem] p-6 shadow-card">
            <div className="flex flex-col items-center text-center">
              <button
                type="button"
                onClick={() => setAvatarIndex((current) => (current + 1) % avatarClasses.length)}
                className={`inline-flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br text-3xl font-semibold text-white shadow-glow-cyan ${avatarClasses[avatarIndex]}`}
              >
                {initials}
              </button>
              <button type="button" onClick={() => setAvatarIndex((current) => (current + 1) % avatarClasses.length)} className="mt-4 text-sm text-aurora-cyan">
                Farbe wechseln
              </button>
            </div>

            <div className="mt-8 space-y-4">
              <div>
                <label className="mb-2 block text-sm text-white/70">Display Name</label>
                <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 px-4 outline-none" />
              </div>
              <div>
                <label className="mb-2 block text-sm text-white/70">Username</label>
                <input value={user?.username ?? ''} readOnly className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-white/45 outline-none" />
              </div>
              <div>
                <label className="mb-2 block text-sm text-white/70">E-Mail</label>
                <input value={email} onChange={(event) => setEmail(event.target.value)} className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 px-4 outline-none" />
              </div>
              <div>
                <label className="mb-2 block text-sm text-white/70">Bio</label>
                <textarea value={bio} onChange={(event) => setBio(event.target.value)} className="min-h-[140px] w-full rounded-3xl border border-white/10 bg-white/5 px-4 py-3 outline-none" />
              </div>
            </div>
          </div>

          <div className="grid gap-6">
            <div className="glass rounded-[2rem] p-6 shadow-card">
              <h2 className="text-2xl font-semibold">AI Preferences</h2>
              <div className="mt-6 space-y-6">
                <div>
                  <div className="mb-3 text-sm font-medium text-white/80">Kommunikationsstil</div>
                  <div className="grid gap-3 md:grid-cols-2">
                    {communicationOptions.map((option) => (
                      <label key={option} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/70">
                        <input type="radio" name="communicationStyle" checked={communicationStyle === option} onChange={() => setCommunicationStyle(option)} />
                        {option}
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="mb-3 text-sm font-medium text-white/80">Antwortsprache</div>
                  <div className="flex gap-3">
                    {(['DE', 'EN'] as const).map((entry) => (
                      <button
                        key={entry}
                        type="button"
                        onClick={() => setLanguage(entry)}
                        className={`rounded-full px-4 py-2 text-sm transition ${
                          language === entry
                            ? 'bg-aurora-cyan/20 text-aurora-cyan shadow-glow-cyan'
                            : 'border border-white/10 bg-white/5 text-white/65'
                        }`}
                      >
                        {entry}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="mb-3 text-sm font-medium text-white/80">Fokusbereiche</div>
                  <div className="flex flex-wrap gap-3">
                    {focusAreas.map((area) => (
                      <button
                        key={area}
                        type="button"
                        onClick={() => toggleFocusArea(area)}
                        className={`rounded-full px-4 py-2 text-sm transition ${
                          selectedFocusAreas.includes(area)
                            ? 'bg-aurora-magenta/20 text-aurora-magenta shadow-glow-magenta'
                            : 'border border-white/10 bg-white/5 text-white/65'
                        }`}
                      >
                        {area}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="glass rounded-[2rem] p-6 shadow-card">
              <h2 className="text-2xl font-semibold">Memory Settings</h2>
              <div className="mt-5 space-y-3">
                {[
                  ['goals', 'Meine Ziele'],
                  ['preferences', 'Meine Vorlieben'],
                  ['communication', 'Meinen Kommunikationsstil'],
                  ['importantDates', 'Wichtige Daten'],
                  ['projectProgress', 'Projektfortschritte'],
                ].map(([key, label]) => (
                  <label key={key} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/70">
                    <span>{label}</span>
                    <input
                      type="checkbox"
                      checked={Boolean(memorySettings[key as keyof typeof memorySettings])}
                      onChange={() =>
                        setMemorySettings((current) => ({
                          ...current,
                          [key]: !current[key as keyof typeof current],
                        }))
                      }
                    />
                  </label>
                ))}
              </div>
            </div>
          </div>
        </motion.section>

        <section className="mt-8 glass rounded-[2rem] p-6 shadow-card">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-2xl font-semibold">Chat Import</h2>
              <p className="mt-2 text-white/60">Importiere bestehende Gespräche aus deinen Lieblings-Tools in Kirobi.</p>
            </div>
            <button
              type="button"
              onClick={() => void handleImport()}
              disabled={isImporting}
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet px-5 py-2.5 font-semibold text-void shadow-glow-cyan disabled:opacity-60"
            >
              {isImporting ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              Import starten
            </button>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {providers.map((provider) => (
              <div
                key={provider.id}
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => {
                  event.preventDefault();
                  const file = event.dataTransfer.files?.[0];
                  if (file) {
                    void handleFileSelection(provider.id, file);
                  }
                }}
                className="rounded-[2rem] border border-dashed border-white/10 bg-white/5 p-5"
              >
                <div className="text-3xl">{provider.logo}</div>
                <div className="mt-4 text-lg font-semibold">{provider.name}</div>
                <p className="mt-2 min-h-[48px] text-sm text-white/55">{importStates[provider.id].message}</p>
                <button
                  type="button"
                  onClick={() => inputRefs[provider.id].current?.click()}
                  className="mt-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/10 px-4 py-2 text-sm text-white/70"
                >
                  <CloudUpload className="h-4 w-4" />
                  Datei wählen
                </button>
                <input
                  ref={inputRefs[provider.id]}
                  type="file"
                  accept={provider.accept}
                  className="hidden"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) {
                      void handleFileSelection(provider.id, file);
                    }
                    event.target.value = '';
                  }}
                />
              </div>
            ))}
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_0.8fr]">
          <div className="glass rounded-[2rem] p-6 shadow-card">
            <h2 className="text-2xl font-semibold">Telegram Status</h2>
            <div className="mt-5 flex items-center gap-3 rounded-3xl border border-white/10 bg-white/5 px-4 py-4 text-sm text-white/70">
              <span className="h-3 w-3 rounded-full bg-amber-400" />
              Disconnected – Verbinde Telegram später über deine Services.
            </div>
          </div>

          <div className="glass rounded-[2rem] p-6 shadow-card">
            <h2 className="text-2xl font-semibold">Speichern</h2>
            <p className="mt-3 text-sm leading-7 text-white/60">
              Sichere deine Präferenzen lokal in diesem Portal, damit Kirobi dich konsistenter begleiten kann.
            </p>
            <button
              type="button"
              onClick={handleSave}
              className="mt-6 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet px-5 py-2.5 font-semibold text-void shadow-glow-cyan"
            >
              <Check className="h-4 w-4" />
              Änderungen speichern
            </button>
          </div>
        </section>
      </main>

      {toastVisible ? (
        <div className="fixed bottom-24 right-4 z-50 rounded-2xl border border-aurora-cyan/20 bg-void-deep/95 px-5 py-3 text-sm text-aurora-cyan shadow-glow-cyan">
          Erfolgreich gespeichert.
        </div>
      ) : null}

      <BottomNav />
    </div>
  );
}
