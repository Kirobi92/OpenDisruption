# Routing-Schema: Kirobi Core

**Zone:** WORKSPACE | **Version:** 1.0

---

## Routing-Entscheidungs-Schema

```typescript
interface RoutingDecision {
  request_id: string;
  timestamp: string;
  input_summary: string;    // Kurze Beschreibung der Anfrage
  detected_zone: Zone;
  detected_type: RequestType;
  selected_agent: AgentName;
  selected_model: ModelName;
  reasoning: string;        // Warum diese Entscheidung?
  fallback_agent?: AgentName;
  requires_human: boolean;
}

type RequestType = 
  | 'code' | 'architecture' | 'ops' | 'monitoring'
  | 'ingestion' | 'family' | 'mediation' | 'creative'
  | 'research' | 'business' | 'general';
```
