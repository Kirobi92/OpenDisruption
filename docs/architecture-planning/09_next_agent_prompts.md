# 09 — Next Agent Prompts

**Datum:** 2026-05-26 · **Regel:** Jeder Agent wird vom Nutzer einzeln freigegeben. Kein Agent startet eine Folgephase. Bei jedem Zweifel: STOPP + Rückfrage.

---

## Agent 1 — Security-Hardening (PHASE A)

**Ziel:** Datenverlust- und Leak-Risiko auf verantwortbares Niveau senken (Snapshot, Secret-Quarantäne, Rotation, Caddy-Härtung, Loopback-Bindings, Restic-Restore-Test).

**Erlaubte Dateien/Pfade:**
- `services/caddy/Caddyfile`, `services/caddy/docker-compose.yml`
- `kirobi-pwa.service`
- `tools/templates/.gitignore` (neu)
- `/Datenspeicher/OpenDisruption-Data/secrets/**` (neu, chmod 600)
- `/Datenspeicher/OpenDisruption-Data/secrets/quarantine/**` (neu)
- `docs/runbooks/backup-restore.md` (neu)
- `/Datenspeicher/Backups/OpenDisruption-pre-migration-2026-05-26/` (Snapshot-Ziel)

**Verbotene Aktionen:**
- Keine Inhalte aus `Benutzer-Ordner/Samira/`, `Benutzer-Ordner/Sineo/`, `Nutzeisen Prozessanalyse/` lesen oder bewegen.
- Keine Repo-Umstrukturierung.
- Keine LUKI-Arbeit.
- Niemals Klartext-Secrets in Outputs oder Logs.

**Precheck:**
- [ ] Snapshot-Ziel-Platte mit ≥3× Repo-Größe frei.
- [ ] `tailscale status` grün.
- [ ] Restic-Binary verfügbar.
- [ ] Wartungsfenster 30–60 min bestätigt.

**Arbeitsschritte:**
1. `rsync -aAX --numeric-ids` Snapshot + Manifest (`find | wc -l`, `du -sh`).
2. `AGENT-ACTIVITY-LOG.md` und (nach Inhaltsprüfung) `KIROBI_OS_AUDIT.md` → `…/secrets/quarantine/` (chmod 600). Redigierte Kopien (Secrets → `MASKED`) im Repo lassen.
3. Secrets rotieren: 3× Telegram-Tokens, InvenTree-PW + API-Token, WooCommerce ck/cs, Restic-Passphrase + neues Repo, Part-DB-Admin-PW, Webshop MySQL + WP-Admin. Neue Werte in `…/secrets/<svc>.env`.
4. Caddyfile: `basicauth` für `/mission`, `/flowise`, `/webui`, `/luki`, `/3dbar`. Bind nur Tailscale-IP / 127.0.0.1. `auto_https on` mit lokaler CA.
5. `kirobi-pwa.service`: `HOST=127.0.0.1`, reload + restart, Caddy-Route `/kirobi` → 127.0.0.1:4300.
6. Restic-Restore-Probelauf in Sandkasten, SHA-Diff 5 Stichproben.
7. Zombie-Check (`docker ps -a`, `journalctl --since '7 days ago' | grep -Ei 'restart|fail'`).

**Tests:**
- Port-Scan LAN: keine offenen Admin-Endpoints ohne 401.
- `ss -ltnp | grep 4300` → nur Loopback.
- Alte Telegram-Tokens → `getMe` 401.
- Restic-Restore Stichproben-SHA stimmt.
- `grep -rEi '(token|password|api[_-]?key|secret|bearer)\s*[:=]' --include='*.md' --include='*.yml' --include='*.env*' /Datenspeicher/OpenDisruption_v0.1` → nur MASKED.

**Output:**
- Bericht `docs/architecture-planning/reports/A-safety-baseline-<datum>.md` mit: erledigte Schritte, Verifikationsresultate, offene Befunde.

**Rollback:**
- `.bak`-Backups von Caddyfile + systemd-Unit zurückkopieren.
- Snapshot R-001 als letzter Anker.

**Abbruchkriterien:**
- Snapshot schlägt fehl oder Größenprüfung weicht ab.
- Rotierte Secrets verifizierbar nicht eingespielt.
- Caddy `validate` schlägt fehl.
- Restic-Restore-Stichprobe-Diff ≠ 0.
→ STOPP, Rollback, Nutzer informieren.

