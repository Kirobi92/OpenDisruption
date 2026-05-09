'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, useReducedMotion } from 'framer-motion';
import axios from 'axios';

const SPRING = { duration: 0.55, ease: [0.16, 1, 0.3, 1] as const };

export default function LoginPage() {
  const router = useRouter();
  const reduced = useReducedMotion();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) router.push('/control-center');
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await axios.post('/api/auth/login', { username, password });
      const { access_token, refresh_token } = response.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      router.push('/control-center');
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? 'Login fehlgeschlagen. Bitte versuche es erneut.');
      } else {
        setError('Login fehlgeschlagen. Bitte versuche es erneut.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-void">
      <div className="ambient-field" aria-hidden="true" />

      {/* Aurora orbit (decorative, paint-only) */}
      <div className="pointer-events-none absolute inset-0 z-0 flex items-center justify-center">
        <motion.div
          aria-hidden
          initial={reduced ? false : { opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.4, ease: [0.16, 1, 0.3, 1] }}
          className="relative h-[640px] w-[640px] max-w-[90vw] max-h-[90vw]"
        >
          <div className="absolute inset-0 rounded-full blur-3xl opacity-50"
               style={{ background: 'radial-gradient(circle, rgba(94,234,212,0.35), transparent 60%)' }} />
          <div className="absolute inset-12 rounded-full blur-2xl opacity-40"
               style={{ background: 'radial-gradient(circle, rgba(232,121,249,0.28), transparent 65%)' }} />
          {!reduced && (
            <div className="absolute inset-24 rounded-full border border-aurora-cyan/20 animate-orbit-slow" />
          )}
        </motion.div>
      </div>

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-10">
        <motion.div
          initial={reduced ? false : { opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={SPRING}
          className="w-full max-w-md space-y-7"
        >
          {/* Brand */}
          <div className="text-center">
            <motion.div
              initial={reduced ? false : { opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ ...SPRING, delay: 0.05 }}
              className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl glass-raised"
            >
              <span className="text-2xl font-bold text-gradient-aurora tracking-display">K</span>
            </motion.div>
            <h1 className="text-4xl font-semibold tracking-display text-balance">
              <span className="text-gradient-aurora">Kirobi</span>
            </h1>
            <p className="mt-2 text-sm text-[color:var(--text-secondary)]">
              Willkommen zurück. Lokale Intelligenz, sichere Räume.
            </p>
          </div>

          {/* Card */}
          <motion.form
            onSubmit={handleLogin}
            initial={reduced ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...SPRING, delay: 0.1 }}
            className="glass-raised rounded-3xl p-7 space-y-5"
          >
            {error && (
              <motion.div
                initial={reduced ? false : { opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25 }}
                className="rounded-xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
                role="alert"
              >
                {error}
              </motion.div>
            )}

            <div className="space-y-4">
              <Field
                id="username"
                label="Benutzername"
                value={username}
                onChange={setUsername}
                placeholder="sven, samira oder sineo"
                type="text"
                autoComplete="username"
              />
              <Field
                id="password"
                label="Passwort"
                value={password}
                onChange={setPassword}
                placeholder="••••••••"
                type="password"
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="group relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-2xl px-4 py-3.5 text-sm font-semibold text-[color:var(--bg-void)] transition-all duration-300 ease-spring disabled:cursor-not-allowed disabled:opacity-60"
              style={{ background: 'linear-gradient(110deg, #5eead4 0%, #a78bfa 50%, #e879f9 100%)' }}
            >
              <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/30 to-transparent transition-transform duration-700 group-hover:translate-x-full" />
              <span className="relative">{loading ? 'Anmelden…' : 'Anmelden'}</span>
              {!loading && (
                <svg className="relative h-4 w-4 transition-transform group-hover:translate-x-0.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
                  <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
                </svg>
              )}
            </button>

            <p className="text-center text-xs text-[color:var(--text-muted)]">
              Erstmaliges Einloggen? Standard-Passwort verwenden und dann ändern.
            </p>
          </motion.form>

          {/* Footer */}
          <motion.div
            initial={reduced ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ ...SPRING, delay: 0.25 }}
            className="flex items-center justify-center gap-2 text-xs uppercase tracking-[0.22em] text-[color:var(--text-muted)]"
          >
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-aurora-cyan animate-breathe" />
            Lokal · Privat · Souverän
          </motion.div>
        </motion.div>
      </div>
    </main>
  );
}

function Field({
  id, label, value, onChange, placeholder, type, autoComplete,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  type: 'text' | 'password';
  autoComplete: string;
}) {
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--text-secondary)]">
        {label}
      </label>
      <div className="group relative">
        <input
          id={id}
          name={id}
          type={type}
          required
          autoComplete={autoComplete}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full rounded-xl border border-[color:var(--border-soft)] bg-[color:var(--bg-deep)]/70 px-4 py-3 text-[color:var(--text-primary)] placeholder:text-[color:var(--text-muted)] outline-none transition-all duration-300 ease-spring focus:border-[color:var(--accent-cyan)] focus:bg-[color:var(--bg-deep)] focus:shadow-glow-cyan"
        />
        <span className="pointer-events-none absolute inset-x-3 -bottom-px h-px scale-x-0 bg-gradient-to-r from-transparent via-aurora-cyan to-transparent transition-transform duration-500 group-focus-within:scale-x-100" />
      </div>
    </div>
  );
}
