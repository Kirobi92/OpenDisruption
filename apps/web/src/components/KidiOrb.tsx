'use client';

import { useEffect, useRef } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

/**
 * KidiOrb — pure CSS/SVG rendition of the living KIDI heart.
 *
 * Vanilla canvas + framer-motion only — no @react-three/fiber, because
 * Next.js 15.x bundles its own canary React whose internals are
 * incompatible with the react-reconciler shipped by fiber 8.x.
 *
 * Visually layered:
 *  - radial halo gradient (blurred backdrop glow)
 *  - 3 concentric SVG halo rings (rotating)
 *  - central distorted blob (animated svg filter morph)
 *  - canvas spark particles orbiting the core (RAF, mouse-aware)
 */

interface KidiOrbProps {
  intensity?: number;
  className?: string;
}

function Sparks({ count = 96 }: { count?: number }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const ctx = cv.getContext('2d');
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    function resize() {
      const cv2 = ref.current;
      if (!cv2) return;
      const r = cv2.getBoundingClientRect();
      cv2.width = r.width * dpr;
      cv2.height = r.height * dpr;
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(cv);

    const particles = Array.from({ length: count }, () => {
      const a = Math.random() * Math.PI * 2;
      const r = 0.55 + Math.random() * 0.35;
      return {
        a,
        r,
        speed: 0.0006 + Math.random() * 0.0014,
        size: 0.6 + Math.random() * 1.4,
        hue: Math.random() < 0.5 ? '#5eead4' : Math.random() < 0.5 ? '#a78bfa' : '#e879f9',
      };
    });

    let raf = 0;
    function frame(t: number) {
      const cv2 = ref.current;
      if (!cv2 || !ctx) return;
      const w = cv2.width;
      const h = cv2.height;
      const cx = w / 2;
      const cy = h / 2;
      const baseR = Math.min(w, h) * 0.42;
      ctx.clearRect(0, 0, w, h);
      ctx.globalCompositeOperation = 'lighter';
      for (const p of particles) {
        p.a += p.speed * 16;
        const wob = Math.sin(t * 0.001 + p.a * 4) * 0.04;
        const r = baseR * (p.r + wob);
        const x = cx + Math.cos(p.a) * r;
        const y = cy + Math.sin(p.a) * r;
        ctx.fillStyle = p.hue;
        ctx.beginPath();
        ctx.arc(x, y, p.size * dpr, 0, Math.PI * 2);
        ctx.fill();
      }
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [count]);
  return <canvas ref={ref} className="absolute inset-0 h-full w-full" aria-hidden />;
}

function FallbackOrb() {
  return (
    <div className="relative aspect-square w-full max-w-[420px]">
      <div className="absolute inset-0 rounded-full bg-gradient-to-br from-aurora-cyan/40 via-aurora-violet/40 to-aurora-magenta/40 blur-3xl" />
      <div className="absolute inset-8 rounded-full border border-aurora-cyan/40 bg-void-900/60 backdrop-blur-2xl" />
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xl font-semibold tracking-[0.3em] text-aurora-cyan/80">KIDI</span>
      </div>
    </div>
  );
}

export default function KidiOrb({ intensity = 0.5, className = '' }: KidiOrbProps) {
  const reduce = useReducedMotion();
  if (reduce) {
    return (
      <div className={`flex items-center justify-center ${className}`}>
        <FallbackOrb />
      </div>
    );
  }

  const pulseScale = 1 + intensity * 0.06;

  return (
    <div className={`relative aspect-square w-full max-w-[480px] ${className}`}>
      {/* Backdrop glow */}
      <div className="pointer-events-none absolute inset-0 rounded-full bg-gradient-to-br from-aurora-cyan/30 via-aurora-violet/30 to-aurora-magenta/20 blur-3xl" />

      {/* Halo rings */}
      <svg viewBox="-100 -100 200 200" className="absolute inset-0 h-full w-full">
        <defs>
          <radialGradient id="kidi-core" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#5eead4" stopOpacity="0.95" />
            <stop offset="55%" stopColor="#a78bfa" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#0b0f24" stopOpacity="0" />
          </radialGradient>
          <filter id="kidi-blur" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="1.4" />
          </filter>
        </defs>

        <motion.g
          animate={{ rotate: 360 }}
          transition={{ duration: 24, ease: 'linear', repeat: Infinity }}
          style={{ transformOrigin: '0 0' }}
        >
          <ellipse cx="0" cy="0" rx="78" ry="22" fill="none" stroke="#5eead4" strokeOpacity="0.55" strokeWidth="0.6" />
        </motion.g>
        <motion.g
          animate={{ rotate: -360 }}
          transition={{ duration: 32, ease: 'linear', repeat: Infinity }}
          style={{ transformOrigin: '0 0' }}
        >
          <ellipse cx="0" cy="0" rx="86" ry="34" fill="none" stroke="#a78bfa" strokeOpacity="0.5" strokeWidth="0.6" transform="rotate(45)" />
        </motion.g>
        <motion.g
          animate={{ rotate: 360 }}
          transition={{ duration: 40, ease: 'linear', repeat: Infinity }}
          style={{ transformOrigin: '0 0' }}
        >
          <ellipse cx="0" cy="0" rx="92" ry="48" fill="none" stroke="#e879f9" strokeOpacity="0.4" strokeWidth="0.55" transform="rotate(110)" />
        </motion.g>

        {/* Core */}
        <motion.circle
          cx="0"
          cy="0"
          r="42"
          fill="url(#kidi-core)"
          filter="url(#kidi-blur)"
          animate={{ scale: [1, pulseScale, 1] }}
          transition={{ duration: 2.4, ease: 'easeInOut', repeat: Infinity }}
          style={{ transformOrigin: '0 0' }}
        />
        <motion.circle
          cx="0"
          cy="0"
          r="28"
          fill="#5eead4"
          fillOpacity="0.18"
          animate={{ scale: [1, 1.08, 1], opacity: [0.18, 0.32, 0.18] }}
          transition={{ duration: 1.6, ease: 'easeInOut', repeat: Infinity }}
          style={{ transformOrigin: '0 0' }}
        />
      </svg>

      {/* Spark canvas overlay */}
      <Sparks />

      {/* KIDI label */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <span className="rounded-full border border-white/10 bg-void-900/40 px-4 py-1 text-xs font-semibold tracking-[0.4em] text-aurora-cyan/80 backdrop-blur-sm">
          KIDI
        </span>
      </div>
    </div>
  );
}
