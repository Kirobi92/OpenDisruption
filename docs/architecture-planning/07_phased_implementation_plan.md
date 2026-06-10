# 07 — Phased Implementation Plan (A–H)

**Datum:** 2026-05-26 · **Regel:** Kein automatischer Übergang. Jede Phase wartet auf explizite `FREIGABE PHASE <X>`.

---

## PHASE A — Safety Baseline

**Ziel:** Datenverlust- und Leak-Risiko auf ein verantwortbares Niveau senken, bevor strukturelle Änderungen beginnen.

**Scope:**
- Externer Snapshot vor jeder Änderung (R-001).
- Klartext-Secret-Quarantäne (R-002).
- Secret-Rotation (R-003).
- Caddy-Härtung + Admin-BasicAuth (R-005).
- Kirobi-PWA auf 127.0.0.1 (R-006).
- Restic-Restore-Probelauf (R-007).
- Zombie-Service-Inventur (R-008).
- `.gitignore`-Skelett vorbereiten (R-004).

**Non-Scope:**
- Keine Verzeichnis-Umzüge in produktive Dienste.
- Keine Compose-Umstellungen.
- Kein Repo-Skelett.
- Keine LUKI-Arbeit.

**Precheck:**
- [ ] Zielplatte für externen Snapshot vorhanden, Schreibrechte verifiziert (`df -h /Datenspeicher/Backups`).
- [ ] Tailscale erreichbar (`tailscale status`).
- [ ] Restic-Binary verfügbar (`restic version`).
- [ ] Nutzer hat 30 Minuten Wartungsfenster zugesagt.
- [ ] Kein anderer Agent läuft im Tree.

**Dateien, die geändert werden DÜRFEN:**
- `services/caddy/Caddyfile`, `services/caddy/docker-compose.yml`
- `kirobi-pwa.service` (systemd Unit)
- `tools/templates/.gitignore` (neu)
- `/Datenspeicher/OpenDisruption-Data/secrets/*.env` (neu, chmod 600)
- `/Datenspeicher/OpenDisruption-Data/secrets/quarantine/` (neu)
- `docs/runbooks/backup-restore.md` (neu)

**Dateien, die NICHT geändert werden dürfen:**
- Inhalt der KIROBI-Privatordner (`Benutzer-Ordner/Samira/`, `Benutzer-Ordner/Sineo/`).
- `Nutzeisen Prozessanalyse/` (LUKI-Material).
- Live-DB-Volumes (`data/webshop-*`).
- Qdrant-Daten.

**Schritte:**
1. Snapshot: `rsync -aAX --numeric-ids /Datenspeicher/OpenDisruption_v0.1/ /Datenspeicher/Backups/OpenDisruption-pre-migration-2026-05-26/`; Manifest schreiben (`find … | wc -l`, `du -sh`).
2. Quarantäne: `AGENT-ACTIVITY-LOG.md` und (nach Inhaltsprüfung) `KIROBI_OS_AUDIT.md` nach `…/secrets/quarantine/` verschieben, chmod 600. Redigierte Kopien (Secrets → `MASKED`) im Repo belassen.
3. Secrets rotieren: Telegram-Tokens (3 Stück) via @BotFather neu; InvenTree-User-PW + API-Token neu; WooCommerce ck/cs regenerieren; Restic-Passphrase + neues Repo; Part-DB-Admin-PW; Webshop MySQL-PWs + WP-Admin. Neue Werte ausschließlich in `…/secrets/<svc>.env` (chmod 600).
4. Caddyfile: Admin-Routen (`/mission`, `/flowise`, `/webui`, `/luki`, `/3dbar`) mit `basicauth` versehen, PW-Hashes aus `…/secrets/caddy.env`. Caddy-Bind auf Tailscale-IP **oder** `127.0.0.1`. `auto_https on` mit lokaler CA.
5. `kirobi-pwa.service`: `Environment=HOST=127.0.0.1`; `systemctl daemon-reload && systemctl restart kirobi-pwa`; Caddy-Route `/kirobi` → `127.0.0.1:4300`.
6. Restic-Restore-Probelauf in `/tmp/restic-restore-test/`, SHA-Diff für 5 Stichprobendateien, Resultat in `docs/runbooks/backup-restore.md`.
7. `docker ps -a`, `systemctl --user list-units`, `journalctl --since '7 days ago' | grep -Ei 'restart|fail'` auswerten, Liste der Dauer-Restarter dokumentieren.
8. `tools/templates/.gitignore` mit harten Regeln (siehe R-004) anlegen.

