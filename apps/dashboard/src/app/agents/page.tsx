'use client';

import { useState } from 'react';
import {
  CpuChipIcon,
  ServerIcon,
  ClipboardDocumentListIcon,
  ShieldCheckIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

// ─── Types ────────────────────────────────────────────────────────────────────

interface AgentDef {
  id: string;
  name: string;
  emoji: string;
  role: string;
  description: string;
  readZones: string[];
  writeZones: string[];
  specialPermissions?: string;
  status: 'active' | 'scaffold' | 'planned';
}

// ─── Agent Registry ───────────────────────────────────────────────────────────

const AGENTS: AgentDef[] = [
  {
    id: 'kirobi-core',
    name: 'kirobi-core',
    emoji: '🧠',
    role: 'Supervisor & Orchestrator',
    description: 'Zentraler Supervisor. Routet Anfragen an spezialisierte Agenten, synthetisiert Antworten.',
    readZones: ['ALL'],
    writeZones: ['ALL (außer SACRED)'],
    specialPermissions: 'Kann SACRED mit expliziter Genehmigung lesen',
    status: 'active',
  },
  {
    id: 'kirobi-architect',
    name: 'kirobi-architect',
    emoji: '🏗️',
    role: 'System-Architekt',
    description: 'Design-Docs, Architektur-Entscheidungen (ADRs), Service-Graphen, API-Contracts.',
    readZones: ['PUBLIC', 'WORKSPACE'],
    writeZones: ['PUBLIC', 'WORKSPACE'],
    status: 'active',
  },
  {
    id: 'kirobi-coder',
    name: 'kirobi-coder',
    emoji: '💻',
    role: 'Code-Implementierung',
    description: 'Python & TypeScript Code, Tests, Bug-Fixes, Refactoring. FastAPI, asyncpg, pytest.',
    readZones: ['PUBLIC', 'WORKSPACE'],
    writeZones: ['PUBLIC', 'WORKSPACE'],
    status: 'active',
  },
  {
    id: 'kirobi-ops',
    name: 'kirobi-ops',
    emoji: '⚙️',
    role: 'DevOps & Infrastruktur',
    description: 'Docker Compose, Shell-Scripts, CI/CD, Infrastruktur-Konfiguration, Service-Deployment.',
    readZones: ['PUBLIC', 'WORKSPACE', 'QUARANTINE'],
    writeZones: ['PUBLIC', 'WORKSPACE', 'QUARANTINE'],
    status: 'active',
  },
  {
    id: 'kirobi-observer',
    name: 'kirobi-observer',
    emoji: '👁️',
    role: 'Monitoring & Reports',
    description: 'Liest alle Zonen (nur Summary für FAMILY), erstellt Reports und Analysen.',
    readZones: ['ALL (Summary für FAMILY)'],
    writeZones: ['PUBLIC', 'WORKSPACE (Reports)'],
    status: 'active',
  },
  {
    id: 'hermes-extractor',
    name: 'hermes-extractor',
    emoji: '📥',
    role: 'Ingestion & Extraktion',
    description: 'Verarbeitet Rohdaten aus sources/, klassifiziert und extrahiert in extracts/.',
    readZones: ['PUBLIC', 'WORKSPACE', 'QUARANTINE'],
    writeZones: ['PUBLIC', 'WORKSPACE', 'QUARANTINE'],
    status: 'active',
  },
  {
    id: 'samira-heart',
    name: 'samira-heart',
    emoji: '💜',
    role: 'Familien-Mediation',
    description: 'Familien-Kommunikation, persönliche Unterstützung, emotionale Intelligenz.',
    readZones: ['PUBLIC', 'WORKSPACE', 'FAMILY_PRIVATE'],
    writeZones: ['PUBLIC', 'FAMILY_PRIVATE'],
    status: 'active',
  },
  {
    id: 'sineo-creator',
    name: 'sineo-creator',
    emoji: '🎨',
    role: 'Creator Content',
    description: 'Kreative Inhalte für Sineo — Musik, Texte, Ideen, Projekte.',
    readZones: ['PUBLIC', 'WORKSPACE', 'FAMILY (Sineo)'],
    writeZones: ['PUBLIC', 'WORKSPACE', 'FAMILY (Sineo)'],
    status: 'active',
  },
  {
    id: 'research-crew',
    name: 'research-crew',
    emoji: '🔬',
    role: 'Recherche & Analyse',
    description: 'Web-Recherche, Quellen-Analyse, Wissens-Synthese.',
    readZones: ['PUBLIC', 'WORKSPACE'],
    writeZones: ['PUBLIC', 'WORKSPACE'],
    status: 'active',
  },
  {
    id: 'creative-agent',
    name: 'creative-agent',
    emoji: '✨',
    role: 'Kreativ-Assistent',
    description: 'Kreative Inhalte, Texte, Ideen, Brainstorming.',
    readZones: ['PUBLIC', 'WORKSPACE'],
    writeZones: ['PUBLIC', 'WORKSPACE'],
    status: 'active',
  },
  {
    id: 'voice-agent',
    name: 'voice-agent',
    emoji: '🎙️',
    role: 'Voice I/O',
    description: 'Sprach-Ein- und Ausgabe. Whisper STT + Piper TTS.',
    readZones: ['PUBLIC', 'WORKSPACE', 'FAMILY (delegiert)'],
    writeZones: ['NONE'],
    status: 'active',
  },
  {
    id: 'enterprise-agent',
    name: 'enterprise-agent',
    emoji: '💼',
    role: 'Business & Enterprise',
    description: 'Geschäftsprozesse, Client-Daten, Workflows, M365-Integration.',
    readZones: ['PUBLIC', 'WORKSPACE'],
    writeZones: ['PUBLIC', 'WORKSPACE'],
    status: 'planned',
  },
];

// ─── Components ───────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: AgentDef['status'] }) {
  const base = 'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium';
  switch (status) {
    case 'active':
      return <span className={`${base} bg-emerald-500/10 text-emerald-400 border border-emerald-500/20`}>✅ Aktiv</span>;
    case 'scaffold':
      return <span className={`${base} bg-amber-500/10 text-amber-400 border border-amber-500/20`}>🚧 Scaffold</span>;
    default:
      return <span className={`${base} bg-gray-700 text-gray-400 border border-gray-600`}>📄 Geplant</span>;
  }
}

