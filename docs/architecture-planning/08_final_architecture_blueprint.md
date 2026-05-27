# 08 — Final Architecture Blueprint

**Datum:** 2026-05-26 · **Status:** Aggregations-Master-Dokument (Mode 2). Aggregiert Phasen 1–7.

---

## 1. Executive Summary

OpenDisruption ist heute ein gewachsener Misch-Tree (24 Top-Level-Ordner, ≈70 GB, kein Git) mit zwei Produkten (KIROBI privat, LUKI Business) und großer Shared-Infrastruktur (Caddy, Hermes-Agent, Qdrant, Ollama, Restic) sowie experimentellen Labs (Webshop, 3D-Druck-Pipeline, ComfyUI, Open-WebUI, Flowise, Hindsight, Mission-Control). Wichtigste Befunde: 16+ Klartext-Secrets im Tree (CRITICAL), Live-DB-Volumes im Repo, doppelte Codebases (kirobi-pwa & home-migration-Tree), Caddy auf `0.0.0.0:80` ohne durchgehende Auth, kein Restore-Test. Ziel-Architektur: Monorepo `OpenDisruption/` mit `products/{kirobi,luki}`, `infra/`, `packages/`, `tools/`, `labs/`, `archive/`; Runtime-Daten ausschließlich unter `/Datenspeicher/OpenDisruption-Data/`; Caddy einziger HTTP-Entry; Secrets pro Service in `…/secrets/<svc>.env` (chmod 600); LUKI startet mit Knowledge-MVP (lokal, Quellenpflicht, Audit-Log). Migration in 8 Phasen (A–H), jede mit Snapshot, Verifikation und Rollback, niemals automatisch.

## 2. Wahrheits-Tree & Bestehende Realität

- **Wahrheits-Tree:** `/Datenspeicher/OpenDisruption_v0.1/` (Nutzerentscheidung).
- **Parallel-Tree:** `/Datenspeicher/home-migration/OpenDisruption/` → ARCHIVE.
- **Parallel-Datenwurzel:** `/Datenspeicher/OpenDisruption_Datenstruktur/` → UNKNOWN_NEEDS_MANUAL_CHECK.
- **Kein Git:** Rollback nur via externem Snapshot.
- **Bestehende Audits** (`KIROBI_OS_AUDIT.md`, `AGENT-ACTIVITY-LOG.md`, `SYSTEM_MAP.md`, `MASTERPLAN-…`, `AGENTS.md`, `README.md`) als Input gelesen, Secret-Lecks in Phase 2 dokumentiert (MASKED).

## 3. Domänenmodell (Ziel)

```
OpenDisruption (Dach)
├── KIROBI_FAMILY        (privat, lokal, Familie)
├── LUKI_BUSINESS        (Business, Nutzeisen/eNVenta, Mittelstand)
├── SHARED_INFRA         (Caddy, Hermes-Runtime, Qdrant, Ollama, DBs, Backup, Monitoring)
├── LABS                 (Webshop, 3D-Druck, ComfyUI, Open-WebUI, Avatar, Marketing-Experimente)
└── ARCHIVE              (Altlasten, eingefrorene Versionen)
```

**Regel:** Keine Komponente lebt in mehreren Domänen. Mischungs-Hotspots in Phase 3 dokumentiert + adressiert.

## 4. Ziel-Repository-Struktur (Monorepo)

(Siehe `04_target_architecture.md` Abschnitt 3 für vollständigen Tree.)

Kurzform: `docs/`, `infra/{caddy,hermes-runtime,qdrant,ollama,postgres,monitoring,backup,secrets-skeleton}`, `products/{kirobi,luki}`, `packages/{policy-gate,ingest,retrieval}`, `tools/{opendisruption-cli,doctor,templates}`, `labs/{webshop,3d-druck,inventory,comfyui,open-webui,flowise,hindsight,mission-control,ionos-integration}`, `archive/`.

## 5. Ziel-Runtime-Datenstruktur (außerhalb Repo)

`/Datenspeicher/OpenDisruption-Data/{shared,kirobi,luki,labs,secrets,backups,archive}/` mit klarer Subgliederung je Domäne. Secrets chmod 700/600, Backup-Ziel extern. (Siehe `04_target_architecture.md` Abschnitt 4.)

## 6. Netzwerkmodell

| Zugang | Mechanismus | Routen |
|---|---|---|
| Loopback | `127.0.0.1:*` | CLI/Debug |
| Docker-Internal | `internal: true` Bridge | DB↔App, App↔Qdrant |
| LAN/Tailscale | Caddy bindet **nur** an Tailscale-IP / 127.0.0.1 + Tailscale-`serve` | `/kirobi`, `/luki`, `/3dbar` etc. |
| Öffentlich | initial nichts | – |

**Regel:** Nur Caddy bindet nicht-Loopback. Admin-Routen immer mit BasicAuth + Tailscale-Bindung.

