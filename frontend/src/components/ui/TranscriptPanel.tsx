/**
 * TranscriptPanel — Live-Transkript + Agent-Antwort
 */
import { useEffect, useRef } from 'react'
import { useAgentStore } from '../../stores/agentStore'
import styles from './TranscriptPanel.module.css'

export function TranscriptPanel() {
  const { userTranscript, userTranscriptFinal, agentText, agentState } = useAgentStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [agentText, userTranscript])

  const showUser = userTranscript || userTranscriptFinal
  const showAgent = agentText

  if (!showUser && !showAgent) {
    return (
      <div className={styles.panel}>
        <div className={styles.empty}>
          <span>Sag etwas, um zu beginnen...</span>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.panel}>
      {showUser && (
        <div className={styles.message + ' ' + styles.user}>
          <span className={styles.label}>Du</span>
          <p className={userTranscriptFinal ? styles.final : styles.partial}>
            {userTranscript}
          </p>
        </div>
      )}
      {showAgent && (
        <div className={styles.message + ' ' + styles.agent}>
          <span className={styles.label}>Kirobi</span>
          <p className={agentState === 'speaking' ? styles.streaming : ''}>
            {agentText}
            {agentState === 'speaking' && <span className={styles.cursor}>▋</span>}
          </p>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
