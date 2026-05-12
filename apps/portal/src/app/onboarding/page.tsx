'use client';

import { AnimatePresence, motion, PanInfo } from 'framer-motion';
import {
  BriefcaseBusiness,
  Lightbulb,
  PenTool,
  Rocket,
  Sparkles,
  Target,
  Waves,
  WandSparkles,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useMemo, useState } from 'react';

const interestOptions = ['Technologie', 'Musik', 'Kreativität', 'Business', 'Familie', 'Lernen', 'Sport', 'Kunst', 'Reisen', 'Kochen'];
const goalSuggestions = ['Mehr Fokus', 'Gesunde Routinen', 'Kreative Projekte', 'Bessere Organisation', 'Tiefe Gespräche'];

const styles = [
  { id: 'professionell', label: 'Professionell', description: 'Klar, souverän und strukturiert.', icon: BriefcaseBusiness },
  { id: 'locker', label: 'Locker & Freundlich', description: 'Warm, leicht und nahbar.', icon: Waves },
  { id: 'kreativ', label: 'Kreativ', description: 'Inspirierend, verspielt und offen.', icon: PenTool },
  { id: 'direkt', label: 'Direkt & Präzise', description: 'Auf den Punkt, effizient und fokussiert.', icon: Target },
] as const;

const features = [
  { title: 'Chat-Assistent', text: 'Sofortige Gespräche, Reflexionen und Ideen in einem Flow.', icon: Sparkles },
  { title: 'Wissensgraph', text: 'Verbinde Gedanken, Dokumente und Erinnerungen visuell.', icon: Lightbulb },
  { title: 'Sprachmodus', text: 'Rede mit Kirobi natürlich per Stimme, auch unterwegs.', icon: Waves },
  { title: 'Mediengenerierung', text: 'Bilder, Musik und Videos direkt aus deinen Impulsen.', icon: WandSparkles },
  { title: 'Ziele & Wachstum', text: 'Behalte Fortschritt, Habits und Coaching im Blick.', icon: Rocket },
] as const;

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [name, setName] = useState('');
  const [interests, setInterests] = useState<string[]>([]);
  const [goals, setGoals] = useState(['', '', '']);
  const [communicationStyle, setCommunicationStyle] = useState<typeof styles[number]['id']>('locker');
  const [featureIndex, setFeatureIndex] = useState(0);

  const progress = useMemo(() => `${(step / 6) * 100}%`, [step]);

  const handleNext = () => setStep((current) => Math.min(6, current + 1));
  const handleBack = () => setStep((current) => Math.max(1, current - 1));
  const handleFinish = () => {
    window.localStorage.setItem(
      'kirobi.portal.onboarding',
      JSON.stringify({ name, interests, goals, communicationStyle, finishedAt: new Date().toISOString() }),
    );
    router.push('/');
  };

  const toggleInterest = (interest: string) => {
    setInterests((current) =>
      current.includes(interest) ? current.filter((item) => item !== interest) : [...current, interest],
    );
  };

  const applyGoalSuggestion = (suggestion: string) => {
    setGoals((current) => {
      const nextGoals = [...current];
      const emptyIndex = nextGoals.findIndex((goal) => !goal.trim());
      const targetIndex = emptyIndex === -1 ? 0 : emptyIndex;
      nextGoals[targetIndex] = suggestion;
      return nextGoals;
    });
  };

  const handleFeatureDrag = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    if (info.offset.x < -80) {
      setFeatureIndex((current) => Math.min(features.length - 1, current + 1));
    }
    if (info.offset.x > 80) {
      setFeatureIndex((current) => Math.max(0, current - 1));
    }
  };

  return (
    <main className="min-h-screen bg-void px-4 py-6 text-white md:px-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div className="flex-1">
            <div className="mb-3 flex items-center justify-between text-xs uppercase tracking-[0.28em] text-white/45">
              <span>Onboarding</span>
              <span>Schritt {step} / 6</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full bg-gradient-to-r from-kirobi-400 via-aurora-cyan to-aurora-violet transition-all duration-500" style={{ width: progress }} />
            </div>
          </div>
          <button
            type="button"
            onClick={() => router.push('/')}
            className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/60 transition hover:border-white/20 hover:text-white"
          >
            Überspringen
          </button>
        </div>

        <AnimatePresence mode="wait">
          <motion.section
            key={step}
            initial={{ opacity: 0, x: 36 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -36 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="glass rounded-[2rem] p-6 shadow-card md:p-10"
          >
            {step === 1 ? (
              <div className="flex min-h-[520px] flex-col items-center justify-center text-center">
                <motion.div
                  animate={{ y: [0, -16, 0] }}
                  transition={{ repeat: Number.POSITIVE_INFINITY, duration: 2.3, ease: 'easeInOut' }}
                  className="mb-8 inline-flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br from-kirobi-400 via-aurora-cyan to-aurora-violet text-5xl shadow-glow-cyan"
                >
                  🌟
                </motion.div>
                <h1 className="text-4xl font-semibold md:text-5xl">Ich bin Kirobi, dein persönlicher KI-Assistent! 🌟</h1>
                <p className="mt-6 max-w-2xl text-lg leading-8 text-white/70">
                  Gemeinsam bauen wir dir einen Raum für Klarheit, Kreativität, Wissen und echtes persönliches Wachstum.
                </p>
                <button
                  type="button"
                  onClick={handleNext}
                  className="mt-10 rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet px-8 py-3 font-semibold text-void shadow-glow-cyan"
                >
                  Weiter
                </button>
              </div>
            ) : null}

            {step === 2 ? (
              <div className="space-y-8">
                <div>
                  <h2 className="text-3xl font-semibold">Wie darf ich dich nennen?</h2>
                  <p className="mt-3 text-white/65">Sag mir deinen Namen und zeig mir, wofür dein Herz gerade schlägt.</p>
                </div>
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Dein Name"
                  className="h-14 w-full rounded-2xl border border-white/10 bg-white/5 px-5 text-lg outline-none focus:border-aurora-cyan/40"
                />
                <div>
                  <div className="mb-4 text-sm font-medium text-white/80">Interessen auswählen</div>
                  <div className="flex flex-wrap gap-3">
                    {interestOptions.map((interest) => {
                      const active = interests.includes(interest);
                      return (
                        <button
                          key={interest}
                          type="button"
                          onClick={() => toggleInterest(interest)}
                          className={`rounded-full px-4 py-2 text-sm transition ${
                            active
                              ? 'bg-aurora-cyan/20 text-aurora-cyan shadow-glow-cyan'
                              : 'border border-white/10 bg-white/5 text-white/70 hover:bg-white/10'
                          }`}
                        >
                          {interest}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : null}

            {step === 3 ? (
              <div className="space-y-8">
                <div>
                  <h2 className="text-3xl font-semibold">Was sind deine wichtigsten Ziele?</h2>
                  <p className="mt-3 text-white/65">Gib mir drei Leitsterne, damit ich dich gezielt begleiten kann.</p>
                </div>
                <div className="space-y-4">
                  {goals.map((goal, index) => (
                    <input
                      key={`goal-${index}`}
                      value={goal}
                      onChange={(event) => {
                        const nextGoals = [...goals];
                        nextGoals[index] = event.target.value;
                        setGoals(nextGoals);
                      }}
                      placeholder={`Ziel ${index + 1}`}
                      className="h-14 w-full rounded-2xl border border-white/10 bg-white/5 px-5 outline-none focus:border-aurora-magenta/40"
                    />
                  ))}
                </div>
                <div>
                  <div className="mb-3 text-sm font-medium text-white/80">Vorschläge</div>
                  <div className="flex flex-wrap gap-3">
                    {goalSuggestions.map((suggestion) => (
                      <button
                        key={suggestion}
                        type="button"
                        onClick={() => applyGoalSuggestion(suggestion)}
                        className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/70 transition hover:border-aurora-violet/30 hover:text-white"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}

            {step === 4 ? (
              <div className="space-y-8">
                <div>
                  <h2 className="text-3xl font-semibold">Wie soll ich mit dir sprechen?</h2>
                  <p className="mt-3 text-white/65">Wähle den Stil, der sich für dich am meisten nach Zuhause anfühlt.</p>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  {styles.map(({ id, label, description, icon: Icon }) => {
                    const active = communicationStyle === id;
                    return (
                      <button
                        key={id}
                        type="button"
                        onClick={() => setCommunicationStyle(id)}
                        className={`rounded-3xl border p-5 text-left transition ${
                          active
                            ? 'border-aurora-magenta/40 bg-aurora-magenta/10 shadow-glow-magenta'
                            : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10'
                        }`}
                      >
                        <Icon className="h-7 w-7 text-white" />
                        <div className="mt-4 text-xl font-semibold">{label}</div>
                        <p className="mt-2 text-sm leading-6 text-white/65">{description}</p>
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : null}

            {step === 5 ? (
              <div className="space-y-8">
                <div>
                  <h2 className="text-3xl font-semibold">Feature Tour</h2>
                  <p className="mt-3 text-white/65">Wische durch die wichtigsten Bereiche deines zweiten Gehirns.</p>
                </div>
                <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-white/5 p-3">
                  <motion.div drag="x" dragConstraints={{ left: 0, right: 0 }} onDragEnd={handleFeatureDrag}>
                    <div className="grid gap-4 md:grid-cols-[1.1fr_0.9fr]">
                      <div className="rounded-[1.5rem] bg-gradient-to-br from-kirobi-500/25 via-aurora-cyan/10 to-aurora-violet/20 p-8">
                        <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10">
                          {(() => {
                            const Icon = features[featureIndex].icon;
                            return <Icon className="h-7 w-7 text-white" />;
                          })()}
                        </div>
                        <h3 className="mt-6 text-2xl font-semibold">{features[featureIndex].title}</h3>
                        <p className="mt-3 max-w-xl text-white/65">{features[featureIndex].text}</p>
                      </div>
                      <div className="flex flex-col justify-between rounded-[1.5rem] border border-white/10 bg-black/10 p-6">
                        <div className="space-y-3">
                          {features.map((feature, index) => (
                            <button
                              key={feature.title}
                              type="button"
                              onClick={() => setFeatureIndex(index)}
                              className={`w-full rounded-2xl px-4 py-3 text-left transition ${
                                index === featureIndex
                                  ? 'bg-white/10 text-white shadow-card'
                                  : 'text-white/55 hover:bg-white/5 hover:text-white'
                              }`}
                            >
                              {feature.title}
                            </button>
                          ))}
                        </div>
                        <div className="mt-6 flex items-center justify-between text-sm text-white/55">
                          <button type="button" onClick={() => setFeatureIndex((current) => Math.max(0, current - 1))}>
                            Zurück
                          </button>
                          <span>
                            {featureIndex + 1} / {features.length}
                          </span>
                          <button type="button" onClick={() => setFeatureIndex((current) => Math.min(features.length - 1, current + 1))}>
                            Weiter
                          </button>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </div>
              </div>
            ) : null}

            {step === 6 ? (
              <div className="relative flex min-h-[520px] flex-col items-center justify-center overflow-hidden text-center">
                <div className="pointer-events-none absolute inset-0">
                  {Array.from({ length: 24 }).map((_, index) => (
                    <span
                      key={`confetti-${index}`}
                      className="absolute h-3 w-3 rounded-full bg-aurora-cyan/70"
                      style={{
                        left: `${(index % 6) * 16 + 10}%`,
                        top: `${Math.floor(index / 6) * 16 + 8}%`,
                        animation: `confetti ${3 + (index % 3)}s linear ${index * 0.08}s infinite`,
                        background:
                          index % 4 === 0
                            ? '#5eead4'
                            : index % 4 === 1
                              ? '#e879f9'
                              : index % 4 === 2
                                ? '#a78bfa'
                                : '#fbbf24',
                      }}
                    />
                  ))}
                </div>
                <div className="relative z-10">
                  <div className="mx-auto inline-flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br from-kirobi-400 via-aurora-cyan to-aurora-violet text-5xl shadow-glow-cyan">
                    🧠
                  </div>
                  <h2 className="mt-8 text-4xl font-semibold md:text-5xl">Alles bereit! Willkommen in deinem zweiten Gehirn 🧠✨</h2>
                  <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-white/65">
                    Kirobi ist startklar, um mit dir zu denken, zu fühlen, zu planen und zu erschaffen.
                  </p>
                  <button
                    type="button"
                    onClick={handleFinish}
                    className="mt-10 rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet px-8 py-3 font-semibold text-void shadow-glow-cyan"
                  >
                    Los geht&apos;s!
                  </button>
                </div>
                <style jsx>{`
                  @keyframes confetti {
                    0% {
                      transform: translateY(-12px) scale(0.8);
                      opacity: 0;
                    }
                    10% {
                      opacity: 1;
                    }
                    100% {
                      transform: translateY(260px) rotate(240deg) scale(1.1);
                      opacity: 0;
                    }
                  }
                `}</style>
              </div>
            ) : null}

            {step > 1 && step < 6 ? (
              <div className="mt-10 flex items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={handleBack}
                  className="rounded-full border border-white/10 px-5 py-2.5 text-sm text-white/60 transition hover:border-white/20 hover:text-white"
                >
                  Zurück
                </button>
                <button
                  type="button"
                  onClick={handleNext}
                  className="rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet px-6 py-2.5 font-semibold text-void shadow-glow-cyan"
                >
                  Weiter
                </button>
              </div>
            ) : null}
          </motion.section>
        </AnimatePresence>
      </div>
    </main>
  );
}