**Tests:**
- Port-Scan Tailscale-IP und LAN-IP: keine offenen Admin-Routen ohne 401.
- `ss -ltnp | grep 4300` → nur `127.0.0.1`.
- `curl --user '<user>:<wrong-password>' https://caddy.lan/mission` → 401.
- Altes Telegram-Token: API-Call schlägt fehl (`getMe` → 401).
- Restic-Restore Stichproben-SHA stimmt.

**Verifikation:**
- [ ] Snapshot-Manifest existiert + verifiziert.
- [ ] `grep -rEi '(token|password|api[_-]?key|secret|bearer)\s*[:=]' --include='*.md' --include='*.yml' --include='*.yaml' --include='*.env*' /Datenspeicher/OpenDisruption_v0.1/` → nur MASKED-Treffer.
- [ ] Alle rotierten Secrets sind in `…/secrets/` (chmod 600).
- [ ] Caddy-Admin-Routen 401 ohne Auth.
- [ ] Kirobi-PWA nur Loopback.
- [ ] Restore-Test grün.

**Rollback:**
- Rotation: alte Secrets wurden vor Rotation in einem versiegelten Vault dokumentiert; falls Dienst kaputt, kurzfristig wiederherstellbar.
- Caddyfile-Backup `.bak.2026-05-26` zurückkopieren + `caddy reload`.
- systemd-Unit `.bak.2026-05-26` zurückkopieren.
- Snapshot R-001 ist immer der Restorepunkt.

**Risiken:**
- Telegram-Bots fallen kurz aus (geplant, Nutzer informieren).
- Webshop-Stack benötigt nach PW-Rotation Restart (Mini-Downtime).
- Caddy-Reload bei Tippfehler im Caddyfile → vorher `caddy validate`.

**Entscheidungspunkt am Ende:**
„FREIGABE PHASE B" durch Nutzer, sonst Halt.

---

## PHASE B — Repository Skeleton

**Ziel:** Leeres, sauberes Monorepo-Skelett mit Git, Pre-Commit-Hooks und CI als künftige Wahrheit; kein Code-Move noch.

**Scope:**
- Neue Wurzel `/Datenspeicher/OpenDisruption/` (oder Branch in eigener Git-Repo-Init im v0.1-Tree — Default: separate Wurzel).
- Ordnerskelett aus Phase 4.
- Runtime-Datenstruktur `/Datenspeicher/OpenDisruption-Data/`.
- `git init` + `.gitignore` + Pre-Commit-Hooks.
- Erste leere READMEs.
- Minimal-CI grün auf leerem Skelett.

**Non-Scope:**
- Keine Code-Migration aus v0.1.
- Keine Compose-Bewegungen.
- Kein Secret-Move.
- Keine Service-Restarts.

**Precheck:**
- [ ] PHASE A vollständig abgeschlossen + freigegeben.
- [ ] Genug freier Platz auf `/Datenspeicher` (`df -h`).
- [ ] Pre-Commit installiert (`pipx install pre-commit`).
- [ ] TruffleHog/gitleaks-Binaries vorhanden.

**Dateien, die geändert werden DÜRFEN:**
- Alles unterhalb von `/Datenspeicher/OpenDisruption/` (neu).
- `/Datenspeicher/OpenDisruption-Data/` (Ordnerstruktur, READMEs).

**Dateien, die NICHT geändert werden dürfen:**
- `/Datenspeicher/OpenDisruption_v0.1/` bleibt unangetastet (read-only Wahrheit bis Phase D/E).

