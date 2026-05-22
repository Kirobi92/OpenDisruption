/**
 * StatusBar — Verbindungsstatus + Agent-State + Provider-Info
 */
import { useAgentStore, AgentState, ConnectionState } from '../../stores/agentStore'
import styles from './StatusBar.module.css'

const STATE_LABEL: Record<AgentState, string> = {
  idle:         '● Bereit',
  listening:    '🎙 Höre zu...',
  transcribing: '⏳ Transkribiere...',
  thinking:     '🧠 Denke...',
  speaking:     '🔊 Spricht...',
  error:        '⚠ Fehler',
}

const CONN_LABEL: Record<ConnectionState, string> = {
  disconnected: '○ Getrennt',
  connecting:   '◌ Verbinde...',
  connected:    '● Verbunden',
  error:        '✕ Verbindungsfehler',
}

const CONN_COLOR: Record<ConnectionState, string> = {
  disconnected: '#666',
  connecting:   '#ffaa00',
  connected:    '#00ff88',
  error:        '#ff4444',
}

export function StatusBar() {
  const { connectionState, agentState, sttProvider, llmProvider, ttsProvider } = useAgentStore()

  return (
    <div className={styles.statusBar}>
      <div className={styles.left}>
        <span
          className={styles.connection}
          style={{ color: CONN_COLOR[connectionState] }}
        >
          {CONN_LABEL[connectionState]}
        </span>
        <span className={styles.divider}>|</span>
        <span className={styles.agentState}>
          {STATE_LABEL[agentState]}
        </span>
      </div>
      <div className={styles.right}>
        <span className={styles.provider}>STT: {sttProvider}</span>
        <span className={styles.provider}>LLM: {llmProvider}</span>
        <span className={styles.provider}>TTS: {ttsProvider}</span>
      </div>
    </div>
  )
}