---

## Agent 2 — Repo-Skeleton (PHASE B)

**Ziel:** Leeres Monorepo-Skelett + Runtime-Datenstruktur + Git + Pre-Commit-Hooks + minimale CI.

**Erlaubte Dateien/Pfade:**
- Alles unterhalb `/Datenspeicher/OpenDisruption/` (neu).
- `/Datenspeicher/OpenDisruption-Data/{shared,kirobi,luki,labs,secrets,backups,archive}/` (Ordnerstruktur + READMEs).

**Verbotene Aktionen:**
- Keine Datei aus `/Datenspeicher/OpenDisruption_v0.1/` lesen/schreiben (bleibt unangetastet bis Phase D/E).
- Keine echten Secrets in `.env.template`.

**Precheck:**
- [ ] PHASE A abgeschlossen + freigegeben.
- [ ] Pre-Commit + TruffleHog + gitleaks installiert.

**Arbeitsschritte:**
1. Ordnerstruktur gemäß `04_target_architecture.md` Abschnitte 3 + 4 anlegen.
2. Jeder Ordner: `README.md` mit Zweck + Domäne + Owner.
3. `git init -b main` in `/Datenspeicher/OpenDisruption/`.
4. `.gitignore` aus `tools/templates/.gitignore`.
5. `.pre-commit-config.yaml` (TruffleHog, gitleaks, ruff, black, eslint, prettier).
6. `pre-commit install && pre-commit run --all-files`.
7. CI-Workflow (`.forgejo/workflows/ci.yml`): pre-commit + dependency-scan + smoke-import.
8. Erster Commit „Skeleton".

**Tests:**
- `git status` sauber.
- `pre-commit run --all-files` grün.
- CI grün.
- `tree -L 3` matches Spec.
- `find /Datenspeicher/OpenDisruption -name '.env' -not -name '*.template'` → leer.
- `ls -ld /Datenspeicher/OpenDisruption-Data/secrets` → `drwx------`.

**Output:**
- Bericht `…/reports/B-repo-skeleton-<datum>.md`.

**Rollback:**
- `rm -rf /Datenspeicher/OpenDisruption /Datenspeicher/OpenDisruption-Data` (vorher Pfad doppelt prüfen).

**Abbruchkriterien:**
- Pre-Commit-Hook blockiert sauberes Skelett.
- CI rot trotz leerem Tree.
→ STOPP, Konfig korrigieren, Nutzer informieren.

---

## Agent 3 — Shared-Infra-Migration (PHASE C)

**Ziel:** Hermes, Qdrant, Ollama, Caddy in neue Struktur überführen; Webshop-Volumes aus `data/` migrieren.

**Erlaubte Dateien/Pfade:**
- `/Datenspeicher/OpenDisruption/infra/**`.
- `/Datenspeicher/OpenDisruption-Data/shared/**`, `…/labs/webshop/**`.
- systemd-Units (alte deaktivieren, neue `od-shared.service`).
- Symlinks in v0.1 für Übergangszeit.

**Verbotene Aktionen:**
- Keine KIROBI-Privatdaten anfassen.
- Kein LUKI-Code (Phase F).
- Keine Compose-Lücken für Labs schließen (Phase H).

**Precheck:**
- [ ] PHASE B freigegeben.
- [ ] Snapshot + Restic-Restore aus Phase A bestanden.
- [ ] Qdrant-Snapshot frisch.
- [ ] Wartungsfenster (Qdrant + Webshop kurz down) bestätigt.

**Arbeitsschritte:**
1. Hermes-Source nach `infra/hermes-runtime/`; Runtime (`.venv`, caches, memories) nach `…shared/hermes/`. Compose-Mounts umstellen.
2. Qdrant snapshotten → in `…shared/qdrant/` migrieren; alte `services/qdrant/` (10 GB) nach `…archive/qdrant-legacy/`. Collections umbenennen: `kirobi_public`, `kirobi_family_shared`.
3. Ollama-Modelle nach `…shared/ollama/models/` (Symlink).
4. Caddy-Compose nach `infra/caddy/compose.shared.yml`; Volumes nach `…shared/caddy/`.
5. Webshop: Stack stop → `mysqldump` + `tar` → in `…labs/webshop/{mysql,wordpress}/` → Compose-Mounts um → Stack start → Smoke (Frontend, Login, Testbestellung lesbar).
6. systemd-Unit `od-shared.service` mit Compose-Wrapper.

