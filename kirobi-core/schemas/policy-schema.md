# Policy-Schema: Kirobi Core

**Zone:** WORKSPACE | **Version:** 1.0

---

## Policy-Struktur

```typescript
interface KirobiPolicy {
  id: string;
  name: string;
  version: string;
  priority: number;     // Niedrigere Zahl = höhere Priorität
  scope: PolicyScope;
  rule: string;         // Beschreibung der Regel
  examples: PolicyExample[];
  exceptions: string[]; // Ausnahmen (müssen explizit sein)
  created_by: string;
  last_reviewed: string;
  reviewed_by: string;
}

interface PolicyScope {
  zones: Zone[];
  agents: AgentName[];
  content_types?: string[];
}

interface PolicyExample {
  scenario: string;
  correct_action: string;
  incorrect_action: string;
}
```
