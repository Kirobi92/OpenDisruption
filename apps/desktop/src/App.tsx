/**
 * Kirobi Family — Desktop App (Tauri + React)
 *
 * Sidebar-Navigation: Dashboard, Chat, Einstellungen
 * Verbindet sich mit dem lokalen Kirobi-Stack via HTTP.
 */

import React, { useEffect, useState } from 'react';
import axios from 'axios';

// ─── Konfiguration ────────────────────────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_URL ?? 'http://kirobi.local/api';

// ─── Typen ────────────────────────────────────────────────────────────────────
type View = 'dashboard' | 'chat' | 'einstellungen';

interface HealthStatus {
  status: 'ok' | 'error' | 'loading';
  latency?: number;
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
function Dashboard() {
  const [health, setHealth] = useState<HealthStatus>({ status: 'loading' });

  useEffect(() => {
    const check = async () => {
      const start = Date.now();
      try {
        await axios.get(`${API_BASE}/health`, { timeout: 5000 });
        setHealth({ status: 'ok', latency: Date.now() - start });
      } catch {
        setHealth({ status: 'error' });
      }
    };
    check();
  }, []);

  return (
    <div className="view">
      <h1>🏠 Dashboard</h1>
      <p className="subtitle">Willkommen bei Kirobi — deinem Familien-Assistenten.</p>

      <div className="card-grid">
        <div className="card">
          <div className="card-icon">📡</div>
          <div className="card-body">
            <div className="card-label">API-Status</div>
            <div
              className={`card-value status-${health.status}`}
            >
              {health.status === 'loading' && 'Prüfe...'}
              {health.status === 'ok' && `Erreichbar (${health.latency}ms)`}
              {health.status === 'error' && 'Nicht erreichbar'}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-icon">🌐</div>
          <div className="card-body">
            <div className="card-label">Endpunkt</div>
            <div className="card-value mono">{API_BASE}</div>
          </div>
        </div>

        <div className="card">
          <div className="card-icon">🖥️</div>
          <div className="card-body">
            <div className="card-label">Plattform</div>
            <div className="card-value">Tauri Desktop</div>
          </div>
        </div>

        <div className="card">
          <div className="card-icon">🔔</div>
          <div className="card-body">
            <div className="card-label">System-Tray</div>
            <div className="card-value">
              Kirobi läuft im Hintergrund — Tray-Icon aktiv
            </div>
          </div>
        </div>
      </div>

      <div className="hint">
        💡 Kirobi minimiert sich in den System-Tray. Klicke das Tray-Icon, um
        die App wieder zu öffnen.
      </div>
    </div>
  );
}

// ─── Chat ─────────────────────────────────────────────────────────────────────
function Chat() {
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([
    { role: 'assistant', text: 'Hallo! Wie kann ich dir helfen?' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const res = await axios.post(
        `${API_BASE}/chat`,
        { message: userMsg },
        { timeout: 30000 }
      );
      const reply: string =
        res.data?.response ?? res.data?.message ?? 'Keine Antwort erhalten.';
      setMessages((prev) => [...prev, { role: 'assistant', text: reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: '⚠️ Verbindungsfehler zum Kirobi-Stack.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="view chat-view">
      <h1>💬 Chat</h1>
      <div className="message-list">
        {messages.map((msg, i) => (
          <div key={i} className={`bubble bubble-${msg.role}`}>
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className="bubble bubble-assistant typing">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </div>
        )}
      </div>
      <div className="input-row">
        <input
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Nachricht eingeben… (Enter zum Senden)"
          disabled={loading}
        />
        <button className="send-btn" onClick={send} disabled={loading}>
          ➤
        </button>
      </div>
    </div>
  );
}

// ─── Einstellungen ────────────────────────────────────────────────────────────
function Einstellungen() {
  const [apiUrl, setApiUrl] = useState(API_BASE);

  return (
    <div className="view">
      <h1>⚙️ Einstellungen</h1>

      <div className="settings-group">
        <label className="settings-label">API-URL</label>
        <input
          className="settings-input"
          value={apiUrl}
          onChange={(e) => setApiUrl(e.target.value)}
          placeholder="http://kirobi.local/api"
        />
        <p className="settings-hint">
          Standard: <code>http://kirobi.local/api</code> — via Caddy geroutet.
          Setze <code>VITE_API_URL</code> in <code>.env</code> für persistente
          Konfiguration.
        </p>
      </div>

      <div className="settings-group">
        <label className="settings-label">System-Tray</label>
        <p className="settings-hint">
          Kirobi minimiert sich beim Schließen in den System-Tray und bleibt im
          Hintergrund aktiv. Konfigurierbar in{' '}
          <code>src-tauri/tauri.conf.json</code>.
        </p>
      </div>

      <div className="settings-group">
        <label className="settings-label">Version</label>
        <p className="settings-hint">Kirobi Desktop 1.0.0 — Tauri + React 18</p>
      </div>
    </div>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
const NAV_ITEMS: { key: View; icon: string; label: string }[] = [
  { key: 'dashboard', icon: '🏠', label: 'Dashboard' },
  { key: 'chat', icon: '💬', label: 'Chat' },
  { key: 'einstellungen', icon: '⚙️', label: 'Einstellungen' },
];

// ─── Root App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [activeView, setActiveView] = useState<View>('dashboard');

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">🤖</span>
          <span className="logo-text">Kirobi</span>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              className={`nav-item ${activeView === item.key ? 'active' : ''}`}
              onClick={() => setActiveView(item.key)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="tray-hint">🔔 Im Tray aktiv</span>
        </div>
      </aside>

      {/* Hauptbereich */}
      <main className="main">
        {activeView === 'dashboard' && <Dashboard />}
        {activeView === 'chat' && <Chat />}
        {activeView === 'einstellungen' && <Einstellungen />}
      </main>
    </div>
  );
}
