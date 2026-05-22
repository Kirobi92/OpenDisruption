import { useEffect, useState, useCallback } from 'react'
import './AgentsModule.css'

const COMPANY_ID = '32a3cd4e-b59f-470b-bddb-aeb288ecfb21'

function paperclipBase(): string {
  const stored = localStorage.getItem('kirobi_backend')
  const host = stored || (window.location.hostname === 'localhost' ? '192.168.178.10' : window.location.hostname)
  return `http://${host}:3100`
}

type Issue = {
  id: string
  identifier?: string
  title: string
  status: string
  priority?: string
  assignedAgentIds?: string[]
}

type Agent = {
  id: string
  name: string
  role?: string
}

const STATUS_COLOR: Record<string, string> = {
  backlog: '#555',
  todo: '#888',
  in_progress: '#4a9eff',
  done: '#4caf50',
  blocked: '#f44336',
  cancelled: '#888',
}

const STATUS_LABEL: Record<string, string> = {
  backlog: '📋 Backlog',
  todo: '📌 Todo',
  in_progress: '⚡ Läuft',
  done: '✅ Fertig',
  blocked: '🚫 Blockiert',
  cancelled: '❌ Abgebrochen',
}

export default function AgentsModule() {
  const [issues, setIssues] = useState<Issue[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [log, setLog] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState<'tasks' | 'agents' | 'log'>('tasks')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const base = paperclipBase()
      const [issuesRes, agentsRes] = await Promise.all([
        fetch(`${base}/api/companies/${COMPANY_ID}/issues`),
        fetch(`${base}/api/companies/${COMPANY_ID}/agents`),
      ])
      if (issuesRes.ok) setIssues(await issuesRes.json())
      if (agentsRes.ok) setAgents(await agentsRes.json())
    } catch (e) {
      console.error('Paperclip nicht erreichbar', e)
    }
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  // Auto-refresh alle 30s
  useEffect(() => {
    const t = setInterval(load, 30000)
    return () => clearInterval(t)
  }, [load])

  const agentMap = Object.fromEntries(agents.map(a => [a.id, a.name]))

  const activeTasks = issues.filter(i => i.status === 'in_progress')
  const backlogTasks = issues.filter(i => i.status === 'backlog' || i.status === 'todo')
  const doneTasks = issues.filter(i => i.status === 'done')

  return (
    <div className="agentsModule">
      <div className="agentsHeader">
        <h2>🤖 Agenten-Team</h2>
        <button className="refreshBtn" onClick={load}>↻</button>
      </div>

      {/* Stats Bar */}
      <div className="statsBar">
        <div className="stat">
          <span className="statNum" style={{ color: '#4a9eff' }}>{activeTasks.length}</span>
          <span className="statLabel">Aktiv</span>
        </div>
        <div className="stat">
          <span className="statNum" style={{ color: '#888' }}>{backlogTasks.length}</span>
          <span className="statLabel">Backlog</span>
        </div>
        <div className="stat">
          <span className="statNum" style={{ color: '#4caf50' }}>{doneTasks.length}</span>
          <span className="statLabel">Fertig</span>
        </div>
        <div className="stat">
          <span className="statNum" style={{ color: '#fff' }}>{agents.length}</span>
          <span className="statLabel">Agenten</span>
        </div>
      </div>

      {/* View Switcher */}
      <div className="viewSwitcher">
        <button className={activeView === 'tasks' ? 'active' : ''} onClick={() => setActiveView('tasks')}>Tasks</button>
        <button className={activeView === 'agents' ? 'active' : ''} onClick={() => setActiveView('agents')}>Agenten</button>
        <button className={activeView === 'log' ? 'active' : ''} onClick={() => setActiveView('log')}>Log</button>
      </div>

      {loading && <div className="loadingText">Lade Paperclip...</div>}

      {/* TASKS VIEW */}
      {activeView === 'tasks' && !loading && (
        <div className="issuesList">
          {activeTasks.length > 0 && (
            <>
              <div className="sectionTitle">⚡ In Arbeit</div>
              {activeTasks.map(issue => (
                <IssueCard key={issue.id} issue={issue} agentMap={agentMap} />
              ))}
            </>
          )}
          {backlogTasks.length > 0 && (
            <>
              <div className="sectionTitle">📋 Warteschlange</div>
              {backlogTasks.map(issue => (
                <IssueCard key={issue.id} issue={issue} agentMap={agentMap} />
              ))}
            </>
          )}
          {doneTasks.length > 0 && (
            <>
              <div className="sectionTitle">✅ Erledigt</div>
              {doneTasks.map(issue => (
                <IssueCard key={issue.id} issue={issue} agentMap={agentMap} />
              ))}
            </>
          )}
          {issues.length === 0 && <div className="emptyState">Keine Tasks vorhanden</div>}
        </div>
      )}

      {/* AGENTS VIEW */}
      {activeView === 'agents' && !loading && (
        <div className="agentsList">
          {agents.map(agent => {
            const myTasks = issues.filter(i => i.assignedAgentIds?.includes(agent.id))
            const active = myTasks.filter(i => i.status === 'in_progress')
            return (
              <div key={agent.id} className="agentCard">
                <div className="agentName">{agent.name}</div>
                <div className="agentMeta">
                  {active.length > 0
                    ? <span style={{ color: '#4a9eff' }}>⚡ {active[0].title.slice(0, 40)}</span>
                    : <span style={{ color: '#555' }}>Bereit</span>
                  }
                </div>
                <div className="agentTaskCount">{myTasks.length} Tasks</div>
              </div>
            )
          })}
        </div>
      )}

      {/* LOG VIEW */}
      {activeView === 'log' && (
        <div className="logView">
          <div className="logText">{log || 'Log wird geladen...'}</div>
        </div>
      )}
    </div>
  )
}

function IssueCard({ issue, agentMap }: { issue: Issue; agentMap: Record<string, string> }) {
  const color = STATUS_COLOR[issue.status] || '#888'
  const label = STATUS_LABEL[issue.status] || issue.status
  const assignee = issue.assignedAgentIds?.[0] ? agentMap[issue.assignedAgentIds[0]] : null

  return (
    <div className="issueCard">
      <div className="issueHeader">
        <span className="issueId">{issue.identifier || '—'}</span>
        <span className="issueStatus" style={{ background: color }}>{label}</span>
      </div>
      <div className="issueTitle">{issue.title}</div>
      {assignee && <div className="issueAssignee">🤖 {assignee}</div>}
    </div>
  )
}
