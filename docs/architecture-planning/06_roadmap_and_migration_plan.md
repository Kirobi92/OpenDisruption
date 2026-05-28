# 06 — Roadmap & Migration Plan (7 / 30 / 60 / 90 Tage)

**Datum:** 2026-05-26 · **Letztes Update:** 2026-05-28 (Phase A+C abgeschlossen) · Format: ausführbare Aufgaben mit Akzeptanz und Rollback.

## Status-Übersicht (2026-05-28)

| Phase | Status | Bericht |
|---|---|---|
| A — Safety Baseline | ✅ COMPLETE | `reports/A-03-phase-a-complete-2026-05-27.md` |
| B — Repository Skeleton | ✅ COMPLETE (mit Phase A) | inkl. Git-Init + `.gitignore` + CI |
| C — Shared Infra | ✅ AUTONOM-SCOPE COMPLETE | `reports/C-03-phase-c-complete-2026-05-28.md` |
| D — KIROBI Cleanup | ⏳ NEXT | Hermes-Runtime-Migration, PWA-Service, Telegram-Gateways |
| E — LUKI Extraction | PENDING | – |
| F — LUKI Knowledge MVP | PENDING | – |
| G — Doku/Runbooks | PENDING | – |
| H — Business Readiness | PENDING | – |

**Verbleibende User-Aktionen (blockierend für 100% Phase A/C):**
1. UFW-Skript ausführen (siehe `C-01-network-hardening-plan-2026-05-28.md`)
2. Telegram-Bot-Tokens via @BotFather rotieren
3. WooCommerce-Keys via WP-Admin neu generieren
4. Caddy-Plaintext-PW-File löschen (`shred -u …secrets/caddy-plaintext-2026-05-27.txt`)

## A) Aufgabenmatrix

