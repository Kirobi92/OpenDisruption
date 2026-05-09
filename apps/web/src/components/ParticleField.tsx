'use client';

import { useEffect, useRef } from 'react';
import { useReducedMotion } from 'framer-motion';

/**
 * GPU-light ambient particle field — vanilla canvas, no react-three.
 *
 * ~600 floating points with mouse parallax, additive blending for a
 * soft "intelligence breathing in the void" feel. Self-positions as
 * fixed background, pointer-events: none.
 */

const PARTICLE_COUNT = 600;

export default function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) return;
    const cv = canvasRef.current;
    if (!cv) return;
    const ctx = cv.getContext('2d');
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    function resize() {
      const cv2 = canvasRef.current;
      if (!cv2) return;
      cv2.width = window.innerWidth * dpr;
      cv2.height = window.innerHeight * dpr;
    }
    resize();
    window.addEventListener('resize', resize);

    const pointer = { x: 0, y: 0 };
    function onMove(e: PointerEvent) {
      pointer.x = (e.clientX / window.innerWidth - 0.5) * 2;
      pointer.y = (e.clientY / window.innerHeight - 0.5) * 2;
    }
    window.addEventListener('pointermove', onMove);

    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random(),
      y: Math.random(),
      z: 0.2 + Math.random() * 0.8,
      vx: (Math.random() - 0.5) * 0.0004,
      vy: (Math.random() - 0.5) * 0.0004,
      hue: Math.random() < 0.4 ? '#5eead4' : Math.random() < 0.5 ? '#a78bfa' : '#e879f9',
      size: 0.4 + Math.random() * 1.2,
    }));

    let raf = 0;
    function frame(t: number) {
      const cv2 = canvasRef.current;
      if (!cv2 || !ctx) return;
      const w = cv2.width;
      const h = cv2.height;
      ctx.clearRect(0, 0, w, h);
      ctx.globalCompositeOperation = 'lighter';

      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x += 1;
        if (p.x > 1) p.x -= 1;
        if (p.y < 0) p.y += 1;
        if (p.y > 1) p.y -= 1;

        const px = (p.x + pointer.x * 0.02 * p.z) * w;
        const py = (p.y + pointer.y * 0.02 * p.z) * h;
        const tw = 0.55 + 0.45 * Math.sin(t * 0.0008 + p.x * 12 + p.y * 12);
        ctx.fillStyle = p.hue;
        ctx.globalAlpha = 0.18 * p.z * tw;
        ctx.beginPath();
        ctx.arc(px, py, p.size * dpr * p.z, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
      window.removeEventListener('pointermove', onMove);
    };
  }, [reduce]);

  if (reduce) return null;

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 h-full w-full"
      style={{ width: '100vw', height: '100vh' }}
    />
  );
}
