/**
 * KirobiAvatar — 3D Talking Head mit Lip-Sync
 * 
 * MVP-Ansatz:
 * - Einfacher 3D-Kopf aus Three.js Geometrien (kein GLB nötig)
 * - Mund-Animation über mouthAmplitude (0.0–1.0) aus Audio-Envelope
 * - State-basierte Animationen: idle, listening, thinking, speaking
 * - Erweiterbar auf Ready Player Me GLB in Phase 2
 */
import { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Environment, MeshDistortMaterial, Sphere } from '@react-three/drei'
import * as THREE from 'three'
import { useAgentStore, AgentState } from '../../stores/agentStore'

// ── Farben pro State ────────────────────────────────────────────────────────
const STATE_COLORS: Record<AgentState, string> = {
  idle:         '#1a1a2e',
  listening:    '#16213e',
  transcribing: '#0f3460',
  thinking:     '#533483',
  speaking:     '#e94560',
  error:        '#ff0000',
}

const STATE_EMISSIVE: Record<AgentState, string> = {
  idle:         '#0a0a14',
  listening:    '#00d4ff',
  transcribing: '#0066ff',
  thinking:     '#9933ff',
  speaking:     '#ff2244',
  error:        '#880000',
}

// ── Inner Glow Sphere ────────────────────────────────────────────────────────
function CoreSphere({ agentState, mouthAmplitude }: { agentState: AgentState, mouthAmplitude: number }) {
  const meshRef = useRef<THREE.Mesh>(null)
  const targetColor = new THREE.Color(STATE_EMISSIVE[agentState])
  const currentColor = useRef(new THREE.Color(STATE_EMISSIVE['idle']))
  const time = useRef(0)

  useFrame((_, delta) => {
    if (!meshRef.current) return
    time.current += delta

    // Farbe smooth interpolieren
    currentColor.current.lerp(targetColor, delta * 4)
    const mat = meshRef.current.material as THREE.MeshStandardMaterial
    mat.emissive.copy(currentColor.current)

    // Idle: sanftes Pulsieren
    if (agentState === 'idle') {
      meshRef.current.scale.setScalar(1 + Math.sin(time.current * 1.2) * 0.02)
    }
    // Listening: schnelleres Pulsieren
    else if (agentState === 'listening') {
      meshRef.current.scale.setScalar(1 + Math.sin(time.current * 4) * 0.04)
    }
    // Thinking: langsame Rotation
    else if (agentState === 'thinking') {
      meshRef.current.rotation.y += delta * 0.8
      meshRef.current.scale.setScalar(1 + Math.sin(time.current * 0.5) * 0.015)
    }
    // Speaking: Amplitude-basierte Scale
    else if (agentState === 'speaking') {
      const target = 1 + mouthAmplitude * 0.12
      const cur = meshRef.current.scale.x
      meshRef.current.scale.setScalar(cur + (target - cur) * 0.3)
    }
    else {
      meshRef.current.scale.setScalar(1)
    }
  })

  return (
    <Sphere ref={meshRef} args={[1, 64, 64]}>
      <meshStandardMaterial
        color={STATE_COLORS[agentState]}
        emissive={STATE_EMISSIVE[agentState]}
        emissiveIntensity={0.8}
        roughness={0.2}
        metalness={0.6}
      />
    </Sphere>
  )
}

// ── Mouth Ring ───────────────────────────────────────────────────────────────
function MouthRing({ amplitude, agentState }: { amplitude: number, agentState: AgentState }) {
  const ringRef = useRef<THREE.Mesh>(null)
  const innerRef = useRef<THREE.Mesh>(null)
  const time = useRef(0)

  useFrame((_, delta) => {
    if (!ringRef.current || !innerRef.current) return
    time.current += delta

    const isSpeaking = agentState === 'speaking'
    const isListening = agentState === 'listening'

    // Äußerer Ring
    const outerTarget = isSpeaking
      ? 0.15 + amplitude * 0.25
      : isListening
        ? 0.12 + Math.sin(time.current * 6) * 0.04
        : 0.1
    const cur = ringRef.current.scale.y
    ringRef.current.scale.y = cur + (outerTarget - cur) * 0.4
    ringRef.current.scale.x = ringRef.current.scale.y * 1.6  // Breiter als hoch

    // Innere Öffnung
    const innerTarget = isSpeaking ? amplitude * 0.15 : 0
    innerRef.current.scale.setScalar(innerTarget + 0.01)
  })

  return (
    <group position={[0, -0.3, 0.85]}>
      {/* Äußerer Mund-Ring */}
      <mesh ref={ringRef}>
        <torusGeometry args={[0.22, 0.05, 8, 32]} />
        <meshStandardMaterial
          color={agentState === 'speaking' ? '#ff4466' : '#444466'}
          emissive={agentState === 'speaking' ? '#ff2244' : '#222244'}
          emissiveIntensity={agentState === 'speaking' ? amplitude * 2 : 0.2}
        />
      </mesh>
      {/* Innere Dunkel-Füllung (simuliert offenen Mund) */}
      <mesh ref={innerRef} position={[0, 0, 0.02]}>
        <circleGeometry args={[0.2, 32]} />
        <meshBasicMaterial color="#000010" transparent opacity={0.9} />
      </mesh>
    </group>
  )
}

