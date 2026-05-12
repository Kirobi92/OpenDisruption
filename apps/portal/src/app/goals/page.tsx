'use client';

import { motion } from 'framer-motion';
import { ChevronDown, ChevronUp, Plus, Sparkles } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { BottomNav } from '@/components/layout/BottomNav';
import { Header } from '@/components/layout/Header';
import { useRequireAuth } from '@/lib/auth';

type GoalStatus = 'Aktiv' | 'Abgeschlossen' | 'Pausiert';
type GoalCategory = 'Gesundheit' | 'Lernen' | 'Karriere' | 'Kreativität' | 'Beziehungen' | 'Finanzen';

type GoalItem = {
  id: string;
  title: string;
  description: string;
  progress: number;
  targetDate: string;
  status: GoalStatus;
  category: GoalCategory;
  agent: string;
  subtasks: { id: string; label: string; done: boolean }[];
};

const habitsSeed = ['Wasser trinken', '15 Min. Fokus', 'Dankbarkeit', 'Bewegung', 'Lernen'];

export default function GoalsPage() {
  const { isLoading, isAuthenticated } = useRequireAuth();
  const [goals, setGoals] = useState<GoalItem[]>([
    {
      id: 'goal-deutsch',
      title: 'Deutsch lernen',
      description: 'Täglich Vokabeln, Hören und kleine Gespräche integrieren.',
      progress: 45,
      targetDate: '2026-08-01',
      status: 'Aktiv',
      category: 'Lernen',
      agent: 'kirobi',
      subtasks: [
        { id: 'g1', label: '10 Minuten Hörverständnis', done: true },
        { id: 'g2', label: '3 neue Sätze schreiben', done: false },
        { id: 'g3', label: 'Vokabelkarten wiederholen', done: false },
      ],
    },
    {
      id: 'goal-fitness',
      title: 'Fitness',
      description: 'Mehr Energie über konsequente Bewegung und Regeneration.',
      progress: 60,
      targetDate: '2026-07-15',
      status: 'Aktiv',
      category: 'Gesundheit',
      agent: 'samira',
      subtasks: [
        { id: 'g4', label: '3 Workouts pro Woche', done: true },
        { id: 'g5', label: 'Täglicher Spaziergang', done: true },
        { id: 'g6', label: 'Schlafroutine stabilisieren', done: false },
      ],
    },
    {
      id: 'goal-project',
      title: 'Neues Projekt starten',
      description: 'Idee konkretisieren und einen ersten sichtbaren Prototyp bauen.',
      progress: 20,
      targetDate: '2026-09-10',
      status: 'Aktiv',
      category: 'Karriere',
      agent: 'sineo',
      subtasks: [
        { id: 'g7', label: 'Mission formulieren', done: true },
        { id: 'g8', label: 'Prototyp skizzieren', done: false },
        { id: 'g9', label: 'Feedbackgespräch planen', done: false },
      ],
    },
  ]);
  const [expandedGoalId, setExpandedGoalId] = useState<string | null>('goal-deutsch');
  const [goalModalOpen, setGoalModalOpen] = useState(false);
  const [goalDraft, setGoalDraft] = useState({
    title: '',
    description: '',
    targetDate: '',
    category: 'Kreativität' as GoalCategory,
  });
  const [habitState, setHabitState] = useState<Record<string, boolean>>({});
  const [mood, setMood] = useState('🙂');
  const [moodNote, setMoodNote] = useState('');
  const [coachingText, setCoachingText] = useState('Wähle ein Ziel und hole dir einen kurzen KI-Coaching-Impuls.');

  useEffect(() => {
    const storedHabits = window.localStorage.getItem('kirobi.portal.habits');
    const storedMood = window.localStorage.getItem('kirobi.portal.mood');

    if (storedHabits) {
      setHabitState(JSON.parse(storedHabits) as Record<string, boolean>);
    } else {
      setHabitState(Object.fromEntries(habitsSeed.map((habit) => [habit, false])));
    }

    if (storedMood) {
      const parsed = JSON.parse(storedMood) as { mood: string; note: string };
      setMood(parsed.mood);
      setMoodNote(parsed.note);
    }
  }, []);

  useEffect(() => {
    if (Object.keys(habitState).length > 0) {
      window.localStorage.setItem('kirobi.portal.habits', JSON.stringify(habitState));
    }
  }, [habitState]);

  useEffect(() => {
    window.localStorage.setItem('kirobi.portal.mood', JSON.stringify({ mood, note: moodNote }));
  }, [mood, moodNote]);

  const progressByCategory = useMemo(() => {
    const groups = new Map<GoalCategory, number[]>();
    goals.forEach((goal) => {
      const current = groups.get(goal.category) ?? [];
      current.push(goal.progress);
      groups.set(goal.category, current);
    });
    return Array.from(groups.entries()).map(([category, values]) => ({
      category,
      progress: Math.round(values.reduce((sum, value) => sum + value, 0) / values.length),
    }));
  }, [goals]);

  const handleCreateGoal = () => {
    if (!goalDraft.title.trim() || !goalDraft.description.trim() || !goalDraft.targetDate) {
      return;
    }

    setGoals((current) => [
      {
        id: `goal-${Date.now()}`,
        title: goalDraft.title.trim(),
        description: goalDraft.description.trim(),
        progress: 0,
        targetDate: goalDraft.targetDate,
        status: 'Aktiv',
        category: goalDraft.category,
        agent: 'kirobi',
        subtasks: [
          { id: `sub-${Date.now()}-1`, label: 'Ersten kleinen Schritt definieren', done: false },
          { id: `sub-${Date.now()}-2`, label: 'Rhythmus festlegen', done: false },
        ],
      },
      ...current,
    ]);
    setGoalDraft({ title: '', description: '', targetDate: '', category: 'Kreativität' });
    setGoalModalOpen(false);
  };

  if (isLoading || !isAuthenticated) {
    return <div className="min-h-screen bg-void" />;
  }

  return (
    <div className="min-h-screen pb-24 md:pb-8">
      <Header title="Ziele" />
      <main className="mx-auto max-w-7xl px-4 pb-10 pt-20 md:px-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold">Ziele & Self-Management</h1>
            <p className="mt-2 text-white/60">Fokus, Gewohnheiten und Coaching in einem lebendigen System.</p>
          </div>
          <button
            type="button"
            onClick={() => setGoalModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet px-5 py-2.5 font-semibold text-void shadow-glow-cyan"
          >
            <Plus className="h-4 w-4" />
            Neues Ziel
          </button>
        </div>

        <section className="mt-6 space-y-4">
          {goals.map((goal) => {
            const expanded = expandedGoalId === goal.id;
            return (
              <motion.div key={goal.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-[2rem] p-6 shadow-card">
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-2xl font-semibold">{goal.title}</h2>
                      <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/60">{goal.status}</span>
                      <span className="rounded-full border border-aurora-cyan/20 bg-aurora-cyan/10 px-3 py-1 text-xs text-aurora-cyan">{goal.agent}</span>
                    </div>
                    <p className="mt-3 text-sm leading-7 text-white/65">{goal.description}</p>
                    <div className="mt-4 h-3 overflow-hidden rounded-full bg-white/10">
                      <div className="h-full rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet" style={{ width: `${goal.progress}%` }} />
                    </div>
                    <div className="mt-3 flex flex-wrap gap-4 text-sm text-white/55">
                      <span>{goal.progress}%</span>
                      <span>Zieltermin: {goal.targetDate}</span>
                      <span>{goal.category}</span>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() =>
                        setCoachingText(
                          `Coaching für ${goal.title}: Heute zählt der nächste winzige Schritt. Frage dich, welche 15-Minuten-Aktion dich am stärksten nach vorne bringt.`,
                        )
                      }
                      className="rounded-full border border-aurora-cyan/20 bg-aurora-cyan/10 px-4 py-2 text-sm text-aurora-cyan"
                    >
                      KI-Coaching
                    </button>
                    <button
                      type="button"
                      onClick={() => setExpandedGoalId(expanded ? null : goal.id)}
                      className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/70"
                    >
                      {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {expanded ? (
                  <div className="mt-5 rounded-3xl border border-white/10 bg-black/10 p-5">
                    <div className="mb-3 text-sm font-medium text-white/80">Sub-Tasks</div>
                    <div className="space-y-3">
                      {goal.subtasks.map((task) => (
                        <label key={task.id} className="flex items-center gap-3 text-sm text-white/70">
                          <input
                            type="checkbox"
                            checked={task.done}
                            onChange={() => {
                              setGoals((current) =>
                                current.map((item) =>
                                  item.id === goal.id
                                    ? {
                                        ...item,
                                        subtasks: item.subtasks.map((subtask) =>
                                          subtask.id === task.id ? { ...subtask, done: !subtask.done } : subtask,
                                        ),
                                      }
                                    : item,
                                ),
                              );
                            }}
                            className="h-4 w-4 rounded border-white/20 bg-transparent"
                          />
                          {task.label}
                        </label>
                      ))}
                    </div>
                  </div>
                ) : null}
              </motion.div>
            );
          })}
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="glass rounded-[2rem] p-6 shadow-card">
            <div className="text-xl font-semibold">Daily Habits</div>
            <div className="mt-5 space-y-3">
              {habitsSeed.map((habit) => (
                <label key={habit} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/70">
                  <span>{habit}</span>
                  <input
                    type="checkbox"
                    checked={Boolean(habitState[habit])}
                    onChange={() => setHabitState((current) => ({ ...current, [habit]: !current[habit] }))}
                    className="h-4 w-4 rounded border-white/20 bg-transparent"
                  />
                </label>
              ))}
            </div>
          </div>

          <div className="grid gap-6">
            <div className="glass rounded-[2rem] p-6 shadow-card">
              <div className="text-xl font-semibold">Mood Log</div>
              <div className="mt-4 flex flex-wrap gap-3">
                {['😔', '😐', '🙂', '😊', '🤩'].map((entry) => (
                  <button
                    key={entry}
                    type="button"
                    onClick={() => setMood(entry)}
                    className={`rounded-full px-4 py-3 text-2xl transition ${
                      mood === entry ? 'bg-aurora-magenta/20 shadow-glow-magenta' : 'border border-white/10 bg-white/5'
                    }`}
                  >
                    {entry}
                  </button>
                ))}
              </div>
              <textarea
                value={moodNote}
                onChange={(event) => setMoodNote(event.target.value)}
                placeholder="Was prägt deine Stimmung heute?"
                className="mt-4 min-h-[120px] w-full rounded-3xl border border-white/10 bg-white/5 px-4 py-3 outline-none"
              />
            </div>

            <div className="glass rounded-[2rem] p-6 shadow-card">
              <div className="inline-flex items-center gap-2 rounded-full border border-aurora-cyan/20 bg-aurora-cyan/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-aurora-cyan">
                <Sparkles className="h-4 w-4" />
                KI-Coaching
              </div>
              <p className="mt-4 text-sm leading-7 text-white/65">{coachingText}</p>
            </div>
          </div>
        </section>

        <section className="mt-8 glass rounded-[2rem] p-6 shadow-card">
          <div className="text-xl font-semibold">Fortschrittsübersicht</div>
          <div className="mt-6 space-y-4">
            {progressByCategory.map((entry) => (
              <div key={entry.category} className="space-y-2">
                <div className="flex items-center justify-between text-sm text-white/65">
                  <span>{entry.category}</span>
                  <span>{entry.progress}%</span>
                </div>
                <div className="h-8 overflow-hidden rounded-xl bg-white/5">
                  <div className="h-full rounded-xl bg-gradient-to-r from-kirobi-400 via-aurora-cyan to-aurora-violet" style={{ width: `${entry.progress}%` }} />
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      {goalModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-xl rounded-[2rem] border border-white/10 bg-void-deep p-6 shadow-card">
            <h3 className="text-2xl font-semibold">Neues Ziel</h3>
            <div className="mt-5 space-y-4">
              <input
                value={goalDraft.title}
                onChange={(event) => setGoalDraft((current) => ({ ...current, title: event.target.value }))}
                placeholder="Titel"
                className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 px-4 outline-none"
              />
              <textarea
                value={goalDraft.description}
                onChange={(event) => setGoalDraft((current) => ({ ...current, description: event.target.value }))}
                placeholder="Beschreibung"
                className="min-h-[140px] w-full rounded-3xl border border-white/10 bg-white/5 px-4 py-3 outline-none"
              />
              <input
                type="date"
                value={goalDraft.targetDate}
                onChange={(event) => setGoalDraft((current) => ({ ...current, targetDate: event.target.value }))}
                className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 px-4 outline-none"
              />
              <select
                value={goalDraft.category}
                onChange={(event) => setGoalDraft((current) => ({ ...current, category: event.target.value as GoalCategory }))}
                className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 px-4 outline-none"
              >
                {['Gesundheit', 'Lernen', 'Karriere', 'Kreativität', 'Beziehungen', 'Finanzen'].map((category) => (
                  <option key={category} value={category} className="bg-void-deep">
                    {category}
                  </option>
                ))}
              </select>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button type="button" onClick={() => setGoalModalOpen(false)} className="rounded-full border border-white/10 px-5 py-2.5 text-white/65">
                Abbrechen
              </button>
              <button type="button" onClick={handleCreateGoal} className="rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet px-5 py-2.5 font-semibold text-void shadow-glow-cyan">
                Speichern
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <BottomNav />
    </div>
  );
}