## 7. Compose- und Deployment-Modell

- `infra/compose.shared.yml`, `products/kirobi/compose.kirobi.yml`, `products/luki/compose.luki.yml`, `labs/<lab>/compose.<lab>.yml`.
- systemd-Wrapper: `od-shared.service`, `od-kirobi.service`, `od-luki.service`, `od-lab-<x>.service`.
- Updates: `git pull` → `docker compose pull` → `up -d` + Healthcheck. Rollback: `git checkout <prev>` + `up -d`.
- Healthchecks + Restart-Policies + gepinnte Image-Tags Pflicht.

## 8. Secrets-Modell

- Speicherort: `/Datenspeicher/OpenDisruption-Data/secrets/` chmod 600, owner sven.
- Repo: nur `*.env.template`, niemals echte Werte.
- Pre-Commit: TruffleHog + gitleaks blockieren Klartext.
- Rotation: Telegram quartalsweise, DB-PW halbjährlich, Restic-Repo-PW jährlich, sofort nach Leak.
- Audit-Doku: ausschließlich `SECRET_FOUND(type=…, file=…, line=…, value=MASKED)`.

## 9. Backup-/Restore-Modell

| Schicht | Tool | Frequenz | Ziel |
|---|---|---|---|
| Datei-Snapshot | Restic | täglich | externes Repo |
| DB-Dumps | mysqldump/pg_dump | täglich | `…/backups/db-dumps/` (7/4/12-Rotation) |
| Qdrant-Snapshots | Qdrant-API | täglich | `…/backups/qdrant/` |
| Restore-Test | scripted | wöchentlich auto + monatlich manuell | Sandkasten |
| Air-Gap | manuell | monatlich | 2. USB-Platte |

**Pflicht:** Restore-Test einmal initial (Phase A) bestanden, danach Routine.

## 10. Monitoring-Modell

- Logs: Loki + Promtail in `…/shared/monitoring/loki/`.
- Metriken (minimal): node-exporter + container-stats; Grafana hinter Caddy+Auth.
- Uptime: Uptime-Kuma als Single-Pane.
- Alerts: Telegram-Channel `od-alerts` — nur Sven, getrennt von User-Bots.

## 11. Logging-Modell

- stdout/stderr → Container-Log → Promtail → Loki.
- Sensible Inhalte nur auf DEBUG, in Produktion deaktiviert.
- LUKI-Audit-Log separat (append-only JSONL, gehasht).

## 12. Test-/CI-Modell

- Unit-Tests pro Package (Python/JS).
- Integrationstests: Compose-Up im CI gegen Smoke-Suite (Mock-Ollama).
- LUKI-Eval: 50 Goldset-Fragen automatisch.
- Security-Scan: Trivy auf Images, TruffleHog auf Diff, Renovate/Dependabot.

## 13. KIROBI im Zielbild

- `products/kirobi/apps/{pwa,avatar}` + `gateways/telegram-{sven,samira}` + `skills/` + `canon/`.
- Privatdaten in `…OpenDisruption-Data/kirobi/{private,shared}/`.
- Family-Zugang: Tailscale + Caddy + BasicAuth; FAMILY_PRIVATE niemals Cloud, niemals LUKI-Kontext.
- Avatar-Domäne: Decision E5 (KIROBI vs. LAB).

## 14. LUKI im Zielbild

- `products/luki/{knowledge,retrieval,audit,evals,canon,source-docs,runbooks,business}`.
- Runtime in `…OpenDisruption-Data/luki/{source-docs,ingest-staging,audit,evals}`.
- MVP = Knowledge: Ingest → Chunk → Embed (Ollama) → Qdrant `luki_knowledge_v1` → Retrieval mit Quellenpflicht → Refusal-Default → Audit-Log → 50-Fragen-Eval.
- Akzeptanz: Top1≥0.50, Top3≥0.75, Halluzination≤0.10.
- Spätere Operatoren: Process / Document / Artikel / Wareneingang / Middleware.

## 15. LABS im Zielbild

- `labs/<lab>/compose.<lab>.yml` mit externen Volumes + Secrets.
- Jeder Lab-Service hat: Owner, Zweck, Start/Stop, Backup, Healthcheck.
- Ohne Compose: FREEZE + Stop (kein Dauerlauf undokumentierter Stacks).

## 16. ARCHIVE-Strategie

- `archive/audits-pre-2026-05/` — alte Audits, Klartext-Secrets quarantäniert.
- `archive/opendisruption-v0.1-snapshot/` — Vor-Migrations-Snapshot.
- `archive/home-migration-tree/` — Parallel-Codebase, eingefroren.
- `archive/qdrant-legacy/` — 10-GB-Duplikat.

## 17. Sicherheits-Baseline (Pflicht vor produktivem Betrieb)