**Schritte:**
1. `mkdir -p /Datenspeicher/OpenDisruption/{docs,infra,products/kirobi,products/luki,packages,tools,labs,archive}` (gemäß Phase 4 Abschnitt 3).
2. `mkdir -p /Datenspeicher/OpenDisruption-Data/{shared,kirobi,luki,labs,secrets,backups,archive}` (gemäß Phase 4 Abschnitt 4), `chmod 700 /Datenspeicher/OpenDisruption-Data/secrets`.
3. Jeder Ordner erhält `README.md` mit Zweck + Domäne + Owner.
4. `cd /Datenspeicher/OpenDisruption && git init -b main`.
5. `.gitignore` aus `tools/templates/.gitignore` kopieren.
6. `.pre-commit-config.yaml` (TruffleHog, gitleaks, ruff, black, eslint, prettier).
7. `pre-commit install && pre-commit run --all-files`.
8. CI-Skelett (`.forgejo/workflows/ci.yml` oder `.github/workflows/ci.yml`): pre-commit + dependency-scan + smoke-import.
9. Erster Commit: „Skeleton".

**Tests:**
- `git status` sauber.
- `pre-commit run --all-files` grün.
- CI-Pipeline grün.
- `tree -L 3 /Datenspeicher/OpenDisruption` matches Spec.

**Verifikation:**
- [ ] Skelett vollständig (jeder Ordner aus Spec existiert).
- [ ] `find /Datenspeicher/OpenDisruption -name '.env'` → leer.
- [ ] `ls -l /Datenspeicher/OpenDisruption-Data/secrets` → drwx------.

**Rollback:**
- `rm -rf /Datenspeicher/OpenDisruption /Datenspeicher/OpenDisruption-Data` (Skelett ist leer und verwerfbar).

**Risiken:**
- Falscher Pfad gewählt → vor `rm` Pfad doppelt prüfen.
- Pre-Commit-Hook blockiert spätere Commits unerwartet → Konfig testen.

**Entscheidungspunkt:** „FREIGABE PHASE C".

---

## PHASE C — Shared Infra Normalisierung

**Ziel:** Caddy, Hermes-Runtime, Qdrant, Ollama, Backups als saubere Shared-Infra in neue Struktur überführen, ohne KIROBI/LUKI-Funktion zu brechen.

**Scope:**
- Hermes-Source nach `infra/hermes-runtime/`; Runtime nach `…OpenDisruption-Data/shared/hermes/` (R-014).
- Qdrant konsolidieren in `…shared/qdrant/`; Collections umbenennen (`kirobi_*`, `luki_*`) (R-015).
- Ollama-Modelle in `…shared/ollama/models/`.
- Caddy-Compose in `infra/caddy/`, Volumes extern.
- Webshop-Volumes aus `data/` migrieren (R-016).
- Monitoring-Stack-Skelett (R-028, optional in dieser Phase).

**Non-Scope:**
- Keine KIROBI-PWA-Migration (Phase D).
- Keine LUKI-Code-Migration (Phase E).
- Keine Compose-Lücken für Labs schließen (Phase H).

**Precheck:**
- [ ] PHASE B abgeschlossen + freigegeben.
- [ ] Snapshot R-001 verifiziert.
- [ ] Restic-Restore funktioniert (PHASE A).
- [ ] Wartungsfenster mit Nutzer abgestimmt (Qdrant + Webshop kurz down).
- [ ] Aktuelle Qdrant-Snapshot vorhanden.

**Dateien, die geändert werden DÜRFEN:**
- Neue Struktur unter `/Datenspeicher/OpenDisruption/infra/`.
- Neue Volumes unter `/Datenspeicher/OpenDisruption-Data/shared/` und `…/labs/webshop/`.
- systemd-Units (`od-shared.service` neu, alte deaktivieren).
- Alte Pfade in v0.1 nur als Symlinks für Übergangszeit.

**Dateien, die NICHT geändert werden dürfen:**
- KIROBI-Privatdaten.
- LUKI-Quellmaterial.
- Hermes-Memories ohne Migration (nur kopieren, niemals löschen).

