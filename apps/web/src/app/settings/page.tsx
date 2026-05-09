'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  UserCircleIcon,
  KeyIcon,
  ShieldCheckIcon,
  SunIcon,
  MoonIcon,
  ArrowRightOnRectangleIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';
import { useClientSearchParams } from '@/lib/use-client-search-params';

interface User {
  id: string;
  username: string;
  display_name: string;
  role: string;
}

interface Permission {
  zone: string;
  can_read: boolean;
  can_write: boolean;
}

interface PermissionsResponse {
  user_id: string;
  username: string;
  zones: Permission[];
}

type Theme = 'dark' | 'light';
type SettingsSection = 'profile' | 'appearance' | 'password' | 'permissions' | 'runtime' | 'session';

interface RuntimeProbe {
  id: string;
  label: string;
  path: string;
  status: 'online' | 'offline' | 'unknown';
  detail: string;
}

export default function SettingsPage() {
  const router = useRouter();
  const searchParams = useClientSearchParams();
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [theme, setTheme] = useState<Theme>('dark');
  const [loadingUser, setLoadingUser] = useState(true);
  const [activeSection, setActiveSection] = useState<SettingsSection>('profile');
  const [runtime, setRuntime] = useState<RuntimeProbe[]>([
    { id: 'auth', label: 'Auth', path: '/api/auth/health', status: 'unknown', detail: 'wird geprüft' },
    { id: 'api', label: 'API', path: '/api/health', status: 'unknown', detail: 'wird geprüft' },
    { id: 'telegram', label: 'Telegram', path: '/telegram/health', status: 'unknown', detail: 'wird geprüft' },
    { id: 'voice', label: 'Voice', path: '/voice/health', status: 'unknown', detail: 'wird geprüft' },
  ]);

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwLoading, setPwLoading] = useState(false);
  const [pwSuccess, setPwSuccess] = useState('');
  const [pwError, setPwError] = useState('');

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

    const savedTheme = (localStorage.getItem('theme') as Theme) ?? 'dark';
    setTheme(savedTheme);
    applyTheme(savedTheme);

    loadUser();
    loadPermissions();
  }, []);

  useEffect(() => {
    const sectionParam = searchParams.get('section');
    if (
      sectionParam === 'profile' ||
      sectionParam === 'appearance' ||
      sectionParam === 'password' ||
      sectionParam === 'permissions' ||
      sectionParam === 'runtime' ||
      sectionParam === 'session'
    ) {
      setActiveSection(sectionParam);
    }
  }, [searchParams]);

  useEffect(() => {
    void Promise.all(
      runtime.map(async (entry) => {
        try {
          const response = await fetch(entry.path, { cache: 'no-store' });
          return {
            ...entry,
            status: response.ok ? 'online' as const : 'offline' as const,
            detail: `HTTP ${response.status}`,
          };
        } catch (error: unknown) {
          return {
            ...entry,
            status: 'offline' as const,
            detail: error instanceof Error ? error.message : 'unreachable',
          };
        }
      })
    ).then((entries) => setRuntime(entries));
  }, []);

  const applyTheme = (t: Theme) => {
    if (t === 'light') {
      document.documentElement.classList.remove('dark');
    } else {
      document.documentElement.classList.add('dark');
    }
  };

  const toggleTheme = () => {
    const next: Theme = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
    applyTheme(next);
  };

  const loadUser = async () => {
    try {
      const response = await getAxios().get<User>('/auth/me');
      setUser(response.data);
    } catch {
      router.push('/');
    } finally {
      setLoadingUser(false);
    }
  };

  const loadPermissions = async () => {
    try {
      const response = await getAxios().get<PermissionsResponse>('/auth/me/permissions');
      setPermissions(response.data.zones ?? []);
    } catch {
      // Permissions endpoint may not exist yet — silently ignore
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwError('');
    setPwSuccess('');

    if (newPassword !== confirmPassword) {
      setPwError('Die neuen Passwörter stimmen nicht überein.');
      return;
    }
    if (newPassword.length < 8) {
      setPwError('Das neue Passwort muss mindestens 8 Zeichen lang sein.');
      return;
    }

    setPwLoading(true);
    try {
      await getAxios().post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwSuccess('Passwort erfolgreich geändert.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setPwError(err.response?.data?.detail ?? 'Passwort konnte nicht geändert werden.');
      } else {
        setPwError('Unbekannter Fehler.');
      }
    } finally {
      setPwLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/');
  };

  const zoneColors: Record<string, string> = {
    PUBLIC: 'bg-green-500/20 text-green-400 border-green-500/30',
    WORKSPACE: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    FAMILY_PRIVATE: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    QUARANTINE: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    SACRED: 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  const zoneLabels: Record<string, string> = {
    PUBLIC: '🌍 Public',
    WORKSPACE: '💼 Workspace',
    FAMILY_PRIVATE: '👨‍👩‍👦 Family Private',
    QUARANTINE: '⚠️ Quarantine',
    SACRED: '🔐 Sacred',
  };

  if (loadingUser) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-white">Laden...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => router.push('/control-center')}
              className="text-gray-400 hover:text-white transition-colors text-sm"
            >
              ← Zurück
            </button>
            <h1 className="text-xl font-bold">Einstellungen</h1>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center space-x-2 px-3 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors text-sm"
          >
            <ArrowRightOnRectangleIcon className="w-4 h-4" />
            <span>Abmelden</span>
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        <section className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <div className="flex flex-wrap gap-2">
            {[
              ['profile', 'Profil'],
              ['appearance', 'Design'],
              ['password', 'Passwort'],
              ['permissions', 'Zonen'],
              ['runtime', 'Runtime'],
              ['session', 'Sitzung'],
            ].map(([id, label]) => (
              <button
                key={id}
                onClick={() => setActiveSection(id as SettingsSection)}
                className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                  activeSection === id
                    ? 'border-kirobi-500/30 bg-kirobi-500/10 text-kirobi-100'
                    : 'border-gray-600 bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </section>

        {/* User Info */}
        {activeSection === 'profile' && (
        <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center space-x-4">
            <UserCircleIcon className="w-16 h-16 text-kirobi-500 flex-shrink-0" />
            <div>
              <h2 className="text-xl font-semibold">{user?.display_name}</h2>
              <p className="text-gray-400">@{user?.username}</p>
              <span className="inline-block mt-1 px-2 py-0.5 bg-kirobi-600/30 text-kirobi-400 text-xs rounded-full border border-kirobi-500/30">
                {user?.role}
              </span>
            </div>
          </div>
        </section>
        )}

        {/* Theme Toggle */}
        {activeSection === 'appearance' && (
        <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center space-x-3 mb-4">
            {theme === 'dark' ? (
              <MoonIcon className="w-5 h-5 text-kirobi-400" />
            ) : (
              <SunIcon className="w-5 h-5 text-yellow-400" />
            )}
            <h2 className="text-lg font-semibold">Erscheinungsbild</h2>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-300">
              {theme === 'dark' ? 'Dunkles Design' : 'Helles Design'}
            </span>
            <button
              onClick={toggleTheme}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-kirobi-500 focus:ring-offset-2 focus:ring-offset-gray-800 ${
                theme === 'dark' ? 'bg-kirobi-600' : 'bg-gray-600'
              }`}
              role="switch"
              aria-checked={theme === 'dark'}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  theme === 'dark' ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </section>
        )}

        {/* Change Password */}
        {activeSection === 'password' && (
        <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center space-x-3 mb-4">
            <KeyIcon className="w-5 h-5 text-kirobi-400" />
            <h2 className="text-lg font-semibold">Passwort ändern</h2>
          </div>

          {pwSuccess && (
            <div className="flex items-center space-x-2 bg-green-500/10 border border-green-500/30 text-green-400 px-4 py-3 rounded-lg mb-4">
              <CheckCircleIcon className="w-5 h-5 flex-shrink-0" />
              <span>{pwSuccess}</span>
            </div>
          )}
          {pwError && (
            <div className="flex items-center space-x-2 bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg mb-4">
              <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
              <span>{pwError}</span>
            </div>
          )}

          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Aktuelles Passwort
              </label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-kirobi-500"
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Neues Passwort
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-kirobi-500"
                placeholder="Mindestens 8 Zeichen"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Neues Passwort bestätigen
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-kirobi-500"
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit"
              disabled={pwLoading}
              className="w-full py-2.5 bg-kirobi-600 hover:bg-kirobi-700 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {pwLoading ? 'Wird gespeichert...' : 'Passwort speichern'}
            </button>
          </form>
        </section>
        )}

        {/* Zone Permissions */}
        {activeSection === 'permissions' && (
        <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center space-x-3 mb-4">
            <ShieldCheckIcon className="w-5 h-5 text-kirobi-400" />
            <h2 className="text-lg font-semibold">Zonen-Berechtigungen</h2>
          </div>

          <div className="mb-4 rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-200">
            SACRED und QUARANTINE bleiben im MVP bewusst geschützt und tauchen nur dann auf,
            wenn dein Konto dafür explizit lokale Rechte hat.
          </div>

          {permissions.length === 0 ? (
            <p className="text-gray-400 text-sm">
              Berechtigungen werden geladen oder sind nicht verfügbar.
            </p>
          ) : (
            <div className="space-y-2">
              {permissions.map((perm) => (
                <div
                  key={perm.zone}
                  className={`flex items-center justify-between px-4 py-3 rounded-lg border ${
                    zoneColors[perm.zone] ?? 'bg-gray-700/50 text-gray-300 border-gray-600'
                  }`}
                >
                  <span className="font-medium text-sm">
                    {zoneLabels[perm.zone] ?? perm.zone}
                  </span>
                  <div className="flex space-x-3 text-xs">
                    <span className={perm.can_read ? 'opacity-100' : 'opacity-30'}>
                      {perm.can_read ? '✓' : '✗'} Lesen
                    </span>
                    <span className={perm.can_write ? 'opacity-100' : 'opacity-30'}>
                      {perm.can_write ? '✓' : '✗'} Schreiben
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
        )}

        {activeSection === 'runtime' && (
        <section className="space-y-6">
          <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="mb-4">
              <h2 className="text-lg font-semibold">Verknüpfte Laufzeit</h2>
              <p className="mt-1 text-sm text-gray-400">
                Diese Karten zeigen echte, angebundene Runtime-Signale statt statischer Deko.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {runtime.map((entry) => (
                <div key={entry.id} className="rounded-xl border border-gray-600 bg-gray-900/60 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-white">{entry.label}</p>
                      <p className="mt-1 text-xs text-gray-500">{entry.path}</p>
                    </div>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      entry.status === 'online'
                        ? 'bg-emerald-500/10 text-emerald-300'
                        : entry.status === 'offline'
                        ? 'bg-red-500/10 text-red-300'
                        : 'bg-amber-500/10 text-amber-200'
                    }`}>
                      {entry.status}
                    </span>
                  </div>
                  <p className="mt-3 text-sm text-gray-400">{entry.detail}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="mb-4">
              <h2 className="text-lg font-semibold">Direkte Kontrollpfade</h2>
              <p className="mt-1 text-sm text-gray-400">
                Einstellungen bleiben mit echten Oberflächen verbunden: Ops, Workbench und Remote-Zugriff.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <Link href="/control-center" className="rounded-xl border border-gray-600 bg-gray-900/60 p-4 transition-colors hover:border-kirobi-500/40">
                <p className="text-sm font-semibold text-white">Control Center</p>
                <p className="mt-1 text-sm text-gray-400">Agentische Empfehlungen, Signale und zentrale Oberflächen.</p>
              </Link>
              <Link href="/dashboard/services" className="rounded-xl border border-gray-600 bg-gray-900/60 p-4 transition-colors hover:border-kirobi-500/40">
                <p className="text-sm font-semibold text-white">Service Matrix</p>
                <p className="mt-1 text-sm text-gray-400">Live-Status, Ports und Health-Probes aller Dienste.</p>
              </Link>
              <Link href="/workbench?surface=open-webui" className="rounded-xl border border-gray-600 bg-gray-900/60 p-4 transition-colors hover:border-kirobi-500/40">
                <p className="text-sm font-semibold text-white">Embedded Workbench</p>
                <p className="mt-1 text-sm text-gray-400">Open WebUI, Flowise und Qdrant innerhalb der Shell öffnen.</p>
              </Link>
              <Link href="/status" className="rounded-xl border border-gray-600 bg-gray-900/60 p-4 transition-colors hover:border-kirobi-500/40">
                <p className="text-sm font-semibold text-white">Remote / Edge Status</p>
                <p className="mt-1 text-sm text-gray-400">Caddy-, LAN- und Tailscale-nahe Einstiegspfade im Überblick.</p>
              </Link>
            </div>
          </section>
        </section>
        )}

        {/* Logout */}
        {activeSection === 'session' && (
        <section className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center space-x-2 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-medium transition-colors"
          >
            <ArrowRightOnRectangleIcon className="w-5 h-5" />
            <span>Abmelden</span>
          </button>
        </section>
        )}
      </main>
    </div>
  );
}