1. Externer Snapshot vorhanden.
2. Klartext-Secrets quarantäniert + rotiert.
3. Caddy: HTTPS lokal, BasicAuth für Admin-Routen, Bind nur an Tailscale/Loopback.
4. Alle Services binden Loopback oder Docker-Internal (außer Caddy).
5. Restic-Restore-Test bestanden.
6. `.gitignore` + Pre-Commit-Hooks im Repo aktiv.
7. Audit-Logs ohne Klartext-Inhalte.
8. Pre-Ingest-PII-Filter bei LUKI.

## 18. Roadmap-Übersicht 7/30/60/90

(Vollständig in `06_roadmap_and_migration_plan.md` Abschnitt A.)

- **0–7 d:** Safety Baseline (R-001..R-008).
- **8–30 d:** Skeleton + Shared-Infra-Migrationen + KIROBI-Cleanup-Vorbereitung + Webshop-Volume-Migration (R-009..R-021).
- **31–60 d:** LUKI Knowledge MVP + Runbooks + Monitoring (R-022..R-028).
- **61–90 d:** LUKI Pilot Nutzeisen + Business-Readiness + Operator-Blueprints + Preismodell (R-029..R-035).

## 19. Critical Path

R-001 → R-002 → R-003 → R-007 → R-016 → R-015 → R-022 → R-023 → R-025 → R-030
(Snapshot → Quarantäne → Rotation → Restore-Test → DB-Volumes raus → Qdrant konsolidiert → LUKI Ingest → Retrieval → Eval → Pilot.)

## 20. Phasenplan A–H (Kurzform)

| Phase | Titel | Ziel | Gate |
|---|---|---|---|
| A | Safety Baseline | Snapshot, Secrets, Caddy, Restore-Test | FREIGABE PHASE B |
| B | Repository Skeleton | Leeres Monorepo + Git + Pre-Commit + CI | FREIGABE PHASE C |
| C | Shared Infra Normalisierung | Hermes, Qdrant, Ollama, Caddy, Webshop-Volumes migrieren | FREIGABE PHASE D |
| D | KIROBI Cleanup | PWA-Wahrheit, Gateways, Skills, Privatdaten konsolidieren | FREIGABE PHASE E |
| E | LUKI Extraction | Profile, Source-Docs, Canon extrahieren | FREIGABE PHASE F |
| F | LUKI Knowledge MVP | Ingest, Retrieval, Audit, Eval, Caddy-Route | FREIGABE PHASE G |
| G | Documentation & Runbooks | Betriebsfähigkeit ohne stilles Wissen | FREIGABE PHASE H |
| H | Business Readiness | Nutzeisen-Pilot, Operator-Blueprints, Preismodell | Projekt-Review |

(Vollständig in `07_phased_implementation_plan.md`.)

## 21. Offene Entscheidungen (Nutzer)

| ID | Frage | Phase |
|---|---|---|
| D1 | InvenTree → LUKI oder LABS? | E |
| D2 | Webshop im Monorepo oder eigenes Repo? | C/H |
| D3 | kirobi-avatar = KIROBI oder LAB? | D |
| D4 | „lebenscoach"/„web3" Owner? | E |
| D5 | kirobi-pwa Wahrheits-Pfad? | D |
| E1 | Monorepo bestätigen? | (vor B) |
| E2 | Backup-Ziel-Hardware? | (vor A) |
| E3 | Tailscale Pflicht oder optional? | (vor A) |
| E4 | Restic-Restore-Berechtigte? | (vor A) |
| E5 | Avatar-Domäne? | D |

## 22. Risiken & Mitigation (Top-5)

1. **Klartext-Secrets im Tree + Live-DB-Volumes:** Phase A rotiert + quarantäniert + isoliert; Phase C migriert Volumes.
2. **Kein Git, kein Branch-Rollback:** Phase A erzwingt externen Snapshot; Phase B initialisiert Git.
3. **Doppelte PWA-Codebase:** Phase D verlangt explizite Wahrheits-Entscheidung + Diff.
4. **Caddy ohne durchgehende Auth + HTTPS lokal:** Phase A härtet sofort.
5. **Halluzinationen in LUKI:** Phase F erzwingt Quellenpflicht, Refusal-Default, Eval-Cycle.

## 23. Nächste Schritte (für Implementierungsagenten)

(Vollständig in `09_next_agent_prompts.md`.)

- Agent 1: Security-Hardening (Phase A).
- Agent 2: Repo-Skeleton (Phase B).
- Agent 3: Shared-Infra-Migration (Phase C).
- Agent 4: KIROBI-Cleanup (Phase D).
- Agent 5: LUKI-Extraction (Phase E).
- Agent 6: LUKI-Knowledge-MVP (Phase F).
- Agent 7: Documentation & Runbooks (Phase G).
- Agent 8: Verification/QA (querschnittlich + Phase H Pre-Pilot).

**Regel:** Jeder Agent läuft nur auf explizite Freigabe; kein automatischer Übergang.