**Tests:**
- Hermes-Skill-Smoketest grün aus neuem Pfad.
- Qdrant `/collections` listet erwartete Collections; Top-K-Smoketest grün.
- Ollama `ollama list` zeigt alle Modelle.
- Caddy `caddy validate` grün; alle Routen 401/200 wie erwartet.
- WP-Frontend grün, MySQL erreichbar.

**Output:**
- Bericht `…/reports/C-shared-infra-<datum>.md`.

**Rollback:**
- Qdrant-Snapshot zurück, Compose-Mounts zurück.
- Webshop-Dumps zurück.
- Hermes-Symlinks rückwärts.
- Snapshot R-001 als letzter Anker.

**Abbruchkriterien:**
- Qdrant-Migration verliert Collection-Daten.
- Webshop-Dump nicht restorebar.
- Hermes-Skill-Smoketest rot nach Migration.
→ STOPP + Rollback + Nutzer informieren.

---

## Agent 4 — KIROBI-Cleanup (PHASE D)

**Ziel:** KIROBI-Wahrheit in `products/kirobi/`; doppelte PWA auflösen; Privatdaten in Runtime-Tree.

**Erlaubte Dateien/Pfade:**
- `products/kirobi/**` (neu).
- `…OpenDisruption-Data/kirobi/{private,shared}/**`.
- systemd-Units der Telegram-Gateways.

**Verbotene Aktionen:**
- Kein LUKI-Move.
- Kein Labs-Move.
- Privatdaten nur `cp -a`, niemals `mv` ohne Backup.
- Schemaänderungen an Skills verboten.

**Precheck:**
- [ ] PHASE C freigegeben.
- [ ] Nutzer hat D5 (PWA-Wahrheit) + D3/E5 (Avatar-Domäne) entschieden.

**Arbeitsschritte:**
1. PWA-Diff (`diff -r kirobi-pwa/ Benutzer-Ordner/Sven/Projekte/kirobi-pwa/`); Wahrheit nach `products/kirobi/apps/pwa/`; Symlink vom Alt-Pfad 30 Tage.
2. Telegram-Gateway-Units anpassen (Pfade) → reload → Bots Ping-Test.
3. Skills migrieren → Hermes neu starten → 3 Skills Smoketest.
4. Privatdaten `rsync -aAX --numeric-ids`; Hash-Stichprobe; Originale erst nach Verifikation entfernen.
5. Avatar: KIROBI oder LAB platzieren (laut Entscheidung).

**Tests:**
- PWA lädt aus neuem Pfad (Tailscale-Browsertest).
- Beide Bots antworten.
- 3 Skills (random) grün.
- Privatdaten SHA-identisch.

**Output:**
- Bericht `…/reports/D-kirobi-cleanup-<datum>.md`.

**Rollback:**
- systemd-Unit `.bak` zurück, Symlinks rückwärts.
- Privatdaten-Originale aus Snapshot R-001.

**Abbruchkriterien:**
- PWA aus neuem Pfad startet nicht.
- Bot antwortet nicht nach Migration.
- Privatdaten-SHA mismatch.
→ STOPP + Rollback.

---

## Agent 5 — LUKI-Extraction (PHASE E)

**Ziel:** LUKI-Material extrahieren — Profile, Source-Docs, Canon — ohne MVP-Stack.

**Erlaubte Dateien/Pfade:**
- `products/luki/**` (neu).
- `…OpenDisruption-Data/luki/source-docs/**`.

**Verbotene Aktionen:**
- KIROBI nicht anfassen.
- Shared-Infra nicht anfassen.
- Keine Secret-Migration (war Phase A).
- Source-Docs nicht ins Repo committen.

**Precheck:**
- [ ] PHASE D freigegeben.
- [ ] D1 + D4 entschieden.