// ── Eye Orbs ──────────────────────────────────────────────────────────────────
function Eyes({ agentState }: { agentState: AgentState }) {
  const leftRef = useRef<THREE.Mesh>(null)
  const rightRef = useRef<THREE.Mesh>(null)
  const time = useRef(0)
  const blinkTimer = useRef(Math.random() * 4 + 2)

  useFrame((_, delta) => {
    time.current += delta
    blinkTimer.current -= delta

    const isThinking = agentState === 'thinking'
    const isListening = agentState === 'listening'

    // Blinzeln
    let scaleY = 1
    if (blinkTimer.current <= 0) {
      blinkTimer.current = Math.random() * 4 + 2
      scaleY = 0.05
    }

    // Thinking: Augen leuchten violet
    const emissive = isThinking ? '#9933ff'
      : isListening ? '#00d4ff'
      : '#003366'

    ;[leftRef.current, rightRef.current].forEach(eye => {
      if (!eye) return
      eye.scale.y += (scaleY - eye.scale.y) * 0.3
      const mat = eye.material as THREE.MeshStandardMaterial
      mat.emissive.set(emissive)
      mat.emissiveIntensity = isThinking
        ? 1 + Math.sin(time.current * 3) * 0.5
        : isListening ? 1.5 : 0.6
    })
  })

  const eyeMaterial = (
    <meshStandardMaterial
      color="#001133"
      emissive="#003366"
      emissiveIntensity={0.6}
      roughness={0.1}
      metalness={0.8}
    />
  )

  return (
    <group>
      <mesh ref={leftRef} position={[-0.3, 0.25, 0.9]}>
        <sphereGeometry args={[0.12, 16, 16]} />
        {eyeMaterial}
      </mesh>
      <mesh ref={rightRef} position={[0.3, 0.25, 0.9]}>
        <sphereGeometry args={[0.12, 16, 16]} />
        {eyeMaterial}
      </mesh>
    </group>
  )
}

// ── Ambient Particles (Speaking) ─────────────────────────────────────────────
function AmbientRing({ agentState }: { agentState: AgentState }) {
  const ref = useRef<THREE.Mesh>(null)
  useFrame((_, delta) => {
    if (!ref.current) return
    ref.current.rotation.z += delta * (agentState === 'speaking' ? 1.5 : 0.3)
    ref.current.rotation.x += delta * 0.2
    const target = agentState !== 'idle' ? 1 : 0.3
    ref.current.material = ref.current.material as THREE.MeshStandardMaterial
    const mat = ref.current.material as THREE.MeshStandardMaterial
    mat.opacity += (target - mat.opacity) * delta * 2
  })
  return (
    <mesh ref={ref} scale={[1.5, 1.5, 1.5]}>
      <torusGeometry args={[1, 0.02, 4, 64]} />
      <meshStandardMaterial
        color={STATE_EMISSIVE[agentState]}
        emissive={STATE_EMISSIVE[agentState]}
        emissiveIntensity={2}
        transparent
        opacity={0.4}
        wireframe
      />
    </mesh>
  )
}

// ── Distort Shell ─────────────────────────────────────────────────────────────
function DistortShell({ agentState, amplitude }: { agentState: AgentState, amplitude: number }) {
  const ref = useRef<any>(null)
  const time = useRef(0)

  useFrame((_, delta) => {
    time.current += delta
    if (!ref.current) return

    const distortTarget = agentState === 'speaking' ? 0.2 + amplitude * 0.4
      : agentState === 'thinking' ? 0.15 + Math.sin(time.current) * 0.05
      : agentState === 'listening' ? 0.08
      : 0.04

    ref.current.distort += (distortTarget - ref.current.distort) * delta * 3
  })

  return (
    <Sphere args={[1.15, 64, 64]}>
      <MeshDistortMaterial
        ref={ref}
        color={STATE_COLORS[agentState]}
        emissive={STATE_EMISSIVE[agentState]}
        emissiveIntensity={0.3}
        distort={0.04}
        speed={agentState === 'thinking' ? 3 : 1}
        roughness={0.6}
        metalness={0.2}
        transparent
        opacity={0.35}
      />
    </Sphere>
  )
}

// ── Avatar Head (Composite) ──────────────────────────────────────────────────
function AvatarHead() {
  const agentState = useAgentStore(s => s.agentState)
  const mouthAmplitude = useAgentStore(s => s.mouthAmplitude)
  const groupRef = useRef<THREE.Group>(null)
  const time = useRef(0)

  useFrame((_, delta) => {
    if (!groupRef.current) return
    time.current += delta

    // Sanfte Kopfbewegung je nach State
    if (groupRef.current) {
      const targetX = Math.sin(time.current * 0.4) * 0.05
      const targetY = Math.cos(time.current * 0.3) * 0.03
      groupRef.current.rotation.x += (targetX - groupRef.current.rotation.x) * delta * 2
      groupRef.current.rotation.y += (targetY - groupRef.current.rotation.y) * delta * 2
    }
  })

  return (
    <group ref={groupRef}>
      <CoreSphere agentState={agentState} mouthAmplitude={mouthAmplitude} />
      <DistortShell agentState={agentState} amplitude={mouthAmplitude} />
      <Eyes agentState={agentState} />
      <MouthRing amplitude={mouthAmplitude} agentState={agentState} />
      <AmbientRing agentState={agentState} />
    </group>
  )
}

// ── Main Avatar Canvas ────────────────────────────────────────────────────────
export function KirobiAvatar() {
  return (
    <Canvas
      camera={{ position: [0, 0, 4], fov: 40 }}
      style={{ background: 'transparent' }}
      dpr={[1, 2]}
    >
      <ambientLight intensity={0.3} />
      <pointLight position={[5, 5, 5]} intensity={1} color="#ffffff" />
      <pointLight position={[-5, -3, 3]} intensity={0.5} color="#4444ff" />
      <pointLight position={[0, -5, 2]} intensity={0.3} color="#ff2244" />
      <AvatarHead />
      <Environment preset="night" />
    </Canvas>
  )
}
