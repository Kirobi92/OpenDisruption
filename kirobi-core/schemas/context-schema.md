# Kontext-Schema: Kirobi Core

**Zone:** WORKSPACE | **Version:** 1.0

---

## Sitzungs-Kontext

```typescript
interface SessionContext {
  session_id: string;
  started_at: string;
  user: string;           // Sven | Samira | Sineo | System
  zone: Zone;
  active_project?: string;
  conversation_history: Message[];
  loaded_documents: string[];
  current_agent: AgentName;
}

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  agent?: AgentName;
  model?: ModelName;
}
```

## Langzeit-Kontext (aus PostgreSQL)

```typescript
interface LongtermContext {
  last_sessions: SessionSummary[];  // Letzte 7 Sitzungen
  open_tasks: Task[];
  recent_learnings: string[];       // Aus experiences/learnings/
  active_projects: Project[];
}
```