**Schritte:**
1. Hermes-Source `cp -a` nach `infra/hermes-runtime/`; `.venv`, `image_cache/`, `audio_cache/`, `logs/`, `memories/` nach `…shared/hermes/`. Compose anpassen (Volumes auf neuen Pfad).
2. Qdrant: aktiven Index snapshotten → in neues Volume `…shared/qdrant/` migrieren. Alte `services/qdrant/` (10 GB) nach `…archive/qdrant-legacy/`. Collections umbenennen: `kirobi_public`, `kirobi_family_shared`, später `luki_knowledge_v1`.
3. Ollama-Modelle nach `…shared/ollama/models/` (Symlink von `~/.ollama/models`).
4. Caddy: Compose nach `infra/caddy/compose.shared.yml`; `data/`, `config/` nach `…shared/caddy/`.
5. Webshop: Stack stoppen, `mysqldump` + `tar` der WP-Files, in `…labs/webshop/{mysql,wordpress}/` ablegen, Compose-Mounts umstellen, Stack starten, Smoke-Test (Frontend lädt, Login funktioniert, Testbestellung lesbar).
6. systemd-Units: `od-shared.service` (Compose-Wrapper), alte Einzelunits deaktivieren.
7. Monitoring-Skelett (optional): `infra/monitoring/compose.yml` mit Uptime-Kuma.

**Tests:**
- Hermes startet aus neuem Pfad, ein Skill-Aufruf grün.
- Qdrant `/collections` listet erwartete Collections, Top-K-Smoketest grün.
- Ollama `ollama list` zeigt alle Modelle.
- Caddy `caddy validate` grün, alle Routen erreichbar mit Auth.
- WordPress-Frontend grün, MySQL-Verbindung steht.
- Uptime-Kuma erreichbar via Caddy + Auth.

**Verifikation:**
- [ ] `du -sh /Datenspeicher/OpenDisruption/infra/hermes-runtime` < 200 MB.
- [ ] `data/webshop-*` ist leer/Symlink, Volumes leben in `…labs/webshop/`.
- [ ] Qdrant alter Pfad existiert nur als Archiv.
- [ ] Healthchecks aller Stacks grün.

**Rollback:**
- Qdrant: Snapshot zurückrollen, Compose-Mount zurück.
- Webshop: alte Dumps wieder einspielen, Compose-Mounts zurück.
- Hermes: Symlinks rückwärts.
- Snapshot R-001 ist Notfallrettung.

**Risiken:**
- Qdrant-Migration verliert Collection-Daten → Vor-Snapshot Pflicht.
- Webshop-Downtime länger als geplant → Wartungsfenster + Pre-Generation der Dumps.
- Hermes-Memories-Pfade nicht aktualisiert → Skills brechen → Smoketest vor produktivem Schalten.

**Entscheidungspunkt:** „FREIGABE PHASE D".

---

## PHASE D — KIROBI Cleanup

**Ziel:** KIROBI-Wahrheit in `products/kirobi/` etablieren, doppelte PWA-Quelle auflösen, Telegram-Gateways konsolidieren, Privatdaten in Runtime-Tree.

**Scope:**
- PWA-Migration (R-012), Wahrheitsauswahl (Open Question D5).
- Telegram-Gateways nach `products/kirobi/gateways/telegram-{sven,samira}/` (R-013).
- KIROBI-Skills aus `Orchestrierung-und-Agenten/01-Hermes/` nach `products/kirobi/skills/`.
- Family-Private-Daten nach `…OpenDisruption-Data/kirobi/private/{Sven,Samira,Sineo}/`.
- Family-Shared nach `…OpenDisruption-Data/kirobi/shared/`.
- Avatar-Entscheidung (D3/E5).

**Non-Scope:**
- Kein LUKI-Move.
- Keine Labs-Bewegung.
- Keine Schemaänderungen an Hermes-Skills.

**Precheck:**
- [ ] PHASE C freigegeben.
- [ ] Nutzer hat D5 (PWA-Wahrheit) entschieden.
- [ ] Nutzer hat D3/E5 (Avatar-Domäne) entschieden.
- [ ] Telegram-Bots laufen stabil (von Phase A).

