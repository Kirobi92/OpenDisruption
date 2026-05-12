'use client';

import { motion } from 'framer-motion';
import { Plus, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { BottomNav } from '@/components/layout/BottomNav';
import { Header } from '@/components/layout/Header';
import { useRequireAuth } from '@/lib/auth';
import { apiClient } from '@/lib/api';

type BrainTab = 'graph' | 'notes' | 'search';
type NodeType = 'concept' | 'chat' | 'document' | 'goal' | 'memory';

type GraphNode = {
  id: string;
  label: string;
  type: NodeType;
  description: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
};

type Note = {
  id: string;
  title: string;
  excerpt: string;
  content: string;
  tags: string[];
  date: string;
};

type SearchResult = {
  id: string;
  title: string;
  excerpt: string;
  score: number;
};

const graphTemplate: Omit<GraphNode, 'x' | 'y' | 'vx' | 'vy'>[] = [
  { id: 'vision', label: 'Vision', type: 'concept', description: 'Langfristiger Nordstern für Entscheidungen.' },
  { id: 'project-alpha', label: 'Projekt Alpha', type: 'goal', description: 'Aktuelles Fokusprojekt mit hoher Bedeutung.' },
  { id: 'learning', label: 'Lernen', type: 'concept', description: 'Wachstum durch reflektierte Praxis.' },
  { id: 'family-notes', label: 'Familiennotizen', type: 'memory', description: 'Wärme, Rituale und persönliche Erinnerungen.' },
  { id: 'creative-lab', label: 'Creative Lab', type: 'concept', description: 'Raum für Ideen, Medien und neue Formate.' },
  { id: 'chat-focus', label: 'Fokus-Chat', type: 'chat', description: 'Gespräch zu Klarheit und Prioritäten.' },
  { id: 'chat-growth', label: 'Growth-Chat', type: 'chat', description: 'Reflexion über Entwicklung und Gewohnheiten.' },
  { id: 'doc-strategy', label: 'Strategie-Dokument', type: 'document', description: 'Strategische Leitlinien und Prioritäten.' },
  { id: 'doc-notes', label: 'Ideenboard', type: 'document', description: 'Lose Gedanken und Forschungsfunde.' },
  { id: 'goal-health', label: 'Gesundheit', type: 'goal', description: 'Energie, Bewegung und Regeneration.' },
  { id: 'goal-language', label: 'Deutsch', type: 'goal', description: 'Sprachentwicklung durch Mikro-Lernen.' },
  { id: 'memory-flow', label: 'Flow-Moment', type: 'memory', description: 'Ein gespeicherter Moment hoher Präsenz.' },
  { id: 'memory-gratitude', label: 'Dankbarkeit', type: 'memory', description: 'Erinnerung an kleine, bedeutsame Schritte.' },
  { id: 'doc-research', label: 'Research Stack', type: 'document', description: 'Verdichtete Erkenntnisse aus Recherche.' },
  { id: 'chat-media', label: 'Media-Session', type: 'chat', description: 'Gespräch über Musik, Bilder und Narrative.' },
];

const edges = [
  ['vision', 'project-alpha'],
  ['vision', 'learning'],
  ['creative-lab', 'chat-media'],
  ['learning', 'goal-language'],
  ['project-alpha', 'doc-strategy'],
  ['doc-strategy', 'chat-focus'],
  ['chat-focus', 'goal-health'],
  ['family-notes', 'memory-gratitude'],
  ['memory-flow', 'creative-lab'],
  ['doc-research', 'learning'],
  ['doc-notes', 'creative-lab'],
  ['chat-growth', 'goal-health'],
  ['chat-growth', 'goal-language'],
  ['chat-media', 'doc-notes'],
  ['doc-research', 'project-alpha'],
];

const nodeColors: Record<NodeType, string> = {
  concept: '#a78bfa',
  chat: '#22d3ee',
  document: '#fbbf24',
  goal: '#e879f9',
  memory: '#5eead4',
};

const initialNotes: Note[] = [
  {
    id: 'note-1',
    title: 'Morgenroutine verfeinern',
    excerpt: 'Mehr Ruhe im Start des Tages durch eine bewusste Reihenfolge.',
    content: 'Wasser, Atemzug, Fokusfrage, dann erst Mails.',
    tags: ['Routinen', 'Fokus'],
    date: '2026-05-10',
  },
  {
    id: 'note-2',
    title: 'Idee für Samira-Abend',
    excerpt: 'Licht, Musik und ein ruhiges Gesprächsritual.',
    content: 'Kleine Fragenkarten und eine gemeinsame Playlist.',
    tags: ['Familie', 'Verbindung'],
    date: '2026-05-09',
  },
  {
    id: 'note-3',
    title: 'Sineo Kreativ-Loop',
    excerpt: 'Malen, Sound und Story in einer Session verbinden.',
    content: 'Erst Farbpalette wählen, dann Ambient-Sound, dann Geschichte.',
    tags: ['Kreativität', 'Sineo'],
    date: '2026-05-08',
  },
];

function createInitialNodes() {
  return graphTemplate.map((node, index) => ({
    ...node,
    x: 140 + (index % 5) * 140,
    y: 110 + Math.floor(index / 5) * 120,
    vx: 0,
    vy: 0,
  }));
}

export default function BrainPage() {
  const { isLoading, isAuthenticated } = useRequireAuth();
  const [activeTab, setActiveTab] = useState<BrainTab>('graph');
  const [nodes, setNodes] = useState<GraphNode[]>(createInitialNodes);
  const [selectedNodeId, setSelectedNodeId] = useState<string>('vision');
  const [notes, setNotes] = useState<Note[]>(initialNotes);
  const [noteModalOpen, setNoteModalOpen] = useState(false);
  const [noteDraft, setNoteDraft] = useState({ title: '', content: '', tags: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    let frame = 0;

    const tick = () => {
      setNodes((current) => {
        const next = current.map((node) => ({ ...node }));

        for (let i = 0; i < next.length; i += 1) {
          for (let j = i + 1; j < next.length; j += 1) {
            const a = next[i];
            const b = next[j];
            const dx = b.x - a.x;
            const dy = b.y - a.y;
            const distance = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
            const force = 2200 / (distance * distance);
            const fx = (dx / distance) * force;
            const fy = (dy / distance) * force;

            a.vx -= fx;
            a.vy -= fy;
            b.vx += fx;
            b.vy += fy;
          }
        }

        edges.forEach(([source, target]) => {
          const a = next.find((node) => node.id === source);
          const b = next.find((node) => node.id === target);
          if (!a || !b) {
            return;
          }

          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const distance = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
          const desired = 140;
          const pull = (distance - desired) * 0.0018;
          const fx = dx * pull;
          const fy = dy * pull;

          a.vx += fx;
          a.vy += fy;
          b.vx -= fx;
          b.vy -= fy;
        });

        next.forEach((node) => {
          node.vx *= 0.92;
          node.vy *= 0.92;
          node.x = Math.min(820, Math.max(60, node.x + node.vx));
          node.y = Math.min(460, Math.max(60, node.y + node.vy));
        });

        return next;
      });

      frame = window.requestAnimationFrame(tick);
    };

    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, []);

  const selectedNode = useMemo(() => nodes.find((node) => node.id === selectedNodeId) ?? nodes[0], [nodes, selectedNodeId]);
  const conceptCount = graphTemplate.filter((node) => node.type === 'concept').length;
  const documentCount = graphTemplate.filter((node) => node.type === 'document').length;

  const handleCreateNote = () => {
    if (!noteDraft.title.trim() || !noteDraft.content.trim()) {
      return;
    }

    const tags = noteDraft.tags
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean);

    setNotes((current) => [
      {
        id: `note-${Date.now()}`,
        title: noteDraft.title.trim(),
        excerpt: noteDraft.content.trim().slice(0, 96),
        content: noteDraft.content.trim(),
        tags,
        date: new Date().toISOString().slice(0, 10),
      },
      ...current,
    ]);
    setNoteDraft({ title: '', content: '', tags: '' });
    setNoteModalOpen(false);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await apiClient.post('/api/proxy/retrieval/search', { query: searchQuery.trim() });
      const payload = response.data?.results ?? response.data?.items ?? response.data ?? [];
      const normalized = Array.isArray(payload)
        ? payload.map((item, index) => {
            const value = (item ?? {}) as Record<string, unknown>;
            return {
              id: String(value.id ?? `result-${index}`),
              title: String(value.title ?? value.name ?? `Treffer ${index + 1}`),
              excerpt: String(value.excerpt ?? value.content ?? value.text ?? ''),
              score: Number(value.score ?? value.similarity ?? 0.82),
            } satisfies SearchResult;
          })
        : [];
      setSearchResults(normalized);
    } catch {
      setSearchResults(
        notes
          .filter((note) => `${note.title} ${note.content}`.toLowerCase().includes(searchQuery.toLowerCase()))
          .map((note, index) => ({
            id: `${note.id}-${index}`,
            title: note.title,
            excerpt: note.excerpt,
            score: 0.78,
          })),
      );
    } finally {
      setIsSearching(false);
    }
  };

  if (isLoading || !isAuthenticated) {
    return <div className="min-h-screen bg-void" />;
  }

  return (
    <div className="min-h-screen pb-24 md:pb-8">
      <Header title="Gehirn" />
      <main className="mx-auto max-w-7xl px-4 pb-10 pt-20 md:px-6">
        <motion.section initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-[2rem] p-6 shadow-card">
          <div className="grid gap-4 md:grid-cols-4">
            {[
              ['Konzepte', conceptCount],
              ['Dokumente', documentCount],
              ['Verbindungen', edges.length],
              ['Notizen', notes.length],
            ].map(([label, value]) => (
              <div key={label} className="rounded-3xl border border-white/10 bg-white/5 p-4">
                <div className="text-sm text-white/55">{label}</div>
                <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
              </div>
            ))}
          </div>
        </motion.section>

        <div className="mt-8 flex flex-wrap gap-3">
          {[
            ['graph', 'Wissensgraph'],
            ['notes', 'Notizen'],
            ['search', 'Suche'],
          ].map(([tab, label]) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab as BrainTab)}
              className={`rounded-full px-5 py-2.5 text-sm transition ${
                activeTab === tab
                  ? 'bg-gradient-to-r from-kirobi-400 to-aurora-violet font-semibold text-void shadow-glow-cyan'
                  : 'border border-white/10 bg-white/5 text-white/65 hover:text-white'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {activeTab === 'graph' ? (
          <section className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <div className="glass overflow-hidden rounded-[2rem] p-4 shadow-card">
              <svg viewBox="0 0 880 520" className="h-[520px] w-full">
                {edges.map(([source, target]) => {
                  const sourceNode = nodes.find((node) => node.id === source);
                  const targetNode = nodes.find((node) => node.id === target);
                  if (!sourceNode || !targetNode) {
                    return null;
                  }
                  return (
                    <line
                      key={`${source}-${target}`}
                      x1={sourceNode.x}
                      y1={sourceNode.y}
                      x2={targetNode.x}
                      y2={targetNode.y}
                      stroke="rgba(255,255,255,0.18)"
                      strokeWidth="1.5"
                    />
                  );
                })}
                {nodes.map((node) => (
                  <g key={node.id} transform={`translate(${node.x}, ${node.y})`} onClick={() => setSelectedNodeId(node.id)} className="cursor-pointer">
                    <circle r="18" fill={nodeColors[node.type]} opacity={selectedNodeId === node.id ? 1 : 0.8} />
                    <circle r="28" fill={nodeColors[node.type]} opacity={selectedNodeId === node.id ? 0.16 : 0.06} />
                    <text x="0" y="40" fill="white" textAnchor="middle" fontSize="12">
                      {node.label}
                    </text>
                  </g>
                ))}
              </svg>
            </div>
            <div className="glass rounded-[2rem] p-6 shadow-card">
              <div className="text-sm uppercase tracking-[0.24em] text-white/45">Node Details</div>
              <div className="mt-5 rounded-3xl border border-white/10 bg-white/5 p-5">
                <div className="inline-flex rounded-full px-3 py-1 text-xs font-medium uppercase tracking-[0.22em] text-white" style={{ backgroundColor: `${nodeColors[selectedNode.type]}22` }}>
                  {selectedNode.type}
                </div>
                <h2 className="mt-4 text-2xl font-semibold">{selectedNode.label}</h2>
                <p className="mt-4 text-sm leading-7 text-white/65">{selectedNode.description}</p>
                <div className="mt-6 space-y-2 text-sm text-white/55">
                  <div>Verknüpfungen: {edges.filter(([source, target]) => source === selectedNode.id || target === selectedNode.id).length}</div>
                  <div>Cluster: Persönlicher Wissensraum</div>
                  <div>Status: Aktiv vernetzt</div>
                </div>
              </div>
            </div>
          </section>
        ) : null}

        {activeTab === 'notes' ? (
          <section className="mt-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Notizen</h2>
              <button
                type="button"
                onClick={() => setNoteModalOpen(true)}
                className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet px-5 py-2.5 font-semibold text-void shadow-glow-cyan"
              >
                <Plus className="h-4 w-4" />
                Neue Notiz
              </button>
            </div>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {notes.map((note) => (
                <div key={note.id} className="glass rounded-3xl p-5 shadow-card">
                  <div className="text-xs uppercase tracking-[0.22em] text-white/40">{note.date}</div>
                  <div className="mt-3 text-xl font-semibold">{note.title}</div>
                  <p className="mt-3 text-sm leading-7 text-white/65">{note.excerpt}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {note.tags.map((tag) => (
                      <span key={tag} className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/60">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {activeTab === 'search' ? (
          <section className="mt-6 glass rounded-[2rem] p-6 shadow-card">
            <div className="flex flex-col gap-3 md:flex-row">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/35" />
                <input
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Suche in deinem Wissensraum"
                  className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 pl-11 pr-4 outline-none focus:border-aurora-cyan/35"
                />
              </div>
              <button
                type="button"
                onClick={() => void handleSearch()}
                className="rounded-2xl bg-gradient-to-r from-kirobi-400 to-aurora-violet px-5 py-3 font-semibold text-void shadow-glow-cyan"
              >
                {isSearching ? 'Suche läuft...' : 'Suchen'}
              </button>
            </div>
            <div className="mt-6 space-y-4">
              {searchResults.length > 0 ? (
                searchResults.map((result) => (
                  <div key={result.id} className="rounded-3xl border border-white/10 bg-white/5 p-5">
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="text-lg font-semibold">{result.title}</h3>
                      <span className="rounded-full border border-aurora-cyan/20 bg-aurora-cyan/10 px-3 py-1 text-xs text-aurora-cyan">
                        {(result.score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-7 text-white/65">{result.excerpt}</p>
                  </div>
                ))
              ) : (
                <div className="rounded-3xl border border-dashed border-white/10 p-6 text-sm text-white/50">
                  Gib eine Suchanfrage ein und finde relevante Erinnerungen, Dokumente oder Gespräche.
                </div>
              )}
            </div>
          </section>
        ) : null}
      </main>

      {noteModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-xl rounded-[2rem] border border-white/10 bg-void-deep p-6 shadow-card">
            <h3 className="text-2xl font-semibold">Neue Notiz</h3>
            <div className="mt-5 space-y-4">
              <input
                value={noteDraft.title}
                onChange={(event) => setNoteDraft((current) => ({ ...current, title: event.target.value }))}
                placeholder="Titel"
                className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 px-4 outline-none"
              />
              <textarea
                value={noteDraft.content}
                onChange={(event) => setNoteDraft((current) => ({ ...current, content: event.target.value }))}
                placeholder="Inhalt"
                className="min-h-[160px] w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 outline-none"
              />
              <input
                value={noteDraft.tags}
                onChange={(event) => setNoteDraft((current) => ({ ...current, tags: event.target.value }))}
                placeholder="Tags, durch Komma getrennt"
                className="h-12 w-full rounded-2xl border border-white/10 bg-white/5 px-4 outline-none"
              />
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button type="button" onClick={() => setNoteModalOpen(false)} className="rounded-full border border-white/10 px-5 py-2.5 text-white/65">
                Abbrechen
              </button>
              <button type="button" onClick={handleCreateNote} className="rounded-full bg-gradient-to-r from-kirobi-400 to-aurora-violet px-5 py-2.5 font-semibold text-void shadow-glow-cyan">
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
