---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# prompts/agents – Agent-Prompts

System-Prompts und Persona-Definitionen für die 14 spezialisierten Kirobi-Agenten. Jeder Agent hat einen eigenen Charakter, Zuständigkeitsbereich und Zonen-Zugriff.

## Zweck

Agent-Prompts definieren die Identität, Fähigkeiten und Grenzen eines Agenten. Sie werden beim Start eines Agenten als System-Prompt übergeben und bestimmen sein Verhalten, seinen Ton und seine Entscheidungslogik.

## Namenskonvention

```
[agent-name]-system-prompt-v[version].md
Beispiele:
  kirobi-core-system-prompt-v1.md
  hermes-extractor-system-prompt-v1.md
  samira-heart-system-prompt-v1.md
```

## Agenten-Übersicht

| Agent | Zuständigkeit | Zonen-Zugriff |
|-------|--------------|---------------|
| `kirobi-core` | Supervisor, Orchestrierung | ALL |
| `kirobi-architect` | Architektur, Design | PUBLIC, WORKSPACE |
| `kirobi-coder` | Code, Tests, Bugfixes | PUBLIC, WORKSPACE |
| `kirobi-ops` | Infra, Docker, CI/CD | PUBLIC, WORKSPACE, QUARANTINE |
| `hermes-extractor` | Ingestion, Klassifizierung | PUBLIC, WORKSPACE, QUARANTINE |
| `samira-heart` | Familien-Mediation | PUBLIC, WORKSPACE, FAMILY_PRIVATE |
| `sineo-creator` | Creator-Content | PUBLIC, WORKSPACE, FAMILY (Sineo) |
| `family-interviewer` | Familien-Interviews | FAMILY_PRIVATE |
| `enterprise-agent` | Business, M365 | PUBLIC, WORKSPACE |
| `voice-agent` | Sprach-I/O | PUBLIC, WORKSPACE (delegiert) |
| `installer-agent` | Setup, Onboarding | PUBLIC, WORKSPACE |
| `research-crew` | Recherche | PUBLIC, WORKSPACE |
| `creative-agent` | Kreative Inhalte | PUBLIC, WORKSPACE |
| `kirobi-observer` | Monitoring, Reports | ALL (summary only) |

## Verwandte Verzeichnisse

- `prompts/family/` – Prompts für familienbezogene Agenten
- `prompts/system/` – Allgemeine System-Prompts
- `kirobi-core/` – Identitäts- und Policy-Dokumente der Agenten
- `metadata/AGENTREGISTRY.md` – Offizielle Agent-Registry
