# quarantine – Nicht klassifizierte Inhalte

**Zone:** QUARANTINE | **Verantwortlich:** kirobi-observer, kirobi-core

## Zweck
Eingehende, noch nicht klassifizierte Inhalte. Kein Agent hat uneingeschränkten Zugriff auf diese Zone. Alle Inhalte müssen vor Weiterverarbeitung geprüft und klassifiziert werden.

## Regeln

1. **Kein Auto-Embedding**: Inhalte werden nicht automatisch eingebettet
2. **Review erforderlich**: Jedes Dokument muss manuell geprüft werden
3. **Kurze Verweildauer**: Max. 30 Tage in Quarantäne
4. **Protokollierung**: Jede Aktion wird geloggt

## Workflow

```
Eingang → Quarantine → Review → [sources/ | trash]
```
