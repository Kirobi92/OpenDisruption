# Phase-A Report — Zombie- & Restart-Loop-Inventur (R-008)

**Datum:** 2026-05-27 · **Methode:** `docker ps -a`, `systemctl list-units`, `journalctl --since '7 days ago' | grep -Ei 'restart|fail'`

## A) Laufende Container (HEALTHY)

| Container | Status | Ports | Domäne | Bewertung |
|---|---|---|---|---|
| `partdb` | Up 3 days | `0.0.0.0:8200->80` | LABS | LAN-Bind (SEC-017) — in Phase C umstellen |
| `partdb-db` | Up 3 days (healthy) | 3306/33060 (intern) | LABS | OK |
| `homebox` | Up 3 days (healthy) | `0.0.0.0:8201->7745` | LABS | LAN-Bind — in Phase C umstellen |
| `webshop-wordpress` | Up 3 days | `0.0.0.0:9001->80` | LABS | LAN-Bind, MySQL-PW im Klartext (SEC-001/002) |
| `webshop-mysql` | Up 3 days | `0.0.0.0:3307->3306` | LABS | **KRITISCH:** MySQL extern erreichbar |
| `webshop-postgres` | Up 3 days (healthy) | `0.0.0.0:5433->5432` | LABS | **KRITISCH:** Postgres extern erreichbar |
| `webshop-redis` | Up 3 days | `0.0.0.0:6380->6379` | LABS | **KRITISCH:** Redis extern erreichbar |
| `opendisruption-caddy` | Up 31h | `0.0.0.0:80->80` | SHARED_INFRA | OK (Caddy soll extern sein), aber HTTP only (SEC-015) |
| `opendisruption-website` | Up 3 days | `0.0.0.0:8080->80` | LABS | OK aber LAN-Bind |
| `3d-druck-bar-preview` | Up 3 days | `0.0.0.0:8081->80` | LABS | LAN-Bind |
| `inventree-3ddruck` | Up 3 days (healthy) | `0.0.0.0:4999->8000` | LABS/LUKI (D1) | LAN-Bind |
| `hindsight` | Up 3 days | `0.0.0.0:5300->8888`, `0.0.0.0:5301->9999` | LABS | LAN-Bind |

## B) Exited Container (kirobi-*-Microservice-Stack — NEU ENTDECKT)

Dies ist ein bisher in Phase 1 nicht dokumentierter Stack. Vermutung: aus `/Datenspeicher/home-migration/OpenDisruption/` oder eigener `kirobi-core`-Tree. Status: **alle exited seit 2 Tagen** — kein Health-State, keine Restarts.

| Container | Exit-Code | Vermutete Quelle | Empfehlung |
|---|---|---|---|
| `kirobi-api` | 0 | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-ingest` | 0 | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-retrieval` | 0 | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-embeddings` | 0 | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-qdrant` | 143 (SIGTERM) | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-ollama` | 0 | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-image-generation` | 0 | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-media-processing` | 0 | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-video-generation` | 0 | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-music-generation` | 0 | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-auth` | 0 | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-postgres` | 0 | home-migration-Tree | UNKNOWN_NEEDS_MANUAL_CHECK |
| `kirobi-nutzi` | 255 (Fehler) | LUKI/Nutzeisen-Container | UNKNOWN_NEEDS_MANUAL_CHECK + DEBUG |

**Auswirkung auf Plan:**
- Bestätigt **SEC-027** (Parallel-Codebase): nicht nur Code, auch Compose-Stacks driften. `home-migration/`-Tree ist nicht inaktiv, sondern hatte mindestens vor 2 Tagen laufende Container.
- Aufnahme in Roadmap nötig: **R-036 (neu)** — kirobi-*-Stack-Audit und Entscheidung (KEEP/MIGRATE/ARCHIVE) vor PHASE B.

## C) systemd Units — kritische Befunde

| Unit | Status | Bewertung |
|---|---|---|
| `kirobi-backup.service` | **FAILED** | **KRITISCH:** Restic-Backup läuft nicht. Verstärkt **SEC-026** (Backup unzuverlässig). Restore-Test in PHASE A wird auf bestehende Snapshots nötig — falls keine vorhanden, ist Backup-Lücke seit X Tagen offen. |
| `kirobi-apk-compare.service` | FAILED | mittlere Priorität (KIROBI-Build-Pipeline) |
| `kirobi-pwa.service` | inactive (dead) | **HINWEIS:** Service ist gar nicht aktiv. Phase D PWA-Migration muss prüfen, ob PWA überhaupt produktiv läuft oder ob Tree veraltet ist. |
| `kirobi-system-monitor.service` | inactive | – |
| `kirobi-weekly-revenue.service` | inactive | – |
| `kirobi-coverage-trend-sync.service` | inactive | – |
| `kirobi-vitest-drift-check.service` | inactive | – |
| `ollama.service` | active (running) | OK — Ollama via systemd auf Host |

## D) journalctl-Befunde (7 Tage)

- **Tailscale:** wiederkehrende `portmapper: failed to get PCP mapping` → kosmetisch (NAT-Router unterstützt PCP nicht). Empfehlung: deaktivieren oder ignorieren.
- **Tailscale DNS-SERVFAIL** am 24.05. 09:01 — DNS-Forward-Fehler. **Action:** DNS-Setup prüfen, sonst Tailscale-Lookups instabil.
- **kirobi-apk-compare** Failures wöchentlich → Pipeline reparieren oder deaktivieren.
- Keine Restart-Loops bei Produktion-Containern in 7 Tagen.

## E) Action-Items für Phase A

1. **SOFORT (P0):** `kirobi-backup.service`-Failure-Ursache klären — vermutlich altes Repo-PW (Verkettung mit SEC-009 Restic-Rotation). **Vor R-007 Restore-Probelauf zwingend prüfen, ob aktuelle Snapshots existieren.**
2. **P0:** R-036 (neu) — kirobi-*-Container-Stack inventarisieren (welches `compose.yml`, woher), Entscheidung KEEP/MIGRATE/ARCHIVE.
3. **P1:** Tailscale-DNS-Setup prüfen (interne `.lan`-Auflösung).
4. **P2:** `kirobi-apk-compare` reparieren oder ausschalten.

## F) Neue Roadmap-Aufgabe (Nachtrag)

| ID | Zeitraum | Titel | Domäne | Prio | Aufwand | Risiko | Aktion |
|---|---|---|---|---|---|---|---|
| R-036 | 0–7 d | kirobi-*-Microservice-Stack inventarisieren | UNKNOWN | P0 | S | LOW | `docker inspect` auf jeden `kirobi-*`-Container → `Labels.com.docker.compose.project` + `working_dir`, daraus Compose-Pfad ermitteln. Klären: home-migration-Tree oder eigener Pfad. Entscheidung: KEEP (in Phase C aufnehmen), MIGRATE (eigene Phase), ARCHIVE (mit `docker rm`). |
