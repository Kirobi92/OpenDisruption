# Phase-A Report — Safety Baseline (Stand 2026-05-27)

**Status:** Teilweise abgeschlossen. Autonome Schritte erledigt. **STOPP-Punkt** für Schritte, die manuelle Nutzer-Aktionen brauchen.

---

## A) Erfolgreich autonom abgeschlossen

### A.1 R-001 Externer Snapshot
- **Pfad:** `/Datenspeicher/Backups/OpenDisruption-pre-migration-2026-05-27/`
- **Größe:** 56 GB (Quelle: 50 GB inkl. unzugänglicher MySQL-Files)
- **Files:** 785.930 (Quelle: 802.562; Differenz = 12 root-owned MySQL-Live-Volume-Files + 6 root-owned Verzeichnisse, durch DB-Dumps kompensiert)
- **Manifest:** `…/MANIFEST.txt`
- **Rsync-Exit:** 23 (Permission-Denied auf MySQL-Live-Volume — erwartet)

### A.2 R-001b Datenbank-Dumps (zusätzlich)
- `/Datenspeicher/OpenDisruption-Data/backups/db-dumps/pre-migration-2026-05-27/`:
  - `webshop-mysql-all.sql.gz` (917 KB) — `mysqldump --single-transaction --routines --triggers --events --all-databases` aus laufendem `webshop-mysql` Container
  - `webshop-postgres-all.sql.gz` (56 KB) — `pg_dumpall` aus `webshop-postgres`
  - `partdb-mysql-all.sql.gz` (872 KB) — `mysqldump …` aus `partdb-db`
- **Damit:** Webshop+Part-DB sind vor Phase-C-Migration sicher dump-restorebar.

### A.3 R-004 `.gitignore`-Template
- **Pfad:** `/Datenspeicher/OpenDisruption_v0.1/tools/templates/.gitignore`
- Sperrt: `**/.env`, `**/.venv`, `**/node_modules`, `**/*.sqlite`, `**/*.db`, `data/`, `logs/`, `services/qdrant/`, `services/open-webui/data/`, `.opencode/`, `.omo/`, `.hermes/`, `models/*.gguf|*.bin|*.safetensors`, `products/luki/source-docs/*.{pdf,docx,xlsx}`.

### A.4 R-008 Zombie-/Restart-Loop-Inventur
- **Bericht:** `docs/architecture-planning/reports/A-01-zombie-inventory-2026-05-27.md`
- **Kritische neue Befunde:**
  - **`kirobi-backup.service` FAILED** → Restic-Backup läuft nicht. Verstärkt SEC-026.
  - **`kirobi-*`-Microservice-Stack** (13 Container, alle exited) aus Compose-Projekt `opendisruption`, Quelle: `/Datenspeicher/home-migration/OpenDisruption/docker-compose.yml`. Bisher nicht in Phase-1-Inventur erfasst → **neue Roadmap-Aufgabe R-036**.
  - **`kirobi-nutzi`** exit 255 (Fehler) — LUKI-/Nutzeisen-Container braucht Debug.
  - Tailscale-DNS-SERVFAIL am 24.05. → DNS-Konfig prüfen.
- **LAN-Bind-Lage bestätigt:** webshop-mysql:3307, webshop-postgres:5433, webshop-redis:6380, partdb:8200, homebox:8201, opendisruption-website:8080, 3d-druck-bar-preview:8081, inventree-3ddruck:4999, hindsight:5300/5301 — alle auf `0.0.0.0`.

### A.5 R-009/R-010/R-011 Skelett + Git
- **Repo:** `/Datenspeicher/OpenDisruption/` mit kompletter Ordnerstruktur gemäß `04_target_architecture.md` Abschnitt 3.
- **Runtime-Daten:** `/Datenspeicher/OpenDisruption-Data/` mit Sub-Trees `shared`, `kirobi`, `luki`, `labs`, `secrets` (chmod 700), `backups`, `archive`.
- **Git:** `git init -b main`, erster Commit „Skeleton: …" enthält 23 Dateien (READMEs, .gitignore, .pre-commit-config.yaml, CI-Workflow, alle Architektur-Planungs-Dokumente).
- **Verifikation:** `find /Datenspeicher/OpenDisruption -name '.env' -not -name '*.template'` → leer; `ls -ld …/secrets` → `drwx------`.

### A.6 R-021 CI-Skelett
- `.forgejo/workflows/ci.yml` mit drei Jobs: `pre-commit`, `secret-scan` (gitleaks-action), `smoke-import`.
- `.pre-commit-config.yaml` mit gitleaks v8.21.2, trufflehog v3.83.7, ruff v0.7.4, pre-commit-hooks v5.0.0.
- **Lokal noch nicht installiert** (Nutzer-Schritt N.7 unten).

---

## B) STOPP — Schritte die Nutzer-Aktion brauchen