**Dateien, die geändert werden DÜRFEN:**
- `products/kirobi/**` (neu).
- `…OpenDisruption-Data/kirobi/**`.
- systemd-Units der Telegram-Gateways.

**Dateien, die NICHT geändert werden dürfen:**
- LUKI-Material.
- Shared-Infra-Komponenten (sind in Phase C abgeschlossen).
- KIROBI-Privatdaten ohne Migration (`cp -a`, niemals `mv` ohne Backup).

**Schritte:**
1. PWA-Diff (`diff -r kirobi-pwa/ Benutzer-Ordner/Sven/Projekte/kirobi-pwa/`); Wahrheit nach `products/kirobi/apps/pwa/`; Symlink vom Alt-Pfad für 30 Tage.
2. Telegram-Gateway-Units anpassen (Pfade), `systemctl daemon-reload`, Bots Antwort-Test.
3. Skills migrieren; Hermes neu starten; Smoketest Skill-Liste.
4. Privatdaten kopieren (`rsync -aAX --numeric-ids`); Hashvergleich Stichprobe; Originale erst nach Verifikation entfernen (oder zunächst belassen).
5. Falls Avatar = KIROBI: nach `products/kirobi/apps/avatar/`. Falls Avatar = LAB: nach `labs/avatar/`.

**Tests:**
- PWA lädt aus neuem Pfad (Tailscale-Browsertest).
- Beide Telegram-Bots antworten auf `/ping`.
- 3 Hermes-Skills (random ausgewählt) funktionieren.
- Privatdaten in neuem Pfad SHA-identisch zur Quelle.

**Verifikation:**
- [ ] `ls /Datenspeicher/OpenDisruption/products/kirobi/apps/pwa` enthält Quelle.
- [ ] Alter PWA-Pfad ist Symlink (oder gelöscht).
- [ ] Bots-Last-Message-Time aktuell.
- [ ] Skill-Smoketest grün.

**Rollback:**
- systemd-Unit `.bak` zurück.
- Symlink-Auflösung rückwärts.
- Privatdaten Original-Tree bleibt im Snapshot R-001.

**Risiken:**
- Falscher PWA-Tree gewählt → Diff-Review zwingend dokumentieren.
- Telegram-Bot-Token-Verwirrung → Tokens stammen aus `…secrets/telegram-*.env`, nicht aus Unit.

**Entscheidungspunkt:** „FREIGABE PHASE E".

---

## PHASE E — LUKI Extraction

**Ziel:** LUKI-Material (Source-Dokumente, Agent-Profile, Business-Wissensbasis) aus dem Misch-Tree in `products/luki/` und `…OpenDisruption-Data/luki/` extrahieren — **noch ohne MVP-Stack**.

**Scope:**
- `Benutzer-Ordner/LUKI/` → `products/luki/runtime/agent-profile/` (R-017).
- `Nutzeisen Prozessanalyse/` → `…OpenDisruption-Data/luki/source-docs/`, Hash-Manifest in `products/luki/source-docs/manifest.json` (R-018).
- `Geteilte-Wissensbasis/04-Business-und-Kunden/` → `products/luki/canon/business/`.
- `Unternehmensstruktur/` (LUKI-Teile: Hardware/Software/Web3) → `products/luki/canon/orga/`; (Lab-Teile: 3d-druck, lebenscoach) bleiben für Phase H.
- Decision D1 (InvenTree) umsetzen.

**Non-Scope:**
- Kein LUKI-Code (kommt in Phase F).
- Kein KIROBI-Material.
- Keine Secret-Migration (war Phase A).

**Precheck:**
- [ ] PHASE D freigegeben.
- [ ] Nutzer hat D1 (InvenTree-Domäne) entschieden.
- [ ] Nutzer hat D4 (lebenscoach/web3-Eigentum) entschieden.

**Dateien, die geändert werden DÜRFEN:**
- `products/luki/**` (neu).
- `…OpenDisruption-Data/luki/source-docs/**`.

**Dateien, die NICHT geändert werden dürfen:**
- KIROBI-Tree.
- Shared-Infra.
- Webshop-Daten.