| ID | Zeitraum | Titel | Domäne | Prio | Aufwand | Risiko | Abhängigkeit | Aktion | Akzeptanzkriterium | Rollback | Evidenz |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R-001 | 0–7 d | Externer Snapshot vor Phase A | OPENDISRUPTION_ROOT | P0 | S | LOW | – | `rsync -aAX --numeric-ids /Datenspeicher/OpenDisruption_v0.1/ /Datenspeicher/Backups/OpenDisruption-pre-migration-2026-05-26/` + Verifikation Dateianzahl/Größe | Snapshot exists + Manifest `find … \| wc -l` notiert | – (read-only) | Plan-Datei |
| R-002 | 0–7 d | Audit-Dateien mit Klartext-Secrets quarantänieren | OPENDISRUPTION_ROOT | P0 | S | LOW | R-001 | `AGENT-ACTIVITY-LOG.md`, `KIROBI_OS_AUDIT.md` (geprüft) nach `/Datenspeicher/OpenDisruption-Data/secrets/quarantine/` (chmod 600) verschieben; redigierte Kopien im Repo (alle Secrets → MASKED) | Originale nicht mehr im Tree; redigierte Kopien geprüft | Snapshot R-001 | SEC-008/010 |
| R-003 | 0–7 d | Klartext-Secrets rotieren | SHARED + LABS | P0 | S | MED | R-002 | Telegram-Bot-Tokens (3d-druck-pipeline) revoken+neu; InvenTree User-PW + API-Token neu; WooCommerce Consumer-Key+Secret regenerieren; Restic-Repo-PW rotieren + neues Repo; Part-DB Default-Admin-PW ändern; Webshop MySQL/WP-PW neu | jeweils alter Wert ungültig + neuer Wert in `…/secrets/<svc>.env` (chmod 600) | alte Secrets dokumentiert deaktiviert | Phase 2 |
| R-004 | 0–7 d | `.gitignore`-Skelett vorbereiten (Pre-Git-Init) | OPENDISRUPTION_ROOT | P1 | XS | LOW | – | Datei `tools/templates/.gitignore` mit harten Regeln (`**/.env`, `**/.venv`, `**/node_modules`, `**/__pycache__`, `**/*.sqlite*`, `**/*.db`, `data/`, `logs/`, `services/qdrant/`, `services/open-webui/data/`, `.opencode/`, `.omo/`, `.hermes/`) | Datei existiert + Review | – | SEC-009 |
| R-005 | 0–7 d | Caddy-Audit + minimale Auth | SHARED_INFRA | P0 | M | MED | R-001 | Caddyfile reviewen, Admin-Routen (`/mission`, `/flowise`, `/webui`, `/luki`, `/3dbar`) hinter `basicauth` (PW-Hashes in `…/secrets/caddy.env`); Caddy nur an Tailscale-IP **oder** `127.0.0.1` binden; `auto_https on` mit lokaler CA für `*.lan` | Port-Scan zeigt keinen offenen Admin-Endpoint ohne Auth | Caddyfile-Backup + reload alt | SEC-015 |
| R-006 | 0–7 d | Kirobi-PWA auf 127.0.0.1 | KIROBI | P0 | XS | LOW | R-005 | `kirobi-pwa.service` Env `HOST=127.0.0.1`, systemd-reload; Caddy-Route `/kirobi` → `127.0.0.1:4300` | `ss -ltnp` zeigt nur Loopback; PWA via Caddy erreichbar | systemd-Unit-Backup | SEC-016 |
| R-007 | 0–7 d | Restic-Restore-Probelauf | SHARED_INFRA | P0 | M | MED | R-003 | Sandkasten-Verzeichnis anlegen, letzte Snapshots restoren, SHA-Diff gegen Live für 5 Stichproben | Restore erfolgreich + Doku `docs/runbooks/backup-restore.md` | – (Probelauf isoliert) | SEC-026 |
| R-008 | 0–7 d | Zombie-/Restart-Loop-Services identifizieren | SHARED + LABS | P1 | S | LOW | – | `docker ps -a`, `systemctl --user list-units`, `journalctl --since '7 days ago' \| grep -i restart` auswerten | Liste der Services mit Restart-Counter >5 in `docs/architecture-planning/07_…` | – | – |
| R-009 | 8–30 d | OpenDisruption-Zielstruktur als leeres Skelett anlegen | OPENDISRUPTION_ROOT | P0 | M | LOW | R-001 | neues Verzeichnis `/Datenspeicher/OpenDisruption/` (oder Branch im neuen Git-Repo) mit allen Ordnern aus Phase 4 (leer, nur READMEs) | Skelett existiert, `tree -L 3` matches Spec | rm Verzeichnis | Phase 4 |
| R-010 | 8–30 d | Runtime-Datenstruktur unter `/Datenspeicher/OpenDisruption-Data/` anlegen | OPENDISRUPTION_ROOT | P0 | S | LOW | – | Ordnerstruktur leer + `secrets/` chmod 700 + README | Struktur existiert + Permissions korrekt | rm Verzeichnis | Phase 4 |
| R-011 | 8–30 d | Git initialisieren im Skelett + Pre-Commit-Hooks | OPENDISRUPTION_ROOT | P0 | M | LOW | R-009, R-004 | `git init`, `.gitignore` aus R-004 kopieren, Pre-Commit-Hooks (TruffleHog, gitleaks, black/ruff/eslint) installieren, ersten Commit „Skeleton" | `pre-commit run --all-files` grün; `git status` sauber | rm `.git` | SEC-025 |
| R-012 | 8–30 d | KIROBI-PWA migrieren (Top-Level + ggf. Benutzer-Ordner-Variante diff) | KIROBI | P1 | M | MED | R-009 | Diff zwischen `kirobi-pwa/` und `Benutzer-Ordner/Sven/Projekte/kirobi-pwa/`; Wahrheit nach `products/kirobi/apps/pwa/` migrieren; systemd-Unit anpassen | PWA startet aus neuem Pfad, alte Pfade als Symlink auf Übergangszeit | systemd-Unit-Backup + Symlink zurück | D5 |
| R-013 | 8–30 d | Telegram-Gateways migrieren | KIROBI | P1 | S | LOW | R-009 | `Orchestrierung-und-Agenten/01-Hermes/systemd/hermes-gateway-{sven,samira}.service` → `products/kirobi/gateways/telegram-{sven,samira}/` + Pfade in Units aktualisieren | systemctl reload; Bots antworten | Unit-Backup | – |
| R-014 | 8–30 d | Hermes-Agent-Source nach `infra/hermes-runtime/` migrieren, Runtime auslagern | SHARED_INFRA | P1 | L | MED | R-009 | Source kopieren; `.venv`, `image_cache/`, `audio_cache/`, `logs/`, `memories/` (sofern Runtime) nach `/Datenspeicher/OpenDisruption-Data/shared/hermes/` migrieren | `du -sh infra/hermes-runtime` < 200 MB; Agent läuft aus neuem Pfad | Komplett-Symlink zurück | SEC-028 |
| R-015 | 8–30 d | Qdrant konsolidieren | SHARED_INFRA | P1 | L | HIGH | R-014 | Snapshot Qdrant; alte `services/qdrant/`-Daten gegen `Systembetrieb-und-Indizes/qdrant/` diffen; eine Wahrheit nach `…OpenDisruption-Data/shared/qdrant/` migrieren; Collections umbenennen (`kirobi_*`, `luki_*`-Präfix) | Qdrant-API listet erwartete Collections; Top-K-Smoketest grün | Snapshot zurückrollen | SEC-013 |
| R-016 | 8–30 d | Live-DB-Volumes aus `data/` migrieren | LABS | P0 | M | HIGH | R-001, R-007 | Webshop-Stack stoppen, `mysqldump`+`tar` von `data/webshop-mysql/`+`data/webshop-wordpress/`, in `…OpenDisruption-Data/labs/webshop/{mysql,wordpress}/` ablegen, Compose-Mounts umstellen, Stack starten | Stack `healthy`, WP-Frontend erreichbar, Stichproben-Bestellung restorebar | Dumps zurückspielen, Mounts zurück | SEC-011/012 |
| R-017 | 8–30 d | `Benutzer-Ordner/LUKI/` extrahieren | LUKI | P1 | S | LOW | R-009 | nach `products/luki/runtime/agent-profile/` verschieben + Doku | dir existiert in LUKI-Tree, alter Pfad als Hinweis-README | rückverschieben | D-Spalte 03 |
| R-018 | 8–30 d | `Nutzeisen Prozessanalyse/` als LUKI-Quelle | LUKI | P1 | S | LOW | R-009 | nach `products/luki/source-docs/nutzeisen/` (Dateien außerhalb Repo, Hash-Manifest im Repo) | Manifest validiert (sha256 für jede Datei) | rückverschieben | – |
| R-019 | 8–30 d | Compose-Lücken schließen oder Services einfrieren | LABS | P2 | M | MED | R-009 | für Hindsight/Flowise/Open-WebUI/Mission-Control: Compose nachziehen (Volumes extern) ODER FREEZE-Stempel + Stop | jeder Service hat Compose oder ist nachweislich gestoppt | Snapshot R-001 | SEC-014 |
| R-020 | 8–30 d | Parallel-Tree `home-migration/OpenDisruption` archivieren | ARCHIVE | P2 | S | LOW | R-001 | Inhalts-Diff (rsync --dry-run vs. v0.1) → ARCHIVE in `…OpenDisruption-Data/archive/home-migration-tree-2026-05-26/` | Symlink `~/OpenDisruption` umbiegen oder löschen | Symlink zurück | SEC-027 |
| R-021 | 8–30 d | Erste Tests im Repo | OPENDISRUPTION_ROOT | P2 | M | LOW | R-011 | Minimal-Test-Suite (CI in Forgejo Actions / Github): pre-commit, dependency-scan, smoke-import auf Skills/Scripts | CI grün auf leerem Skelett | – | – |
| R-022 | 31–60 d | LUKI Knowledge: Ingest-Pipeline | LUKI | P0 | L | MED | R-015, R-018 | extract+chunk+embed-CLI in `products/luki/knowledge/`; Run auf Nutzeisen-Set | Collection `luki_knowledge_v1` enthält N Chunks; Stichproben-Retrieval grün | Collection drop | Phase 5 |
| R-023 | 31–60 d | LUKI Knowledge: Retrieval+Antwort-Service | LUKI | P0 | L | MED | R-022 | FastAPI-Service auf `127.0.0.1:8410`; System-Prompt mit Quellenpflicht; Refusal-Default | API antwortet auf Smoke-Set; 1 Refusal-Test grün | Service stoppen | Phase 5 |
| R-024 | 31–60 d | LUKI Audit-Log + Hashing | LUKI | P0 | S | LOW | R-023 | JSONL-Append + Hash-Mapping in `_unhashed/` chmod 600 | Audit-Eintrag pro Anfrage; `jq` parseable | Logging deaktivieren | Phase 5 |
| R-025 | 31–60 d | LUKI 50-Fragen-Eval + Bericht | LUKI | P0 | M | MED | R-023 | Goldset erstellen + Eval-Run + `report.md` | report.md mit Top1≥0.50 oder dokumentierter Mitigation | – | Phase 5 |
| R-026 | 31–60 d | LUKI Caddy-Route + BasicAuth | LUKI | P0 | S | LOW | R-005, R-023 | `/luki` → 8410 mit Auth aus `…/secrets/caddy.env`; nur Tailscale | curl-Test mit Auth grün, ohne Auth 401 | Route entfernen | – |
| R-027 | 31–60 d | Runbooks: Start/Stop/Backup/Restore/Incident | OPENDISRUPTION_ROOT | P0 | M | LOW | R-022..R-026 | `docs/runbooks/*.md` mit konkreten Befehlen | jede Runbook von Sven manuell durchgespielt | – | – |
| R-028 | 31–60 d | Monitoring-Stack (Loki/Promtail/Uptime-Kuma) | SHARED_INFRA | P1 | L | MED | R-009 | `infra/monitoring/compose.yml`; Telegram-Alerts Channel | Alerts feuern bei Service-Stop; Grafana hinter Caddy+Auth | Stack stoppen | – |
| R-029 | 61–90 d | LUKI Quick-Audit-Vorlage (für Pilotkunden) | LUKI | P1 | M | LOW | R-027 | strukturierter Fragebogen + Tooling-Checkliste | als PDF/MD im Repo + 1 Trockenlauf | – | – |
| R-030 | 61–90 d | LUKI Knowledge Pilot bei Nutzeisen | LUKI | P0 | L | HIGH | R-025, R-026, R-027 | Pilot-Installation On-Premise; 2–3 User onboarden; 2-Wochen-Begleitung | Eval mit echten Nutzerfragen, Zufriedenheits-Check, Audit-Stichprobe | Pilot stoppen, Daten löschen | – |
| R-031 | 61–90 d | Operator-Blueprint (Process/Document/Artikel/Wareneingang) | LUKI | P1 | M | MED | R-030 | je Operator Spec + Demo-Mock | Blueprint-Dokumente im Repo | – | – |
| R-032 | 61–90 d | Nutzeisen-Referenzcase + Demo-Paket | LUKI | P1 | M | LOW | R-030 | Case-Study (NDA-konform), 1-Pager + Demo-Skript + Folien | Demo-Paket lieferbar | – | – |
| R-033 | 61–90 d | Preismodell-Entwurf LUKI | LUKI | P2 | M | LOW | R-030 | 2–3 Preisstaffeln (Eval/Pilot/Prod), Lizenz-/Wartungsmodell | Dokument `products/luki/business/pricing-v1.md` | – | – |
| R-034 | 61–90 d | Go/No-Go WhatsApp/Teams/eNVenta-Middleware | LUKI | P1 | S | MED | R-030 | Entscheidungsdokument anhand Pilot-Erfahrung | klare Entscheidung dokumentiert | – | – |
| R-035 | 61–90 d | KIROBI-Avatar Entscheidung (KIROBI vs. LAB) | KIROBI | P2 | S | LOW | R-012 | Entscheidung E5 finalisieren | dokumentiert + entsprechende Migration | – | D-Spalte 03 |
| R-036 | 0–7 d | **DONE** kirobi-*-Stack archivieren | ARCHIVE | P0 | S | LOW | – | 13 orphan-Container von Compose-Projekt `opendisruption` removed | ✅ Phase A abgeschlossen | – | A-01 |
| R-037 | 8–30 d | Hindsight-Compose rekonstruieren | LABS | P2 | S | LOW | R-009 | `docker inspect hindsight` → `infra/hindsight/docker-compose.yml`; Bind 127.0.0.1 | Compose committed, Restart-fähig | bestehender Container | C-02 |
| R-038 | 8–30 d | 3d-druck-bar-preview-Compose rekonstruieren | LABS | P2 | XS | LOW | R-009 | wie R-037 für 8081-Service | Compose committed | wie oben | C-02 |
| R-039 | 8–30 d | Mission-Control-Service-Quelle klären | SHARED_INFRA | P1 | S | LOW | – | systemd? container? port 4100 → identifizieren | Komponente dokumentiert oder als gestoppt markiert | – | C-02 |
| R-040 | 8–30 d | Open-WebUI Compose erstellen | LABS | P2 | S | LOW | R-009 | Service unter `services/open-webui/` finalisieren, Bind 127.0.0.1 | Compose + Service-Start grün | – | C-02 |
| R-041 | 8–30 d | Hermes-Runtime → Data-Tree-Migration | SHARED_INFRA | P0 | M | MED | R-010 | `~/.hermes` → `…OpenDisruption-Data/shared/hermes/` + Symlink + Service-Restart | Telegram-Echo läuft, Daten in Restic-Backup | Symlink rückgängig, ~/.hermes.bak | C-03 |
| R-042 | 8–30 d | UFW-Backend-Lockdown | SHARED_INFRA | P0 | S | LOW | – | 18 Backend-Ports nur Tailscale/Docker/Loopback | LAN-Scan (von anderem Host) → ports closed | `sudo ufw disable` | C-01 |
| R-043 | 8–30 d | DB-PW-Rotation Webshop+Partdb | LABS | P1 | M | HIGH | R-016 | `ALTER USER` im Container + wp-config.php update + env_file aktualisieren | Stack startet mit neuen PWs, kein Datenverlust | DB-Dumps als Restore-Punkt | – |

