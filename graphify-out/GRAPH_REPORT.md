# Graph Report - OpenDisruption  (2026-06-10)

## Corpus Check
- 37 files · ~25,525 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 349 nodes · 386 edges · 37 communities (29 shown, 8 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b80324f1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]

## God Nodes (most connected - your core abstractions)
1. `08 — Final Architecture Blueprint` - 24 edges
2. `05 — LUKI MVP Definition` - 16 edges
3. `04 — Target Architecture` - 15 edges
4. `00 — Execution Protocol` - 12 edges
5. `build_status()` - 10 edges
6. `06 — Roadmap & Migration Plan (7 / 30 / 60 / 90 Tage)` - 10 edges
7. `07 — Phased Implementation Plan (A–H)` - 10 edges
8. `09 — Next Agent Prompts` - 10 edges
9. `answer_question()` - 8 edges
10. `B) STOPP — Schritte die Nutzer-Aktion brauchen` - 8 edges

## Surprising Connections (you probably didn't know these)
- `test_audit_rejects_repo_data_root()` --calls--> `datetime`  [INFERRED]
  tests/test_luki_mvp_server.py → tools/luki_mvp_server.py
- `test_answer_refuses_without_retrieval_sources_and_writes_hash_audit()` --calls--> `datetime`  [INFERRED]
  tests/test_luki_mvp_server.py → tools/luki_mvp_server.py

## Import Cycles
- 1-file cycle: `tools/luki_mvp_server.py -> tools/luki_mvp_server.py`

## Communities (37 total, 8 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.15
Nodes (23): BaseHTTPRequestHandler, datetime, HTTPStatus, RuntimeError, answer_question(), AskRequest, AskResponse, _audit_path() (+15 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (24): 08 — Final Architecture Blueprint, 10. Monitoring-Modell, 11. Logging-Modell, 12. Test-/CI-Modell, 13. KIROBI im Zielbild, 14. LUKI im Zielbild, 15. LABS im Zielbild, 16. ARCHIVE-Strategie (+16 more)

### Community 2 - "Community 2"
Cohesion: 0.10
Nodes (20): audit, enabled, hash_answer, hash_question, hash_user, chunk_overlap, chunk_size, collection (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (18): A.1 R-001 Externer Snapshot, A.2 R-001b Datenbank-Dumps (zusätzlich), A.3 R-004 `.gitignore`-Template, A.4 R-008 Zombie-/Restart-Loop-Inventur, A.5 R-009/R-010/R-011 Skelett + Git, A.6 R-021 CI-Skelett, A) Erfolgreich autonom abgeschlossen, B) STOPP — Schritte die Nutzer-Aktion brauchen (+10 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (16): 05 — LUKI MVP Definition, 10. Logging, 11. Evaluation, 12. Demo-Szenario (Nutzeisen), 13. Akzeptanzkriterien (messbar), 14. Risiken (MVP), 15. Spätere Operatoren (nach MVP), 1. Problem (+8 more)

### Community 5 - "Community 5"
Cohesion: 0.19
Nodes (22): CapabilityState, Namespace, build_parser(), build_status(), cmd_blueprint(), cmd_graph(), cmd_status(), _feature_planes() (+14 more)

### Community 6 - "Community 6"
Cohesion: 0.12
Nodes (15): 04 — Target Architecture, 10. Ziel-Deployment-Modell, 11. Ziel-Logging-Modell, 12. Ziel-Testmodell, 13. Monorepo vs. Multi-Repo, 14. Offene Entscheidungen (für Nutzer), 1. Architekturprinzipien (verbindlich), 2. Ziel-Domänenmodell (+7 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (13): Bereit für PHASE C (Shared Infra), Caddy-Hardening Details, Caddy-Klartext-File löschen, DB-PW-Rotation (webshop-mysql, partdb-db), Deferred to Phase C, Legacy-Tree-Residual-Secrets, N.2#4/5 InvenTree, N.2#6 WooCommerce REST-API-Keys (+5 more)

### Community 8 - "Community 8"
Cohesion: 0.14
Nodes (13): Aufgeschoben — Bewusst nicht autonom ausgeführt, DB-PW-Rotation (von Phase A geerbt), Erreichtes (autonom), PC.1 — kirobi-backup.service fixed, PC.2 — Compose-Lücken-Analyse, PC.2b — Weitere Secret-Funde (bonus), PC.3 — Hermes-Runtime-Daten-Migration (~/.hermes → Data-Tree), PC.4 — Netz-Hardening (UFW) (+5 more)

### Community 9 - "Community 9"
Cohesion: 0.15
Nodes (12): 00 — Execution Protocol, 10. Wie ich fortfahre, 11. Evidenzlabels, 1. Bestätigter Arbeitsmodus, 2. Erkannte Projektwurzel, 3. Erkannte Git-Situation, 4. Parallele Codebase (Klärung erledigt), 5. Erkannte Hauptbereiche (Top-Level v0.1) (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.17
Nodes (11): 3D-Druck-Bar Preview, Compose-Lücken-Analyse (R-019) — Stand 2026-05-28, Fehlende Compose-Files (R-019), Flowise / Paperclip / Ollama / Qdrant / Comfy / Avatar / Shop-Admin, Hindsight Server, Laufende Container ohne nachvollziehbares Compose, Mission Control, Open-WebUI (+3 more)

### Community 11 - "Community 11"
Cohesion: 0.18
Nodes (10): 06 — Roadmap & Migration Plan (7 / 30 / 60 / 90 Tage), A) Aufgabenmatrix, B) Critical Path, C) Stop-Doing-List, D) Decision Log (initial), E) Open Questions, F) Migration Order (kurz), G) Rollback Points (+2 more)