**Schritte:**
1. `Benutzer-Ordner/LUKI/` → `products/luki/runtime/agent-profile/` (`cp -a`, dann nach Verifikation Originale archivieren).
2. `Nutzeisen Prozessanalyse/` → `…OpenDisruption-Data/luki/source-docs/`; SHA256 pro Datei in `products/luki/source-docs/manifest.json`.
3. Business-Canon migrieren.
4. Unternehmensstruktur split: LUKI-Anteile nach `products/luki/canon/orga/`; Labs-Anteile mit FREEZE-Marker für Phase H.
5. InvenTree-Entscheidung umsetzen: entweder `products/luki/integrations/inventree/` oder `labs/inventory/inventree/`.

**Tests:**
- Manifest-Validierung: `python -c "import json,hashlib,pathlib; …"` prüft jede gelistete Datei.
- `git status` zeigt nur erwartete Adds.
- KIROBI-Tree unverändert (`diff -r` gegen Snapshot Stichprobe).

**Verifikation:**
- [ ] Hash-Manifest grün.
- [ ] Keine Nutzeisen-Dateien mehr im Repo (nur Manifest).
- [ ] LUKI-Tree enthält Profile + Canon + (ggf.) InvenTree-Integration.

**Rollback:**
- Kopierte Originale bleiben bis Phase F-Abschluss erhalten.
- Snapshot R-001 als letzter Rettungsanker.

**Risiken:**
- Source-Docs versehentlich ins Repo committen → `.gitignore` schließt `products/luki/source-docs/*.{pdf,docx}` explizit aus.
- Verwechslung Privat- vs. Business-Tree → vor `mv` immer `ls -la` zeigen.

**Entscheidungspunkt:** „FREIGABE PHASE F".

---

## PHASE F — LUKI Knowledge MVP

**Ziel:** Funktionsfähiger LUKI-Knowledge-Stack mit Ingest, Retrieval, Audit-Log und Eval — lokal, gehärtet, dokumentiert.

**Scope:**
- Ingest-CLI (R-022).
- Retrieval-/Antwort-Service auf 127.0.0.1:8410 (R-023).
- Audit-Log + Hashing (R-024).
- 50-Fragen-Eval + Bericht (R-025).
- Caddy-Route + BasicAuth (R-026).

**Non-Scope:**
- Kein Multi-Tenant.
- Keine Operatoren (Process/Document/Artikel/Wareneingang) — nach MVP.
- Keine WhatsApp/Teams-Brücke.
- Kein ERP-Schreiben.

**Precheck:**
- [ ] PHASE E freigegeben.
- [ ] Qdrant in Shared-Infra läuft.
- [ ] Ollama hat passendes Embedding-Modell + LLM gepullt.
- [ ] Source-Docs-Manifest gültig.
- [ ] LUKI-Secrets in `…secrets/luki.env`.

**Dateien, die geändert werden DÜRFEN:**
- `products/luki/{knowledge,retrieval,audit,evals,compose.luki.yml,config}/**`.
- `infra/caddy/Caddyfile` (nur LUKI-Route).
- `…OpenDisruption-Data/luki/{ingest-staging,audit,evals}/**`.

**Dateien, die NICHT geändert werden dürfen:**
- KIROBI-Collections.
- Webshop-Stack.
- Hermes-Skills.

**Schritte:**
1. Ingest: extract (pypdfium/textract) → normalize → chunk(800/150) → embed (Ollama `nomic-embed-text`) → Qdrant upsert in `luki_knowledge_v1`. CLI: `python -m luki.knowledge.ingest --batch …`.
2. Retrieval-Service: FastAPI auf `127.0.0.1:8410`, System-Prompt mit Quellenpflicht + Refusal-Default, Top-K=8, Score-Threshold konfigurierbar.
3. Audit-Log: append-only JSONL pro Anfrage; Hashing für User/Frage/Antwort; Mapping-Tabelle in `_unhashed/` (chmod 600, nicht in Backups die das Haus verlassen).
4. Eval-Goldset (50 Fragen) in `products/luki/evals/v1/questions.json`; Run-Skript erzeugt `report.md`.
5. Caddy-Route `/luki` → 8410 mit BasicAuth aus `…secrets/caddy.env`; nur Tailscale.
6. Whitelist-Test: Service darf nur `luki_*`-Collections lesen (Qdrant-Client-Allowlist).

