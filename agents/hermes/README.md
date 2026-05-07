---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Agent: hermes-reasoner

Reasoning-Agent für Multi-Step-Logik, Chain-of-Thought, Pro/Contra-Debatten und Research-Synthese. Intern als `hermes-reasoner` bezeichnet, um Kollision mit dem bestehenden `hermes-extractor` zu vermeiden.

## Zustand

Phase-2-Skelett. Der `handle()`-Body gibt ein strukturiertes Echo-Ergebnis zurück. Echtes LLM-Reasoning wird in Phase 4 implementiert.

## Dateien

- `agent.py` — Implementierung von `HermesReasonerAgent` (erbt von `BaseAgent`)
- `__init__.py` — Modul-Export
- `Dockerfile` — Container-Definition

## Unterstützte Task-Typen

- `chain_of_thought` — Schrittweise Schlussfolgerung
- `debate` — Pro/Contra-Analyse
- `hypothesis` — Hypothesen-Generierung und Validierung
- `research_synthesis` — Zusammenführung mehrerer Quellen
- `multi_step_reasoning` — Mehrstufige Problemlösung

## Erlaubte Zonen

Input und Output: `PUBLIC`, `WORKSPACE`

## Verwandte Agenten

- `hermes-extractor` — Ingestion-Pipeline (anderer Agent, gleiches Namensfeld)
- `agents/_base/agent.py` — Basis-Klasse mit Zone-Enforcement
