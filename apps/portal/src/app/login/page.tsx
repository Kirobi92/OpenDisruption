'use client';

import { motion } from 'framer-motion';
import { ArrowRight, LockKeyhole, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import { useAuth } from '@/lib/auth';

const profiles = [
  {
    username: 'sven',
    emoji: '🌟',
    title: 'Sven',
    subtitle: 'Vision, Systeme, Fokus',
    accent: 'from-kirobi-400 to-aurora-cyan',
  },
  {
    username: 'samira',
    emoji: '💜',
    title: 'Samira',
    subtitle: 'Wärme, Harmonie, Tiefe',
    accent: 'from-aurora-magenta to-aurora-violet',
  },
  {
    username: 'sineo',
    emoji: '🎨',
    title: 'Sineo',
    subtitle: 'Kreativität, Spiel, Ausdruck',
    accent: 'from-aurora-violet to-kirobi-500',
  },
] as const;

export default function LoginPage() {
  const router = useRouter();
  const auth = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!auth.isLoading && auth.token) {
      router.replace('/');
    }
  }, [auth.isLoading, auth.token, router]);

  const selectedProfile = useMemo(
    () => profiles.find((profile) => profile.username === username.toLowerCase()),
    [username],
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!username.trim() || !password.trim()) {
      setError('Bitte gib Benutzername und Passwort ein.');
      return;
    }

    try {
      setError('');
      await auth.login(username.trim(), password);
      router.push('/');
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : 'Anmeldung fehlgeschlagen.');
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-void text-white">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-[-12rem] h-[28rem] w-[28rem] -translate-x-1/2 rounded-full bg-aurora-cyan/15 blur-3xl animate-[float_18s_ease-in-out_infinite]" />
        <div className="absolute right-[-8rem] top-1/3 h-80 w-80 rounded-full bg-aurora-magenta/15 blur-3xl animate-[float_22s_ease-in-out_infinite_reverse]" />
        <div className="absolute bottom-[-10rem] left-[-6rem] h-96 w-96 rounded-full bg-aurora-violet/15 blur-3xl animate-[float_20s_ease-in-out_infinite]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(94,234,212,0.16),transparent_35%),radial-gradient(circle_at_80%_30%,rgba(232,121,249,0.14),transparent_30%),radial-gradient(circle_at_20%_70%,rgba(167,139,250,0.16),transparent_35%)]" />
      </div>

      <div className="relative z-10 mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-4 py-10 md:px-8">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mx-auto w-full max-w-5xl overflow-hidden rounded-[2rem] border border-white/10 bg-white/5 shadow-card backdrop-blur-2xl"
        >
          <div className="grid min-h-[720px] lg:grid-cols-[1.1fr_0.9fr]">
            <section className="relative flex flex-col justify-between overflow-hidden border-b border-white/10 px-6 py-8 md:px-10 lg:border-b-0 lg:border-r">
              <div className="space-y-5">
                <div className="inline-flex items-center gap-2 rounded-full border border-aurora-cyan/20 bg-aurora-cyan/10 px-4 py-2 text-xs font-medium uppercase tracking-[0.24em] text-aurora-cyan">
                  <Sparkles className="h-4 w-4" />
                  Persönlicher KI-Begleiter
                </div>
                <div>
                  <div className="bg-gradient-to-r from-kirobi-200 via-aurora-cyan to-aurora-violet bg-clip-text text-4xl font-black tracking-[0.35em] text-transparent md:text-5xl">
                    KIROBI
                  </div>
                  <p className="mt-4 max-w-xl text-base leading-7 text-white/70 md:text-lg">
                    Willkommen zurück in deinem warmen, futuristischen Raum für Gespräche, Wissen, Ziele und Kreativität.
                  </p>
                </div>
              </div>

              <div className="mt-10 grid gap-4 md:grid-cols-3">
                {profiles.map((profile, index) => {
                  const active = selectedProfile?.username === profile.username;

                  return (
                    <motion.button
                      key={profile.username}
                      type="button"
                      onClick={() => {
                        setUsername(profile.username);
                        setError('');
                      }}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 + index * 0.08 }}
                      className={`group rounded-3xl border p-5 text-left transition ${
                        active
                          ? 'border-aurora-cyan/50 bg-white/10 shadow-glow-cyan'
                          : 'border-white/10 bg-white/5 hover:border-white/25 hover:bg-white/10'
                      }`}
                    >
                      <div className={`inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br text-2xl ${profile.accent}`}>
                        {profile.emoji}
                      </div>
                      <div className="mt-4">
                        <div className="text-lg font-semibold text-white">{profile.title}</div>
                        <div className="mt-1 text-sm text-white/60">{profile.subtitle}</div>
                      </div>
                    </motion.button>
                  );
                })}
              </div>
            </section>

            <section className="flex items-center px-6 py-8 md:px-10">
              <div className="w-full space-y-8">
                <div>
                  <h1 className="text-3xl font-semibold text-white">Schön, dass du da bist</h1>
                  <p className="mt-3 text-sm leading-6 text-white/60">
                    Melde dich an und starte mit Kirobi in deinen persönlichen Flow-Modus.
                  </p>
                </div>

                <form className="space-y-5" onSubmit={handleSubmit}>
                  <div className="space-y-2">
                    <label htmlFor="username" className="text-sm font-medium text-white/80">
                      Benutzername
                    </label>
                    <input
                      id="username"
                      value={username}
                      onChange={(event) => setUsername(event.target.value)}
                      placeholder="sven, samira oder sineo"
                      className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 px-4 text-white outline-none transition placeholder:text-white/30 focus:border-aurora-cyan/40 focus:bg-white/10"
                      autoComplete="username"
                    />
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="password" className="text-sm font-medium text-white/80">
                      Passwort
                    </label>
                    <div className="relative">
                      <LockKeyhole className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                      <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        placeholder="••••••••"
                        className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 pl-11 pr-4 text-white outline-none transition placeholder:text-white/30 focus:border-aurora-cyan/40 focus:bg-white/10"
                        autoComplete="current-password"
                      />
                    </div>
                  </div>

                  {error ? (
                    <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                      {error}
                    </div>
                  ) : null}

                  <button
                    type="submit"
                    disabled={auth.isLoading}
                    className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-kirobi-400 via-aurora-cyan to-aurora-violet font-semibold text-void transition hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {auth.isLoading ? 'Anmeldung läuft...' : 'Portal öffnen'}
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </form>

                <div className="rounded-3xl border border-white/10 bg-white/5 p-5 text-sm leading-6 text-white/60">
                  <div className="font-medium text-white/80">Tipp</div>
                  Wähle einfach deinen Avatar aus, um den Benutzernamen vorzufüllen und schneller in deinen Raum zu gleiten.
                </div>
              </div>
            </section>
          </div>
        </motion.div>
      </div>

      <style jsx>{`
        @keyframes float {
          0%,
          100% {
            transform: translate3d(0, 0, 0) scale(1);
          }
          50% {
            transform: translate3d(0, 18px, 0) scale(1.04);
          }
        }
      `}</style>
    </main>
  );
}