**Tests:**
- Ingest auf Goldset-Quellen erzeugt N Chunks.
- Smoke-Frage über API liefert Antwort mit ≥1 Quelle.
- Frage außerhalb Material → „Ich weiß es nicht".
- Eval-Run: Top1≥0.50, Top3≥0.75, Halluzinationsrate≤0.10.
- Audit-Log parseable (`jq -c . < luki-audit-*.jsonl`).
- Whitelist-Test: Versuch auf `kirobi_*` schlägt fehl.
- `curl --user '<user>:<wrong-password>' https://lan/luki/ask` → 401.

**Verifikation:**
- [ ] Eval-Bericht im Repo.
- [ ] Akzeptanzschwellen erreicht ODER Mitigation dokumentiert.
- [ ] Audit-Log existiert pro Anfrage.
- [ ] Restore-Test für LUKI-Volume in `docs/runbooks/luki-backup-restore.md`.

**Rollback:**
- Collection drop: `qdrant collection delete luki_knowledge_v1` → sauberer Re-Ingest.
- Service stoppen, Caddy-Route entfernen.
- Audit-Logs bleiben (Read-Only).

**Risiken:**
- PDF-Extraction-Qualität schwach → OCR-Fallback dokumentieren, Lücken im Audit.
- Embedding-Modell zu schwach für DE → bge-m3 als Alternative vorbereiten.
- Cross-Collection-Leak → Whitelist-Test im CI verankern.

**Entscheidungspunkt:** „FREIGABE PHASE G".

---

## PHASE G — Documentation & Runbooks

**Ziel:** Betriebsfähigkeit ohne stillschweigendes Wissen herstellen. Jede betriebliche Tätigkeit ist runbookbasiert.

**Scope:**
- Runbooks: Start/Stop pro Stack, Backup, Restore, Incident, On-Call.
- LUKI-Demo-Skript für Nutzeisen.
- Architektur-Diagramme (C4 light) als Markdown + Mermaid.
- Security-Doku: Zonen-Modell, Cloud-Policy, Secret-Policy.
- Update-Doku: Image-Bump-Prozess, Test-Cycle.
- Monitoring-Doku: Alerts-Kanäle, Eskalationspfade.

**Non-Scope:**
- Keine neuen Features.
- Keine Code-Änderungen außer in Runbook-Code-Schnipseln.

**Precheck:**
- [ ] PHASE F freigegeben.
- [ ] Monitoring-Stack steht (Uptime-Kuma mindestens).

**Dateien, die geändert werden DÜRFEN:**
- `docs/runbooks/**`, `docs/security/**`, `docs/architecture-planning/**` (nur additiv).
- `products/luki/runbooks/**`.

**Dateien, die NICHT geändert werden dürfen:**
- Service-Code.
- Compose-Files (außer Healthcheck-Ergänzungen, falls Lücken auffallen — dann eigene Mini-Phase).

**Schritte:**
1. Runbook-Set: `start-stop-shared.md`, `start-stop-kirobi.md`, `start-stop-luki.md`, `backup-restore.md`, `incident-luki.md`, `incident-webshop.md`, `secret-rotation.md`.
2. LUKI Demo-Skript `products/luki/runbooks/demo-nutzeisen.md`.
3. Diagramme: Domain-Boundaries, Netz, Datenflüsse.
4. Security-Doku in `docs/security/`.
5. Update-Prozess `docs/runbooks/updates.md`.
6. Sven läuft jedes Runbook einmal manuell durch, korrigiert Lücken.

**Tests:**
- Trockenlauf jedes Runbooks durch Sven; Ergebnis dokumentiert.
- `grep -L 'Last verified' docs/runbooks/*.md` → leer.

**Verifikation:**
- [ ] Jedes Runbook hat „Last verified"-Datum.
- [ ] Demo-Skript erfolgreich vorgeführt.

**Rollback:**
- Doku ist additiv, keine Service-Wirkung; Git-Revert genügt.

