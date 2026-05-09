'use client';

import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, Float } from '@react-three/drei';
import { useReducedMotion } from 'framer-motion';
import * as THREE from 'three';

/**
 * KidiOrb — the living heart of KIDI.
 *
 * A central distorted sphere with neon pulse, surrounded by orbiting halo
 * rings and a soft rim glow. Reactive to time + optional `intensity` prop
 * (0..1) for binding to runtime state (heartbeat / inference activity).
 *
 * Reduced-motion users get a static SVG fallback.
 */

interface KidiOrbProps {
  intensity?: number; // 0..1, drives pulse amplitude
  size?: number; // viewport width hint, used for canvas height
  className?: string;
}

function Core({ intensity }: { intensity: number }) {
  const ref = useRef<THREE.Mesh>(null);
  useFrame((state) => {
    const m = ref.current;
    if (!m) return;
    const t = state.clock.elapsedTime;
    const pulse = 1 + (Math.sin(t * 1.6) * 0.04 + intensity * 0.1);
    m.scale.setScalar(pulse);
    m.rotation.y = t * 0.18;
    m.rotation.x = t * 0.08;
  });
  return (
    <Float speed={1.2} rotationIntensity={0.4} floatIntensity={0.6}>
      <Sphere ref={ref} args={[1.1, 96, 96]}>
        <MeshDistortMaterial
          color="#5eead4"
          emissive="#a78bfa"
          emissiveIntensity={0.7 + intensity * 0.6}
          roughness={0.18}
          metalness={0.55}
          distort={0.42}
          speed={1.6}
        />
      </Sphere>
    </Float>
  );
}

function HaloRing({ radius, speed, color, tilt }: { radius: number; speed: number; color: string; tilt: number }) {
  const ref = useRef<THREE.Mesh>(null);
  useFrame((state) => {
    const m = ref.current;
    if (!m) return;
    m.rotation.z = state.clock.elapsedTime * speed;
    m.rotation.x = tilt;
  });
  return (
    <mesh ref={ref}>
      <torusGeometry args={[radius, 0.012, 16, 200]} />
      <meshBasicMaterial color={color} transparent opacity={0.7} blending={THREE.AdditiveBlending} />
    </mesh>
  );
}

function Sparks({ count = 80, radius = 2.4 }: { count?: number; radius?: number }) {
  const ref = useRef<THREE.Points>(null);
  const positions = (() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = radius * (0.85 + Math.random() * 0.3);
      arr[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      arr[i * 3 + 2] = r * Math.cos(phi);
    }
    return arr;
  })();
  useFrame((state) => {
    const p = ref.current;
    if (!p) return;
    p.rotation.y = state.clock.elapsedTime * 0.12;
    p.rotation.x = state.clock.elapsedTime * 0.05;
  });
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial
        color="#e879f9"
        size={0.05}
        sizeAttenuation
        transparent
        opacity={0.9}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
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

  return (
    <div className={`relative aspect-square w-full max-w-[480px] ${className}`}>
      {/* Soft halo glow behind canvas */}
      <div className="pointer-events-none absolute inset-0 rounded-full bg-gradient-to-br from-aurora-cyan/30 via-aurora-violet/30 to-aurora-magenta/20 blur-3xl" />
      <Canvas
        camera={{ position: [0, 0, 4.2], fov: 50 }}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
        dpr={[1, 2]}
      >
        <ambientLight intensity={0.4} />
        <pointLight position={[3, 2, 4]} intensity={1.2} color="#5eead4" />
        <pointLight position={[-3, -2, 2]} intensity={0.9} color="#e879f9" />
        <pointLight position={[0, 4, -3]} intensity={0.6} color="#a78bfa" />
        <Core intensity={intensity} />
        <HaloRing radius={1.6} speed={0.25} color="#5eead4" tilt={0.6} />
        <HaloRing radius={1.85} speed={-0.18} color="#a78bfa" tilt={1.1} />
        <HaloRing radius={2.1} speed={0.14} color="#e879f9" tilt={1.7} />
        <Sparks count={120} radius={2.4} />
      </Canvas>
    </div>
  );
}
