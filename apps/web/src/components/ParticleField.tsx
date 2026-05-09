'use client';

import { useEffect, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { useReducedMotion } from 'framer-motion';
import * as THREE from 'three';

/**
 * GPU-accelerated ambient particle field.
 * - Renders ~2000 instanced points orbiting a central attractor
 * - Reactive to mouse position (subtle parallax)
 * - Falls back to nothing when prefers-reduced-motion
 *
 * Drop into a layout: <ParticleField /> — it self-positions as fixed bg.
 */

const PARTICLE_COUNT = 2000;
const FIELD_RADIUS = 18;

function Cloud({ pointer }: { pointer: React.MutableRefObject<{ x: number; y: number }> }) {
  const ref = useRef<THREE.Points>(null);

  // Build initial positions + per-particle phase only once.
  const { positions, phases, colors } = (() => {
    const positions = new Float32Array(PARTICLE_COUNT * 3);
    const phases = new Float32Array(PARTICLE_COUNT);
    const colors = new Float32Array(PARTICLE_COUNT * 3);
    const palette = [
      new THREE.Color('#5eead4'), // aurora cyan
      new THREE.Color('#a78bfa'), // aurora violet
      new THREE.Color('#e879f9'), // aurora magenta
      new THREE.Color('#fbbf24'), // aurora gold
    ];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const r = Math.cbrt(Math.random()) * FIELD_RADIUS;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3 + 0] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
      phases[i] = Math.random() * Math.PI * 2;
      const c = palette[i % palette.length];
      colors[i * 3 + 0] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }
    return { positions, phases, colors };
  })();

  useFrame((state) => {
    const points = ref.current;
    if (!points) return;
    const t = state.clock.elapsedTime;
    const arr = points.geometry.attributes.position.array as Float32Array;
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const phase = phases[i];
      arr[i * 3 + 1] += Math.sin(t * 0.4 + phase) * 0.0015;
      arr[i * 3 + 0] += Math.cos(t * 0.3 + phase) * 0.0010;
    }
    points.geometry.attributes.position.needsUpdate = true;
    points.rotation.y = t * 0.02 + pointer.current.x * 0.4;
    points.rotation.x = pointer.current.y * 0.2;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={PARTICLE_COUNT}
          array={positions}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          count={PARTICLE_COUNT}
          array={colors}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.08}
        sizeAttenuation
        vertexColors
        transparent
        opacity={0.85}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

export default function ParticleField({ className = '' }: { className?: string }) {
  const reduce = useReducedMotion();
  const pointer = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (reduce) return;
    const onMove = (e: PointerEvent) => {
      pointer.current.x = (e.clientX / window.innerWidth) * 2 - 1;
      pointer.current.y = (e.clientY / window.innerHeight) * 2 - 1;
    };
    window.addEventListener('pointermove', onMove, { passive: true });
    return () => window.removeEventListener('pointermove', onMove);
  }, [reduce]);

  if (reduce) return null;

  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none fixed inset-0 -z-10 ${className}`}
      style={{ background: 'radial-gradient(circle at 50% 30%, rgba(94,234,212,0.06), transparent 60%)' }}
    >
      <Canvas
        camera={{ position: [0, 0, 14], fov: 60 }}
        gl={{ antialias: false, alpha: true, powerPreference: 'high-performance' }}
        dpr={[1, 1.5]}
      >
        <Cloud pointer={pointer} />
      </Canvas>
    </div>
  );
}
