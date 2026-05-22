/**
 * ChatModule — Text-Chat mit Paperclip-Agenten
 *
 * - Lädt alle Agenten aus Paperclip (Port 3100)
 * - Auswahl via Dropdown oder Tap
 * - Text-Nachrichten via SSE-Stream an Kirobi-Backend /api/agents/chat
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { getRuntimeBackendHost } from '../../stores/agentStore'
import './ChatModule.css'

const PAPERCLIP_COMPANY = '32a3cd4e-b59f-470b-bddb-aeb288ecfb21'

type PaperclipAgent = {
  id: string
  name: string
  role?: string
  title?: string
  status: string
}

type ChatMessage = {
  id: string
  role: 'user' | 'agent'
  content: string
  ts: number
  streaming?: boolean
}

function paperclipBase(): string {
  const host = getRuntimeBackendHost()
  return `http://${host}:3100`
}

function backendBase(): string {
  const host = getRuntimeBackendHost()
  return `http://${host}:8765`
}

const STATUS_EMOJI: Record<string, string> = {
  idle: '🟢',
  error: '🔴',
  running: '🔵',
  paused: '⏸️',
}

export default function ChatModule() {
  const [agents, setAgents] = useState<PaperclipAgent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<PaperclipAgent | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(true)
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAgentPicker, setShowAgentPicker] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const streamingIdRef = useRef<string | null>(null)

  // Agenten aus Paperclip laden
  const loadAgents = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${paperclipBase()}/api/companies/${PAPERCLIP_COMPANY}/agents`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: PaperclipAgent[] = await res.json()
      setAgents(data)
      // Standard: Kirobi (CEO) vorauswählen
      const kirobi = data.find(a => a.name.toLowerCase().includes('kirobi') || a.name.toLowerCase().includes('ceo'))
      if (kirobi) setSelectedAgent(kirobi)
      else if (data.length > 0) setSelectedAgent(data[0])
    } catch (e) {
      setError(`Paperclip nicht erreichbar: ${e}`)
    }
    setLoading(false)
  }, [])

  useEffect(() => { loadAgents() }, [loadAgents])

  // Auto-Scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Nachricht senden
  const sendMessage = useCallback(async () => {
    const text = inputText.trim()
    if (!text || !selectedAgent || streaming) return

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      ts: Date.now(),
    }
    setMessages(prev => [...prev, userMsg])
    setInputText('')
    setStreaming(true)
    setError(null)

    const agentMsgId = crypto.randomUUID()
    streamingIdRef.current = agentMsgId
    setMessages(prev => [...prev, {
      id: agentMsgId,
      role: 'agent',
      content: '',
      ts: Date.now(),
      streaming: true,
    }])

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const res = await fetch(`${backendBase()}/api/agents/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: selectedAgent.id,
          agent_name: selectedAgent.name,
          message: text,
        }),
        signal: controller.signal,
      })

      if (!res.ok) {
        const err = await res.text()
        throw new Error(`Backend ${res.status}: ${err}`)
      }

      const reader = res.body?.getReader()
      if (!reader) throw new Error('Kein Stream')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const raw = line.slice(6)
            if (raw === '[DONE]') break
            try {
              const chunk = JSON.parse(raw)
              if (chunk.text) {
                setMessages(prev => prev.map(m =>
                  m.id === agentMsgId
                    ? { ...m, content: m.content + chunk.text }
                    : m
                ))
              }
            } catch {}
          }
        }
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name === 'AbortError') {
        // Benutzer hat abgebrochen
      } else {
        setError(`Fehler: ${e}`)
        setMessages(prev => prev.map(m =>
          m.id === agentMsgId
            ? { ...m, content: m.content || `⚠️ Fehler: ${e}` }
            : m
        ))
      }
    } finally {
      setMessages(prev => prev.map(m =>
        m.id === agentMsgId ? { ...m, streaming: false } : m
      ))
      setStreaming(false)
      streamingIdRef.current = null
      abortRef.current = null
    }
  }, [inputText, selectedAgent, streaming])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }, [sendMessage])

  const cancelStream = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const clearChat = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  return (
    <div className="chatModule">
      {/* Header */}
      <div className="chatHeader">
        <div className="chatHeaderLeft">
          <span className="chatIcon">💬</span>
          <span className="chatTitle">Agent-Chat</span>
        </div>
        <div className="chatHeaderRight">
          <button className="chatClearBtn" onClick={clearChat} title="Chat leeren">🗑</button>
          <button className="chatRefreshBtn" onClick={loadAgents} title="Agenten neu laden">↻</button>
        </div>
      </div>

      {/* Agent Picker */}
      <div className="agentPickerBar" onClick={() => setShowAgentPicker(v => !v)}>
        {loading ? (
          <span className="agentPickerLoading">Lade Agenten...</span>
        ) : selectedAgent ? (
          <>
            <span className="agentPickerStatus">{STATUS_EMOJI[selectedAgent.status] || '⚪'}</span>
            <span className="agentPickerName">{selectedAgent.name}</span>
            <span className="agentPickerRole">{selectedAgent.title || selectedAgent.role || ''}</span>
            <span className="agentPickerCount">({agents.length} Agenten) ▾</span>
          </>
        ) : (
          <span className="agentPickerEmpty">Keinen Agenten ausgewählt ▾</span>
        )}
      </div>

      {/* Agent Dropdown */}
      {showAgentPicker && (
        <div className="agentDropdown">
          {agents.map(agent => (
            <div
              key={agent.id}
              className={`agentDropdownItem ${selectedAgent?.id === agent.id ? 'active' : ''}`}
              onClick={() => {
                setSelectedAgent(agent)
                setShowAgentPicker(false)
                setMessages([])
              }}
            >
              <span>{STATUS_EMOJI[agent.status] || '⚪'}</span>
              <span className="agentDropdownName">{agent.name}</span>
              {agent.title && <span className="agentDropdownTitle">{agent.title}</span>}
            </div>
          ))}
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="chatErrorBanner" onClick={() => setError(null)}>
          ⚠️ {error} <span className="errorDismiss">✕</span>
        </div>
      )}

      {/* Messages */}
      <div className="chatMessages">
        {messages.length === 0 && !loading && (
          <div className="chatEmptyState">
            {selectedAgent
              ? `💬 Chatte mit ${selectedAgent.name}`
              : 'Wähle einen Agenten aus'}
          </div>
        )}
        {messages.map(msg => (
          <div key={msg.id} className={`chatMsg chatMsg--${msg.role}`}>
            <div className="chatMsgBubble">
              {msg.content || (msg.streaming ? <span className="chatTyping">●●●</span> : '')}
            </div>
            <div className="chatMsgMeta">
              {msg.role === 'agent' ? (selectedAgent?.name || 'Agent') : 'Du'}
              {' · '}
              {new Date(msg.ts).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chatInputArea">
        <textarea
          ref={inputRef}
          className="chatInput"
          value={inputText}
          onChange={e => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={selectedAgent ? `Nachricht an ${selectedAgent.name}...` : 'Agenten auswählen...'}
          disabled={!selectedAgent || streaming}
          rows={2}
        />
        {streaming ? (
          <button className="chatSendBtn chatSendBtn--stop" onClick={cancelStream}>⏹</button>
        ) : (
          <button
            className="chatSendBtn"
            onClick={sendMessage}
            disabled={!inputText.trim() || !selectedAgent}
          >
            ➤
          </button>
        )}
      </div>
    </div>
  )
}
