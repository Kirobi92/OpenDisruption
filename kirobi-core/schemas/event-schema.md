# Event-Schema: Kirobi Core

**Zone:** WORKSPACE | **Version:** 1.0

---

## Pflichtfelder

```typescript
interface KirobiEvent {
  id: string;          // UUID v4
  timestamp: string;   // ISO-8601
  event_code: string;  // SYS.BOOT, AGT.TASK_START, etc.
  agent: string;       // Agent-Name aus AGENTREGISTRY
  zone: Zone;          // PUBLIC|WORKSPACE|FAMILY_PRIVATE|QUARANTINE|SACRED
  message: string;     // Menschenlesbare Beschreibung
  severity: Severity;  // INFO|WARNING|ERROR|CRITICAL
}

type Zone = 'PUBLIC' | 'WORKSPACE' | 'FAMILY_PRIVATE' | 'QUARANTINE' | 'SACRED';
type Severity = 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
```

## Optionale Felder

```typescript
interface KirobiEventDetails {
  source?: string;      // Quelldatei oder -pfad
  target?: string;      // Zieldatei oder -pfad
  duration_ms?: number; // Dauer der Operation
  error_code?: string;  // Fehlercode bei ERROR/CRITICAL
  related_ids?: string[]; // IDs verknüpfter Events
  human_required?: boolean; // Human-in-Loop erforderlich?
}
```