function ZoneBadge({ zone }: { zone: string }) {
  const colorMap: Record<string, string> = {
    'PUBLIC': 'bg-emerald-500/10 text-emerald-400',
    'WORKSPACE': 'bg-kirobi-500/10 text-kirobi-400',
    'FAMILY_PRIVATE': 'bg-violet-500/10 text-violet-400',
    'QUARANTINE': 'bg-red-500/10 text-red-400',
    'SACRED': 'bg-amber-500/10 text-amber-400',
    'ALL': 'bg-gray-600/30 text-gray-300',
    'NONE': 'bg-gray-800 text-gray-600',
  };
  const key = Object.keys(colorMap).find(k => zone.includes(k)) ?? 'ALL';
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-mono ${colorMap[key]}`}>
      {zone}
    </span>
  );
}

function AgentCard({ agent }: { agent: AgentDef }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-2xl">{agent.emoji}</span>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white font-mono">{agent.name}</p>
            <p className="text-xs text-gray-400">{agent.role}</p>
          </div>
        </div>
        <StatusBadge status={agent.status} />
      </div>

      <p className="text-xs text-gray-400 leading-relaxed">{agent.description}</p>

      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
      >
        <ShieldCheckIcon className="w-3.5 h-3.5" />
        {expanded ? 'Berechtigungen ausblenden' : 'Berechtigungen anzeigen'}
      </button>

      {expanded && (
        <div className="space-y-2 pt-2 border-t border-gray-700/50">
          <div>
            <p className="text-xs text-gray-500 mb-1.5">Lesen:</p>
            <div className="flex flex-wrap gap-1">
              {agent.readZones.map(z => <ZoneBadge key={z} zone={z} />)}
            </div>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1.5">Schreiben:</p>
            <div className="flex flex-wrap gap-1">
              {agent.writeZones.map(z => <ZoneBadge key={z} zone={z} />)}
            </div>
          </div>
          {agent.specialPermissions && (
            <p className="text-xs text-amber-400/80 italic">{agent.specialPermissions}</p>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AgentsPage() {
  const [filter, setFilter] = useState<'all' | AgentDef['status']>('all');

  const filtered = filter === 'all' ? AGENTS : AGENTS.filter(a => a.status === filter);
  const counts = {
    all: AGENTS.length,
    active: AGENTS.filter(a => a.status === 'active').length,
    scaffold: AGENTS.filter(a => a.status === 'scaffold').length,
    planned: AGENTS.filter(a => a.status === 'planned').length,
  };

  return (
    <>
      <header className="sticky top-0 z-10 border-b border-gray-700/60 bg-gray-900/80 px-6 py-4 backdrop-blur">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-base font-semibold text-white">Agent Registry</h1>
            <p className="mt-0.5 text-xs text-gray-500">{AGENTS.length} Agenten im OpenDisruption-Ökosystem</p>
          </div>
          <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-xs font-mono text-emerald-400">
            {counts.active} aktiv
          </span>
        </div>
      </header>

      <div className="space-y-6 p-6">
        <div className="flex gap-2 flex-wrap">
          {(['all', 'active', 'scaffold', 'planned'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filter === f
                  ? 'bg-kirobi-600/20 text-kirobi-400 border border-kirobi-600/30'
                  : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600'
              }`}
            >
              {f === 'all' ? 'Alle' : f === 'active' ? 'Aktiv' : f === 'scaffold' ? 'Scaffold' : 'Geplant'}
              <span className="ml-1.5 text-gray-500">{counts[f]}</span>
            </button>
          ))}
        </div>

        <div className="card">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-500">Zonen-Legende</p>
          <div className="flex flex-wrap gap-2">
            {[
              { zone: 'PUBLIC', desc: '🌍 Öffentlich' },
              { zone: 'WORKSPACE', desc: '💼 Intern' },
              { zone: 'FAMILY_PRIVATE', desc: '👨‍👩‍👦 Familie' },
              { zone: 'QUARANTINE', desc: '⚠️ Ungeprüft' },
              { zone: 'SACRED', desc: '🔐 Höchst vertraulich' },
            ].map(({ zone, desc }) => (
              <div key={zone} className="flex items-center gap-1.5">
                <ZoneBadge zone={zone} />
                <span className="text-xs text-gray-500">{desc}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {filtered.map(agent => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      </div>
    </>
  );
}
