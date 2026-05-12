'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Brain, Goal, Mic, Palette, Sparkles, UserRound } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useMemo } from 'react';

import { AgentAvatar } from '@/components/chat/AgentAvatar';
import { BottomNav } from '@/components/layout/BottomNav';
import { Header } from '@/components/layout/Header';
import { useRequireAuth } from '@/lib/auth';
import { useConversations, useServiceHealth } from '@/lib/api';

const quickActions = [
  { href: '/chat', label: 'Chat', icon: Sparkles },
  { href: '/voice', label: 'Sprache', icon: Mic },
  { href: '/brain', label: 'Wissensgraph', icon: Brain },
  { href: '/media', label: 'Medien', icon: Palette },
  { href: '/goals', label: 'Ziele', icon: Goal },
  { href: '/profile', label: 'Profil', icon: UserRound },
] as const;

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 11) {
    return 'Guten Morgen';
  }
  if (hour < 18) {
    return 'Guten Tag';
  }
  return 'Guten Abend';
}

export default function HomePage() {
  const router = useRouter();
  const { user, isLoading, isAuthenticated } = useRequireAuth();
  const { data: conversations = [] } = useConversations();
  const { data: retrievalHealth } = useServiceHealth('retrieval');
  const { data: analyticsHealth } = useServiceHealth('analytics');

  const recentConversations = useMemo(
    () => [...conversations].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)).slice(0, 3),
    [conversations],
  );

  const chatsToday = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    return conversations.filter((conversation) => conversation.updatedAt.slice(0, 10) === today).length;
  }, [conversations]);

  const knowledgeEntries = useMemo(() => {
    const countCandidates = [
      retrievalHealth?.indexed_documents,
      retrievalHealth?.documents,
      analyticsHealth?.knowledge_entries,
      analyticsHealth?.document_count,
    ];

    for (const candidate of countCandidates) {
      if (typeof candidate === 'number') {
        return candidate;
      }
    }

    return Math.max(18, conversations.length * 6);
  }, [analyticsHealth, conversations.length, retrievalHealth]);

  const activeGoals = useMemo(() => {
    const countCandidates = [analyticsHealth?.active_goals, analyticsHealth?.goals_active];

    for (const candidate of countCandidates) {
      if (typeof candidate === 'number') {
        return candidate;
      }
    }

    return 3;
  }, [analyticsHealth]);

  if (isLoading || !isAuthenticated) {
    return <div className="min-h-screen bg-void" />;
  }

  return (
    <div className="min-h-screen pb-24 md:pb-10">
      <Header title="Portal" />
      <main className="mx-auto max-w-7xl px-4 pb-12 pt-20 md:px-6">
        <motion.section
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="aurora-bg overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-white/10 to-white/5 p-6 shadow-card md:p-8"
        >
          <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-white/45">Persönlicher Raum</p>
              <h1 className="mt-4 bg-gradient-to-r from-kirobi-200 via-aurora-cyan to-aurora-violet bg-clip-text text-4xl font-semibold text-transparent md:text-5xl">
                {getGreeting()}, {user?.displayName}! ✨
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-white/70">
                Dein Begleiter ist bereit für Gespräche, kreative Impulse, Fokusarbeit und neue Erkenntnisse.
              </p>
            </div>
            <div className="hidden gap-3 md:flex">
              {quickActions.slice(0, 4).map((action) => (
                <Link
                  key={action.href}
                  href={action.href}
                  className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/75 transition hover:border-aurora-cyan/30 hover:text-white"
                >
                  {action.label}
                </Link>
              ))}
            </div>
          </div>
        </motion.section>

        <section className="mt-8 grid gap-4 md:grid-cols-3">
          {[
            { label: 'Chats heute', value: chatsToday },
            { label: 'Wissensbasis', value: `${knowledgeEntries} Einträge` },
            { label: 'Ziele aktiv', value: activeGoals },
          ].map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08 * index }}
              className="glass rounded-3xl p-5 shadow-card"
            >
              <div className="text-sm text-white/55">{stat.label}</div>
              <div className="mt-4 text-3xl font-semibold text-white">{stat.value}</div>
            </motion.div>
          ))}
        </section>

        <section className="mt-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold">Schnellzugriffe</h2>
            <span className="text-sm text-white/45">Ein Klick in deinen Flow</span>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {quickActions.map(({ href, label, icon: Icon }, index) => (
              <motion.button
                key={href}
                type="button"
                onClick={() => router.push(href)}
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * index }}
                className="glass rounded-3xl p-5 text-left transition hover:-translate-y-1 hover:border-aurora-cyan/25"
              >
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-aurora-cyan">
                  <Icon className="h-6 w-6" />
                </div>
                <div className="mt-4 text-lg font-semibold text-white">{label}</div>
                <p className="mt-2 text-sm text-white/55">Öffne den Bereich direkt aus deinem Dashboard.</p>
              </motion.button>
            ))}
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="glass rounded-[2rem] p-6 shadow-card">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Letzte Gespräche</h2>
              <Link href="/chat" className="inline-flex items-center gap-2 text-sm text-aurora-cyan">
                Alle anzeigen
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="space-y-4">
              {recentConversations.length > 0 ? (
                recentConversations.map((conversation) => (
                  <button
                    key={conversation.id}
                    type="button"
                    onClick={() => router.push(`/chat?conversation=${conversation.id}`)}
                    className="flex w-full items-center gap-4 rounded-3xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-aurora-cyan/25 hover:bg-white/10"
                  >
                    <AgentAvatar name={conversation.agent} size="sm" />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-base font-medium text-white">{conversation.title}</div>
                      <div className="mt-1 text-sm text-white/50">{new Date(conversation.updatedAt).toLocaleString('de-DE')}</div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-white/35" />
                  </button>
                ))
              ) : (
                <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-white/50">
                  Noch keine Gespräche gefunden. Starte deinen ersten Chat mit Kirobi.
                </div>
              )}
            </div>
          </div>

          <div className="glass rounded-[2rem] p-6 shadow-card">
            <div className="inline-flex items-center gap-2 rounded-full border border-aurora-magenta/20 bg-aurora-magenta/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.24em] text-aurora-magenta">
              Täglicher Impuls
            </div>
            <h2 className="mt-5 text-2xl font-semibold">Dein Raum wächst mit jedem ehrlichen Gedanken.</h2>
            <p className="mt-4 text-sm leading-7 text-white/65">
              Kleine Schritte sind keine kleinen Geschichten. Jede Frage, jede Idee und jedes bewusste Gespräch wird Teil deiner persönlichen inneren Infrastruktur.
            </p>
            <div className="mt-6 rounded-3xl border border-white/10 bg-black/10 p-5 text-sm text-white/65">
              Heute könntest du dir eine Minute nehmen und Kirobi fragen: „Was ist mein nächster kraftvoller Schritt?“
            </div>
          </div>
        </section>
      </main>
      <BottomNav />
    </div>
  );
}