### Community 12 - "Community 12"
Cohesion: 0.18
Nodes (10): 07 — Phased Implementation Plan (A–H), PHASE A — Safety Baseline, PHASE B — Repository Skeleton, PHASE C — Shared Infra Normalisierung, PHASE D — KIROBI Cleanup, PHASE E — LUKI Extraction, PHASE F — LUKI Knowledge MVP, PHASE G — Documentation & Runbooks (+2 more)

### Community 13 - "Community 13"
Cohesion: 0.18
Nodes (10): 09 — Next Agent Prompts, Agent 1 — Security-Hardening (PHASE A), Agent 2 — Repo-Skeleton (PHASE B), Agent 3 — Shared-Infra-Migration (PHASE C), Agent 4 — KIROBI-Cleanup (PHASE D), Agent 5 — LUKI-Extraction (PHASE E), Agent 6 — LUKI-Knowledge-MVP (PHASE F), Agent 7 — Documentation & Runbooks (PHASE G) (+2 more)

### Community 14 - "Community 14"
Cohesion: 0.20
Nodes (9): 01 — Current State Inventory, A) Services & Runtime-Komponenten, B) Daten-/Benutzerbereich (Klassifikation), C) Parallel-Tree (summarisch), Compose-Inventar (vollständig), D) Drift-Befunde gegen Alt-Audits, E) Zentrale Befunde, Systemd-Units (im Tree) (+1 more)

### Community 15 - "Community 15"
Cohesion: 0.22
Nodes (8): A — Docker-Network-Refactor (CLEAN, INVASIV), Aktueller Zustand (Stand 2026-05-28 07:15), B — Dual-Bind (PRAGMATISCH), C — Host-Firewall (UFW), Empfehlung, Lösungs-Ansätze, Network-Hardening Plan — Port-Binding Lockdown, UFW-Skript (vom User auszuführen)

### Community 16 - "Community 16"
Cohesion: 0.25
Nodes (7): A) Laufende Container (HEALTHY), B) Exited Container (kirobi-*-Microservice-Stack — NEU ENTDECKT), C) systemd Units — kritische Befunde, D) journalctl-Befunde (7 Tage), E) Action-Items für Phase A, F) Neue Roadmap-Aufgabe (Nachtrag), Phase-A Report — Zombie- & Restart-Loop-Inventur (R-008)

### Community 17 - "Community 17"
Cohesion: 0.29
Nodes (6): 02 — Security & Operations Risks, A) Secret-Inventar (alle maskiert), B) Risikomatrix, C) Top-5 kritische Risiken, D) Quick-Wins (Aufwand XS/S, Kritikalität HIGH+), E) Hinweis zur Reihenfolge

### Community 18 - "Community 18"
Cohesion: 0.29
Nodes (6): OpenDisruption, Owner, Runtime-Daten, Status, Struktur, Wichtige Regeln

### Community 19 - "Community 19"
Cohesion: 0.33
Nodes (5): Ausfuehrbare Control Plane, Definition von Ultimate, Feature Planes, Naechste Implementierungswellen, OpenDisruption Ultimate

### Community 20 - "Community 20"
Cohesion: 0.57
Nodes (6): ask(), readJson(), refreshStatus(), setAnswer(), setText(), state

### Community 21 - "Community 21"
Cohesion: 0.40
Nodes (4): Boundaries, MVP Rule, OpenDisruption Agent Instructions, Versioning

### Community 22 - "Community 22"
Cohesion: 0.40
Nodes (4): 03 — Domain Boundary Model, A) Komponenten-Zuordnung, B) Vermischungs-Hotspots (mit konkreter Aktion), C) Offene Entscheidungspunkte (Nutzer)

### Community 23 - "Community 23"
Cohesion: 0.40
Nodes (4): collection, documents, notes, schema

### Community 25 - "Community 25"
Cohesion: 0.83
Nodes (3): log(), send_telegram(), backup-datenspeicher.sh script

### Community 26 - "Community 26"
Cohesion: 0.50
Nodes (3): questions, schema, target_count

### Community 35 - "Community 35"
Cohesion: 0.29
Nodes (4): Path, test_answer_refuses_without_retrieval_sources_and_writes_hash_audit(), test_audit_rejects_repo_data_root(), test_config_rejects_collection_outside_allowlist()

### Community 36 - "Community 36"
Cohesion: 0.40
Nodes (4): Commands, Graphify Runbook, Rules, Runtime Surfaces

## Knowledge Gaps
- **211 isolated node(s):** `collection`, `embedding_model`, `llm_model`, `top_k`, `score_threshold` (+206 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `datetime` connect `Community 0` to `Community 35`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Why does `UltimateStatus` connect `Community 5` to `Community 0`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **What connects `collection`, `embedding_model`, `llm_model` to the rest of the system?**
  _211 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.1477832512315271 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.09523809523809523 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._