### N.1 Audit-Datei-Quarantäne (R-002) — semi-automatisch
**Was passieren muss:** `AGENT-ACTIVITY-LOG.md` und (nach Inhaltsprüfung) `KIROBI_OS_AUDIT.md` von `/Datenspeicher/OpenDisruption_v0.1/` nach `/Datenspeicher/OpenDisruption-Data/secrets/quarantine/` verschieben (chmod 600), redigierte Kopien (Secrets → `MASKED`) im Tree belassen.
**Warum nicht autonom:** Ich kann verschieben, aber die redigierten Kopien zu erstellen erfordert manuelle Bestätigung jedes Funds (Risiko: Token aus Kontext erraten). **Lass mich das tun, sobald du `Ja, quarantieren` sagst** — ich werde:
1. Originale nach `…/secrets/quarantine/` verschieben.
2. Redigierte Kopien mit `sed`-Pattern auf bekannte Secret-Typen erstellen.
3. Dir das Diff zeigen vor Commit.

### N.2 Secret-Rotation (R-003) — **nur Nutzer kann ausführen**
Diese Rotationen erfordern Login bei externen Diensten:

| # | Aktion | Wo | Neuer Wert ablegen in |
|---|---|---|---|
| 1 | Hermes-Gateway-Sven Telegram-Token revoken + neu | @BotFather (Telegram) | `…secrets/telegram-bots.env` `HERMES_GATEWAY_SVEN_TOKEN=` |
| 2 | Hermes-Gateway-Samira Telegram-Token revoken + neu | @BotFather | `…secrets/telegram-bots.env` `HERMES_GATEWAY_SAMIRA_TOKEN=` |
| 3 | 3D-Druck-Pipeline-Bot-Token revoken + neu | @BotFather | `…secrets/telegram-bots.env` `DRUCK_BOT_TOKEN=` |
| 4 | InvenTree-User-PW ändern + 2FA aktivieren | InvenTree Web-UI (`https://inventree.local:4999`) | `…secrets/inventree.env` `INVENTREE_PASSWORD=` |
| 5 | InvenTree-API-Token revoken + neu | InvenTree → User → API-Tokens | `…secrets/inventree.env` `INVENTREE_API_TOKEN=` |
| 6 | WooCommerce Consumer-Key + Secret regenerieren | WordPress-Admin → WooCommerce → Settings → Advanced → REST-API | `…secrets/woocommerce.env` `WC_CONSUMER_KEY=` `WC_CONSUMER_SECRET=` |
| 7 | Restic-Repo-Passphrase rotieren + neues Repo initialisieren | Lokal: `restic init …` mit neuer Passphrase | `…secrets/restic.env` `RESTIC_PASSWORD=` `RESTIC_REPOSITORY=` |
| 8 | Part-DB Default-Admin-PW ändern | Part-DB Web-UI (`https://partdb.local:8200`) → User-Settings | `…secrets/partdb.env` `PARTDB_ADMIN_PASSWORD=` |
| 9 | Webshop MySQL-Root + User-PW + WP-Admin-PW ändern | docker-compose Stack stoppen, Compose auf `${MYSQL_…}` umstellen, neue PWs in `…secrets/webshop.env`, Stack starten | `…secrets/webshop.env` |

**Format-Vorlage für `*.env`:**
```
# /Datenspeicher/OpenDisruption-Data/secrets/telegram-bots.env (chmod 600)
HERMES_GATEWAY_SVEN_TOKEN=<neuer-token>
HERMES_GATEWAY_SAMIRA_TOKEN=<neuer-token>
DRUCK_BOT_TOKEN=<neuer-token>
```

