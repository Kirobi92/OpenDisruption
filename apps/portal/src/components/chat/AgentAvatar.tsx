'use client';

const AGENT_STYLES: Record<string, { emoji: string; className: string }> = {
  kirobi: { emoji: '🌟', className: 'from-kirobi-400 to-aurora-cyan shadow-glow-cyan' },
  samira: { emoji: '💜', className: 'from-aurora-magenta to-aurora-violet shadow-glow-magenta' },
  sineo: { emoji: '🎨', className: 'from-aurora-violet to-kirobi-500 shadow-glow-violet' },
  hermes: { emoji: '🜂', className: 'from-aurora-violet to-purple-700 shadow-glow-violet' },
  nutzi: { emoji: '✨', className: 'from-aurora-gold to-amber-500 shadow-[0_0_20px_rgba(251,191,36,0.35)]' },
};

const SIZE_CLASSES = {
  sm: 'h-8 w-8 text-sm',
  md: 'h-10 w-10 text-base',
  lg: 'h-14 w-14 text-xl',
} as const;

export function AgentAvatar({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' | 'lg' }) {
  const style = AGENT_STYLES[name.toLowerCase()] ?? AGENT_STYLES.kirobi;

  return (
    <div
      className={`inline-flex items-center justify-center rounded-full bg-gradient-to-br text-white ${SIZE_CLASSES[size]} ${style.className}`}
      aria-label={`${name} Avatar`}
      title={name}
    >
      <span>{style.emoji}</span>
    </div>
  );
}
