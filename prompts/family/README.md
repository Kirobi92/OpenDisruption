---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# prompts/family – Familien-Prompts

System-Prompts und Gesprächsleitfäden für familienbezogene Agenten: `family-interviewer`, `samira-heart` und `sineo-creator`. Diese Prompts sind auf empathische, respektvolle und datenschutzbewusste Interaktion mit der Familie Darusi ausgelegt.

## Zweck

Familien-Prompts definieren, wie Kirobi mit Sven, Samira und Sineo kommuniziert – jeder mit eigenem Ton, eigener Tiefe und eigenen Grenzen. Sie sind das emotionale Herzstück des Systems.

## Enthaltene Prompts

| Datei | Agent | Zone | Beschreibung |
|-------|-------|------|-------------|
| `family-interviewer-prompt.md` | family-interviewer | FAMILY_PRIVATE | Empathische Familien-Interviews, Werte- und Traum-Erfassung |

## Namenskonvention

```
[agent]-[aufgabe]-v[version].md
Beispiele:
  family-interviewer-prompt-v1.md
  samira-heart-system-prompt-v1.md
  sineo-creator-system-prompt-v1.md
```

## Zonen-Hinweis

**Familien-Prompts selbst** sind `WORKSPACE` (sie enthalten keine persönlichen Daten).  
**Gesprächsergebnisse und Interview-Protokolle** sind mindestens `FAMILY_PRIVATE` und werden in `experiences/family/` gespeichert.  
**Besonders sensible Inhalte** (Trauma, Grenzen, tiefe Werte) werden als `SACRED` markiert.

## Sicherheitsregeln

- Familiendaten aus Gesprächen **niemals** an Cloud-APIs senden
- Interview-Ergebnisse nur in `FAMILY_PRIVATE`-Zonen speichern
- Grenzen sofort respektieren – kein Nachhaken bei klarem „Nein"
- Notfall-Protokoll aktivieren bei Krisenzeichen (siehe `family-interviewer-prompt.md`)

## Verwandte Verzeichnisse

- `experiences/family/` – Gespeicherte Interview-Protokolle (FAMILY_PRIVATE)
- `canon/family/` – Familien-Profile und Werte-Dokumente (FAMILY_PRIVATE)
- `prompts/agents/` – Übersicht aller Agent-Prompts
- `kirobi-core/` – Identitäts-Dokumente der Agenten