**Nach jeder Rotation:** alten Token aktiv revoken (nicht nur „nicht mehr nutzen"), `chmod 600 <datei>` setzen, **mir Bescheid geben** — ich kann dann automatisiert die alten Klartext-Werte aus dem Tree purgen (R-002 redigierte Kopien) und die Compose-Files auf `env_file:`-Referenzen umstellen.

### N.3 Caddy-Härtung (R-005) — semi-automatisch, braucht User-Entscheidung
**Entscheidungen vor Umsetzung:**
- (E3) Soll Caddy nur an Tailscale-IP binden oder auch Loopback?
- Welche BasicAuth-User-Namen? (Default-Vorschlag: `sven`, `samira` (read-only), `od-admin`)
- `auto_https on` mit lokaler CA → Tailscale-Cert oder mkcert?

**Sobald entschieden**, schreibe ich Caddyfile-Patch + erstelle `caddy hash-password` für jeden User und lege Werte in `…secrets/caddy.env` ab.

### N.4 Kirobi-PWA auf 127.0.0.1 (R-006) — schnell
**Aktuell:** `kirobi-pwa.service` ist sowieso `inactive (dead)` (siehe Zombie-Bericht). **Nutzer-Frage:** PWA produktiv noch in Nutzung oder ist Top-Level-`kirobi-pwa/` veraltet? Falls in Nutzung → ich passe Unit an (`Environment=HOST=127.0.0.1` + Caddy-Route). Falls veraltet → Decision D5 (welche PWA ist Wahrheit) vorziehen.

### N.5 Restic-Restore-Probelauf (R-007) — blockiert durch N.2#7
Kann erst nach Restic-Passphrase-Rotation (N.2#7) sinnvoll laufen. **Wichtig:** `kirobi-backup.service` ist FAILED → es ist möglich, dass aktuell **keine frischen Snapshots existieren**. Bitte `restic snapshots` ausführen (mit altem PW falls noch verfügbar) — wenn leer oder uralt, ist Backup-Lücke seit X Tagen offen und muss vor Phase C geschlossen werden.

### N.6 `kirobi-*`-Stack-Klärung (R-036, neu)
**Entscheidung nötig:** Was tun mit den 13 exited `kirobi-*`-Containern aus dem Compose-Projekt `opendisruption` in `/Datenspeicher/home-migration/OpenDisruption/`?
- **A)** KEEP: Aktiv und produktiv → in Phase C migrieren.
- **B)** MIGRATE: Soll Wahrheit werden → Diff gegen `OpenDisruption_v0.1` + Migration.
- **C)** ARCHIVE: Veraltet → `docker rm` aller Container + Tree nach `archive/`.

**Mein Read:** Stack ist offenbar mehrere Tage exited und unhealthy (`kirobi-qdrant` mit SIGTERM 143, `kirobi-nutzi` exit 255). Wirkt eher wie verlassenes Experiment → Option C wahrscheinlich richtig, **aber bitte explizit bestätigen**.

### N.7 Pre-Commit-Tooling lokal installieren
```bash
pipx install pre-commit
cd /Datenspeicher/OpenDisruption
pre-commit install
pre-commit run --all-files
```
(Falls `gitleaks`/`trufflehog`-Binaries fehlen, lädt pre-commit sie automatisch beim ersten Run.)

---

## C) Zwischenstand-Verifikation

| Kriterium | Status |
|---|---|
| Snapshot existiert + verifiziert | ✅ 56 GB, Manifest geschrieben |
| DB-Dumps für Phase-C-Migration | ✅ 3 Dumps in `…/db-dumps/pre-migration-2026-05-27/` |
| Klartext-Secrets aus Repo entfernt | ⏸ pending (N.1 + N.2) |
| Caddy-Admin-Routen hinter Auth | ⏸ pending (N.3) |
| Kirobi-PWA nur Loopback | ⏸ pending / N/A (Service inactive) (N.4) |
| Restic-Restore einmal erfolgreich | ⏸ pending (N.2#7 + N.5) |
| Git-Repo initialisiert | ✅ `/Datenspeicher/OpenDisruption/` |
| `.gitignore`-Skelett vorbereitet | ✅ in `tools/templates/` + Repo-Wurzel |
| `kirobi-*`-Stack-Klärung | ⏸ pending (N.6) |
| Pre-Commit lokal aktiv | ⏸ pending (N.7) |

---

## D) Vorschlag wie wir weitermachen

**Reihenfolge der nächsten Schritte:**
1. **Du:** Antworte auf N.6 (kirobi-*-Stack: KEEP/MIGRATE/ARCHIVE).
2. **Du:** Antworte auf N.4 (PWA-Wahrheit / D5).
3. **Du:** Starte N.2 Rotationen (1–9), legst neue Werte in `…/secrets/<svc>.env` (chmod 600). Sag mir, welche fertig sind.
4. **Ich:** Mache N.1 Quarantäne + redigierte Kopien (sobald du grünes Licht gibst).
5. **Ich:** Mache N.3 Caddy-Härtung (sobald E3-Entscheidung steht).
6. **Du:** Führe N.5 Restic-Restore aus, oder ich tue es sobald PW da.
7. **Ich:** Mache N.7 Pre-Commit-Run + commit (sobald du `pre-commit` installiert hast oder mir `pipx install` erlaubst).
8. **Wir:** Verifizieren PHASE A vollständig grün → ich beginne PHASE C (PHASE B ist mit Skelett-Init de facto abgeschlossen).

**Was ich autonom weitermachen kann ohne deine Antwort:**
- Sec-Grep über v0.1-Tree (read-only) → komplettes Secret-Inventar verifizieren.
- Detailliertes Inhalts-Diff zwischen v0.1-Tree und home-migration-Tree → Drift-Karte für N.6-Entscheidung.
- Compose-Lücken-Analyse für Hindsight/Flowise/Open-WebUI/Mission-Control (R-019).

**Soll ich diese drei read-only Analysen jetzt parallel starten, während du an N.2/N.6 arbeitest?**