## B) Critical Path

R-001 → R-002 → R-003 → R-007 → R-016 → R-015 → R-022 → R-023 → R-025 → R-030

(Snapshot → Quarantäne → Rotation → Restore-Test → DB-Volumes raus → Qdrant konsolidiert → LUKI Ingest → Retrieval → Eval → Pilot)

## C) Stop-Doing-List

- Neue Features in KIROBI/Labs starten, bevor Safety Baseline durch ist.
- Klartext-Secrets in Markdown-Audits oder Compose-Files schreiben.
- Services ohne Compose dauerhaft laufen lassen.
- Manuell gestartete `python script.py &` als Dauerdienst nutzen.
- Webshop-Live-DB-Volume in `data/` lassen.
- Parallele Codebase `home-migration/` weiter editieren.

## D) Decision Log (initial)

| Datum | Entscheidung | Begründung |
|---|---|---|
| 2026-05-26 | Wahrheits-Tree = `OpenDisruption_v0.1` | Nutzer-Antwort |
| 2026-05-26 | Externer Snapshot vor Phase A Pflicht | kein Git, kein Branch-Rollback |
| 2026-05-26 | Monorepo empfohlen | Solo-Owner, atomische Cross-Changes |
| 2026-05-26 | LUKI-MVP startet mit Knowledge | kleinster sinnvoller Schritt |
| 2026-05-27 | Restic-Repo NICHT rotieren | Repo intakt, 10 Snapshots — kein Schadensgrund |
| 2026-05-27 | kirobi-* Compose-Stack: ARCHIVE | Nutzer-Entscheidung — Experimentelles Setup |
| 2026-05-27 | PWA-Wahrheit: Top-Level `kirobi-pwa/` | Nutzer-Entscheidung |
| 2026-05-27 | Caddy-User: sven, samira, sineo, od-admin | Nutzer-Vorgabe |
| 2026-05-28 | DB-PW-Rotation deferred bis Phase E (mit DB-Konsolidierung) | Risiko vs. Nutzen — saubere Lösung braucht ohnehin Stack-Refactor |
| 2026-05-28 | Netz-Hardening Hybrid B+C: UFW jetzt, Network-Refactor später | sudo-Skript trivial, Compose-Refactor groß |

