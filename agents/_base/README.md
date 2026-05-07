---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# agents/_base

Abstrakte Basisklasse fuer alle Kirobi-Agenten. Definiert das gemeinsame Interface, Zonen-Validierung, Logging und die optionale Integration mit dem kidi-Kontext-Layer.

## Zweck

Jeder Agent im `agents/`-Paket erbt von `BaseAgent`. Die Basisklasse stellt sicher, dass:
- Aufgaben vor der Ausfuehrung auf Zonen-Konformitaet geprueft werden
- Genehmigungs-pflichtige Aufgaben (`requires_approval=True`) nicht ohne Token ausgefuehrt werden
- Kontext-Informationen optional in der kidi-ContextDB persistiert werden koennen
- Jede Aufgabe mit einer eindeutigen `task_id` (UUID) nachverfolgbar ist

## Wichtige Dateien

| Datei | Beschreibung |
|-------|-------------|
| `agent.py` | Enthaelt `BaseAgent` (abstrakte Klasse), `Task` (Dataclass) und `AgentResult` (Dataclass) |
| `__init__.py` | Exportiert `BaseAgent`, `Task`, `AgentResult` |

## Datenmodelle

### Task
```python
@dataclass
class Task:
    task_id: str          # UUID (automatisch generiert)
    task_type: str        # Aufgaben-Typ (agenten-spezifisch)
    zone: str             # Sicherheitszone (PUBLIC/WORKSPACE/...)
    payload: dict         # Aufgaben-Daten
    requires_approval: bool
    approval_token: str | None
    created_at: str       # ISO-8601 UTC
```

### BaseAgent (abstrakt)
Unterklassen muessen `handle(task: Task) -> AgentResult` implementieren.

## Abhaengigkeiten

- `kidi.context_db.client.ContextDB` — optional; graceful degradation wenn kidi nicht installiert
- Keine externen Abhaengigkeiten jenseits der Standardbibliothek