**Risiken:**
- Doku läuft Realität hinterher → Quartals-Refresh festlegen.

**Entscheidungspunkt:** „FREIGABE PHASE H".

---

## PHASE H — Business Readiness

**Ziel:** LUKI pilotreif bei Nutzeisen; Labs-Stand klären (laufen, einfrieren, archivieren); Geschäftsartefakte (Preis/Demo/Case) vorbereiten.

**Scope:**
- LUKI Pilot On-Premise bei Nutzeisen (R-030).
- Quick-Audit-Vorlage (R-029).
- Operator-Blueprints (R-031).
- Referenzcase + Demo-Paket (R-032).
- Preismodell-Entwurf (R-033).
- Middleware-Entscheidung (R-034).
- Labs-Audit: jeder Lab-Service entweder Compose vollständig + Volumes extern + dokumentiert, ODER FREEZE-Stempel + Stop (R-019).
- `home-migration/`-Tree archivieren (R-020).

**Non-Scope:**
- Keine Multi-Tenant-Architektur.
- Kein Cloud-LLM.
- Keine Werbe-/Marketing-Automation.

**Precheck:**
- [ ] PHASE G freigegeben.
- [ ] Nutzeisen hat Pilot-Slot zugesagt.
- [ ] Backup-Restore-Test bei Pilot-Hardware grün.

**Dateien, die geändert werden DÜRFEN:**
- `products/luki/business/**` (Pricing, Case).
- `labs/<lab>/**` (Compose nachziehen oder FREEZE).
- `archive/home-migration-tree/**` (Verschiebung).

**Dateien, die NICHT geändert werden dürfen:**
- KIROBI-Privatdaten.
- LUKI-Audit-Mapping `_unhashed/` (verlässt nie Pilot-Hardware).

**Schritte:**
1. Pilot-Installation bei Nutzeisen (Compose-Bundle aus PHASE F), 2–3 User onboarden.
2. 2-Wochen-Begleitung, echte Fragen sammeln, Feedback einarbeiten.
3. Audit-Stichprobe + Eval-Run mit Realfragen.
4. Case-Study (NDA-konform), Demo-Paket, Preismodell-Entwurf.
5. Operator-Blueprints (Process/Document/Artikel/Wareneingang) als Specs.
6. Middleware-Entscheidung (WhatsApp/Teams/eNVenta) dokumentiert.
7. Labs: pro Service Compose schließen oder FREEZE + Stop; `home-migration/`-Tree archivieren.

**Tests:**
- Pilot-Eval-Bericht.
- Restore-Test auf Pilot-Hardware.
- Labs-Audit-Tabelle: Status pro Lab.

**Verifikation:**
- [ ] Pilot abgeschlossen + Case dokumentiert.
- [ ] Jeder Lab-Service hat klaren Zustand (LIVE+Compose / FREEZE / ARCHIVE).
- [ ] `home-migration/`-Tree nur noch in Archive.
- [ ] Preismodell + Demo + Operator-Blueprints im Repo.

**Rollback:**
- Pilot stoppen, Daten löschen, Pilot-Hardware zurückbauen.
- Labs-FREEZE rückgängig durch Stack-Start.

**Risiken:**
- Pilot-Erwartung übersteigt MVP-Scope → Demo-Skript klar mit Non-Scope.
- Labs-FREEZE bricht versteckte Abhängigkeiten → vor FREEZE Inbound-Check (welcher Stack ruft was).

**Entscheidungspunkt:** Projekt-Review mit Nutzer; weitere Roadmap (Multi-Tenant, Cloud-Pilot, Operatoren v1) als neue Planung.

---

## Querschnittsregeln (gelten in jeder Phase)

- Jede schreibende Aktion → Backup-Punkt benannt und verfügbar.
- Jede Secret-Berührung → MASKED in Doku, Klartext nur in `…secrets/`.
- Jede Service-Migration → vor/nach-Smoketest.
- Jede Phase endet mit explizitem Halt, niemals automatisch in die nächste.
- Bei jedem Zweifel: STOPP + Nutzer fragen.