## E) Open Questions

- O1: InvenTree-Zuordnung (LUKI vs. LABS) — D1
- O2: Webshop in Repo oder eigenes Repo — D2
- O3: Backup-Ziel-Hardware — E2
- O4: Avatar-Domäne — E5
- O5: `kirobi-pwa` Wahrheits-Pfad — D5

## F) Migration Order (kurz)

Safety → Skeleton → Shared Infra → KIROBI → LUKI Extract → LUKI MVP → Docs → Business Readiness.

## G) Rollback Points

- nach R-001: vollständiger Snapshot existiert; jede spätere Phase kann auf diesen Stand zurück
- nach R-009: leeres Skelett ist verwerfbar (rm)
- nach R-011: Git-History erlaubt revert
- nach R-016: DB-Dumps + alte Volumes (in Snapshot) erlauben Rollback der Webshop-Stacks
- nach R-022: Qdrant-Collection drop = sauberer Re-Ingest
- nach R-030: Pilot-Daten löschen, Pilot pausieren

## H) Verification Checklist (lückenlos abzuhaken pro Aufgabe)

- [ ] Snapshot R-001 verifiziert (Datei-Anzahl, Größe)
- [ ] Keine Klartext-Secrets mehr im Repo (`grep -rEi '(token|password|api[_-]?key|secret|bearer)\s*[:=]' --include='*.{md,yml,yaml,env*}'` → nur MASKED)
- [ ] Alle Caddy-Routen geprüft und Admin-Routen hinter Auth
- [ ] Kirobi-PWA bindet 127.0.0.1
- [ ] Restic-Restore einmal erfolgreich durchgeführt
- [ ] Git-Repo initialisiert, Pre-Commit-Hooks aktiv
- [ ] Qdrant konsolidiert, Collections umbenannt
- [ ] LUKI-Eval mit Akzeptanzschwellen erreicht
- [ ] Runbooks von Sven manuell durchgespielt
- [ ] Pilot abgeschlossen + Case dokumentiert