**Arbeitsschritte:**
1. `Benutzer-Ordner/LUKI/` → `products/luki/runtime/agent-profile/`.
2. `Nutzeisen Prozessanalyse/` → `…OpenDisruption-Data/luki/source-docs/`; Hash-Manifest in `products/luki/source-docs/manifest.json`.
3. `Geteilte-Wissensbasis/04-Business-und-Kunden/` → `products/luki/canon/business/`.
4. `Unternehmensstruktur/` split: LUKI-Anteile nach `products/luki/canon/orga/`; Labs-Anteile mit FREEZE-Marker.
5. InvenTree-Entscheidung (D1) umsetzen.

**Tests:**
- Manifest-Validierung grün (SHA256 jede Datei).
- `git status` zeigt nur erwartete Adds.
- KIROBI-Tree-Diff gegen Snapshot (Stichprobe) unverändert.

**Output:**
- Bericht `…/reports/E-luki-extraction-<datum>.md`.

**Rollback:**
- Kopierte Originale bis Phase F-Ende behalten.
- Snapshot R-001 als Anker.

**Abbruchkriterien:**
- Manifest-Validierung rot.
- KIROBI-Tree versehentlich verändert.
- Source-Docs landen im Repo.
→ STOPP + Rollback.

---

## Agent 6 — LUKI-Knowledge-MVP (PHASE F)

**Ziel:** Funktionsfähiger LUKI-Knowledge-Stack mit Quellenpflicht, Audit-Log, Eval-Bericht.

**Erlaubte Dateien/Pfade:**
- `products/luki/{knowledge,retrieval,audit,evals,compose.luki.yml,config}/**`.
- `infra/caddy/Caddyfile` (nur LUKI-Route).
- `…OpenDisruption-Data/luki/{ingest-staging,audit,evals}/**`.

**Verbotene Aktionen:**
- KIROBI-Collections nicht lesen (Whitelist).
- Kein Webshop-Eingriff.
- Keine Cloud-LLM-Aufrufe.
- Keine Klartext-Frage/Antwort im API-Log.

**Precheck:**
- [ ] PHASE E freigegeben.
- [ ] Qdrant + Ollama in Shared-Infra laufen.
- [ ] Embedding-Modell + LLM gepullt.
- [ ] `…secrets/luki.env` vorhanden.

**Arbeitsschritte:**
1. Ingest-CLI: extract → normalize → chunk(800/150) → embed → Qdrant upsert in `luki_knowledge_v1`.
2. Retrieval-Service FastAPI auf 127.0.0.1:8410; System-Prompt mit Quellenpflicht + Refusal-Default.
3. Audit-Log: JSONL append-only, Hashing User/Frage/Antwort; Mapping `_unhashed/` chmod 600.
4. 50-Fragen-Goldset in `products/luki/evals/v1/questions.json`; Run-Skript → `report.md`.
5. Caddy-Route `/luki` mit BasicAuth, nur Tailscale.
6. Whitelist-Test: Service liest nur `luki_*`-Collections.

**Tests:**
- Smoke-Frage → Antwort mit ≥1 Quelle.
- Frage außerhalb Material → „Ich weiß es nicht".
- Eval: Top1≥0.50, Top3≥0.75, Halluzination≤0.10.
- Audit-JSONL parseable (`jq`).
- Versuch `kirobi_*` → 403/fehlt.
- `curl -u user:wrong …/luki/ask` → 401.

**Output:**
- Eval-Report in Repo + Bericht `…/reports/F-luki-mvp-<datum>.md`.

**Rollback:**
- `qdrant collection delete luki_knowledge_v1` → sauberer Re-Ingest.
- Service stoppen, Caddy-Route entfernen.

**Abbruchkriterien:**
- Akzeptanzschwellen nicht erreicht + keine Mitigation dokumentiert.
- Cross-Collection-Leak im Whitelist-Test.
- Klartext-Frage im API-Log.
→ STOPP + Rollback + Nutzer informieren.

---

## Agent 7 — Documentation & Runbooks (PHASE G)

**Ziel:** Betriebsfähigkeit ohne stilles Wissen; jede operative Tätigkeit runbookbasiert.

**Erlaubte Dateien/Pfade:**
- `docs/runbooks/**`, `docs/security/**`, `docs/architecture-planning/**` (additiv).
- `products/luki/runbooks/**`.

