/**
 * BackendSwitcher — LAN / Tailscale / Custom
 * Persistiert in localStorage, Reload triggert neue WS-Verbindung
 */
import { useState } from 'react'
import { useAgentStore, BackendMode, BACKEND_PRESETS } from '../../stores/agentStore'
import styles from './BackendSwitcher.module.css'

export function BackendSwitcher() {
  const { backendMode, customBackendHost, setBackendMode } = useAgentStore()
  const [open, setOpen] = useState(false)
  const [customInput, setCustomInput] = useState(customBackendHost)

  const modes: { key: BackendMode; label: string; desc: string }[] = [
    { key: 'lan',       label: '🏠 LAN',       desc: '192.168.178.10 — Heimnetz' },
    { key: 'tailscale', label: '🌐 Tailscale',  desc: '100.127.16.62 — überall' },
    { key: 'custom',    label: '⚙️ Custom',     desc: 'eigene IP/Host' },
  ]

  const handleSelect = (mode: BackendMode) => {
    if (mode !== 'custom') {
      setBackendMode(mode)
    }
  }

  const handleCustomSave = () => {
    setBackendMode('custom', customInput)
  }

  return (
    <div className={styles.wrapper}>
      <button className={styles.trigger} onClick={() => setOpen(o => !o)} title="Backend wechseln">
        <span className={styles.dot} data-mode={backendMode} />
        {backendMode === 'lan' ? '🏠' : backendMode === 'tailscale' ? '🌐' : '⚙️'}
      </button>

      {open && (
        <div className={styles.panel}>
          <div className={styles.title}>Backend</div>
          {modes.map(({ key, label, desc }) => (
            <button
              key={key}
              className={`${styles.option} ${backendMode === key ? styles.active : ''}`}
              onClick={() => key !== 'custom' ? handleSelect(key) : undefined}
            >
              <span className={styles.optLabel}>{label}</span>
              <span className={styles.optDesc}>{desc}</span>
              {key === 'custom' && (
                <div className={styles.customRow} onClick={e => e.stopPropagation()}>
                  <input
                    className={styles.customInput}
                    value={customInput}
                    onChange={e => setCustomInput(e.target.value)}
                    placeholder="IP oder Hostname"
                    onKeyDown={e => e.key === 'Enter' && handleCustomSave()}
                  />
                  <button className={styles.saveBtn} onClick={handleCustomSave}>✓</button>
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
