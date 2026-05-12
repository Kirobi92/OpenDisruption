'use client';

import { LoaderCircle, Mic, Volume2 } from 'lucide-react';

export function VoiceButton({
  state,
  onClick,
}: {
  state: 'idle' | 'listening' | 'processing' | 'speaking';
  onClick: () => void;
}) {
  const isListening = state === 'listening';
  const isProcessing = state === 'processing';
  const isSpeaking = state === 'speaking';

  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative inline-flex h-20 w-20 items-center justify-center rounded-full border text-white transition duration-300 ${
        isListening
          ? 'border-aurora-cyan/60 bg-aurora-cyan/20 shadow-glow-cyan'
          : isProcessing
            ? 'border-aurora-gold/60 bg-aurora-gold/10'
            : isSpeaking
              ? 'border-aurora-magenta/60 bg-aurora-magenta/20 shadow-glow-magenta'
              : 'border-white/15 bg-white/5'
      }`}
      aria-label="Sprachaufnahme"
    >
      {isListening && (
        <>
          <span className="pointer-events-none absolute inset-0 rounded-full border border-aurora-cyan/40 animate-[voicePulse_1.6s_ease-out_infinite]" />
          <span className="pointer-events-none absolute inset-[-12px] rounded-full border border-aurora-cyan/25 animate-[voicePulse_1.6s_ease-out_0.3s_infinite]" />
          <span className="pointer-events-none absolute inset-[-24px] rounded-full border border-aurora-cyan/15 animate-[voicePulse_1.6s_ease-out_0.6s_infinite]" />
        </>
      )}

      {isProcessing ? (
        <LoaderCircle className="h-8 w-8 animate-spin text-aurora-gold" />
      ) : isSpeaking ? (
        <div className="flex items-end gap-1">
          <span className="h-3 w-1 rounded-full bg-white animate-[voiceWave_0.9s_ease-in-out_infinite]" />
          <span className="h-5 w-1 rounded-full bg-white animate-[voiceWave_0.9s_ease-in-out_0.15s_infinite]" />
          <Volume2 className="h-7 w-7 text-white" />
        </div>
      ) : (
        <Mic className={`h-8 w-8 ${isListening ? 'text-aurora-cyan' : 'text-white/85'}`} />
      )}

      <style jsx>{`
        @keyframes voicePulse {
          0% {
            transform: scale(1);
            opacity: 0.7;
          }
          100% {
            transform: scale(1.55);
            opacity: 0;
          }
        }
        @keyframes voiceWave {
          0%,
          100% {
            transform: scaleY(0.5);
            opacity: 0.7;
          }
          50% {
            transform: scaleY(1.2);
            opacity: 1;
          }
        }
      `}</style>
    </button>
  );
}