**Verbotene Aktionen:**
- Keine Service-Code-Änderungen.
- Keine Compose-Änderungen (Ausnahme: Healthcheck-Lücken — dann eigene Mini-Phase).
- Keine neuen Features.

**Precheck:**
- [ ] PHASE F freigegeben.
- [ ] Monitoring-Stack mindestens Uptime-Kuma steht.

**Arbeitsschritte:**
1. Runbook-Set: `start-stop-{shared,kirobi,luki}.md`, `backup-restore.md`, `incident-{luki,webshop}.md`, `secret-rotation.md`, `updates.md`.
2. Demo-Skript `products/luki/runbooks/demo-nutzeisen.md`.
3. Architektur-Diagramme (Mermaid): Domain-Boundaries, Netz, Datenflüsse.
4. Security-Doku in `docs/security/` (Zonen, Cloud-Policy, Secret-Policy).
5. Sven läuft jedes Runbook einmal durch; Lücken korrigieren.

**Tests:**
- Trockenlauf jedes Runbooks durch Sven dokumentiert.
- `grep -L 'Last verified' docs/runbooks/*.md` → leer.

**Output:**
- Runbook-Set + Bericht `…/reports/G-docs-runbooks-<datum>.md`.

**Rollback:**
- Git-Revert.

**Abbruchkriterien:**
- Trockenlauf eines Runbooks scheitert nicht-trivial.
→ Runbook reparieren, dann erneut.

---

## Agent 8 — Verification & QA (querschnittlich + Pre-Pilot in PHASE H)

**Ziel:** Unabhängige Verifikation jeder Phase + Pilot-Vorbereitung für PHASE H.

**Erlaubte Dateien/Pfade:**
- `docs/architecture-planning/reports/**` (additiv).
- Read-only auf alles andere.

**Verbotene Aktionen:**
- Keine produktiven Änderungen (Agent ist read+test-only).
- Keine Secret-Berührung.
- Keine Service-Restarts.

**Precheck:**
- [ ] Phase, die verifiziert werden soll, ist abgeschlossen.
- [ ] Bericht der ausführenden Phase liegt vor.

**Arbeitsschritte (pro Phase):**
1. Phase-Akzeptanzkriterien aus `07_phased_implementation_plan.md` durchgehen, Beweis pro Kriterium sammeln.
2. Stichproben: 3 Smoketests, 3 Sec-Greps, 1 Restore-Probelauf (falls relevant).
3. Verifikations-Bericht `…/reports/Q-<phase>-<datum>.md` mit GO/NO-GO-Empfehlung.

**Arbeitsschritte (Pre-Pilot Phase H):**
1. Pilot-Hardware-Audit (Disk, RAM, Netz, Tailscale).
2. Backup-Restore-Test auf Pilot-Hardware.
3. Whitelist-Test auf Pilot-Qdrant.
4. Eval-Run mit Pilot-Goldset (≥10 Realfragen vom Kunden).
5. Datenschutz-Checkliste (Audit-Log-Hashing, kein FAMILY_*-Zugriff).

**Tests:**
- Akzeptanzliste vollständig grün.
- Restic-Restore auf Pilot-Hardware bestanden.
- Eval auf Realfragen ≥ MVP-Schwellen oder dokumentierte Mitigation.

**Output:**
- QA-Bericht mit GO/NO-GO + Liste der Befunde.

**Rollback:**
- Nicht zutreffend (read-only).

**Abbruchkriterien:**
- Akzeptanzkriterium rot ohne Mitigation.
- Sec-Grep liefert Klartext-Secret.
- Restore-Test scheitert.
→ NO-GO + Befundliste an Nutzer.

---

## Globale Regeln für alle Agenten

1. Niemals Klartext-Secrets ausgeben. Format: `SECRET_FOUND(type=…, file=…, line=…, value=MASKED)`.
2. Niemals Phase B starten ohne Phase A-FREIGABE — analog für jede Folge-Phase.
3. Bei jedem Zweifel: STOPP + Frage an Nutzer.
4. Jeder Agent schreibt einen Bericht in `docs/architecture-planning/reports/`.
5. Jeder Agent prüft seinen Precheck **bevor** er etwas verändert.
6. Kein Agent erweitert seinen Scope.
7. Snapshot R-001 ist immer der letzte Restorepunkt.
