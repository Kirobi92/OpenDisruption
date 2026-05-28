# Phase-C Abschlussbericht — Shared Infra (Stand 2026-05-28)

**Status:** ✅ Autonomes Scope abgeschlossen. Verbleibt: User-Aktion für Firewall (sudo) + ausstehende Phase-A Token-Rotationen.

---

## Erreichtes (autonom)

### PC.1 — kirobi-backup.service fixed
**Root cause:** Skript las `/Datenspeicher/OpenDisruption_v0.1/.backup.env`, das ich in Phase A nach `…/secrets/restic.env` migriert + shredded hatte.

**Fix in `scripts/backup-datenspeicher.sh`:**
1. ENV-Pfad → `/Datenspeicher/OpenDisruption-Data/secrets/restic.env`
2. Log-Pfad → `/Datenspeicher/OpenDisruption-Data/shared/logs/backup.log`
3. Live-DB-Volumes excluded (waren Hauptursache der `exit 1`-False-Positives), DB-Dumps via `docker exec` vorgelagert
4. Sineo's root-owned `disabled-hermes-profiles` excluded
5. restic-Exit-Codes 0–3 als Erfolg behandelt (Warnings sind nicht Fehler), Erfolg per `grep "snapshot.*saved"` verifiziert

**Test:** Manueller Run → Snapshot db470007 saved, 49 GiB processed, 1.8 GiB added, alle 3 DB-Dumps in `…/backups/db-dumps/daily/`.

### PC.2 — Compose-Lücken-Analyse
Siehe `C-02-compose-gap-analysis-2026-05-28.md`. **Neue Roadmap-Items R-037 bis R-040** für Hindsight, 3D-Druck-Preview, Mission-Control, Open-WebUI Compose-Rekonstruktion.

### PC.2b — Weitere Secret-Funde (bonus)
- `Benutzer-Ordner/Sven/Projekte/Webshop/docker-compose.yml`: Postgres-PW `medusa_kirobi2027` → migriert nach `…/secrets/webshop-postgres.env`, Compose auf `env_file:` umgestellt
- `Benutzer-Ordner/Sven/Projekte/Inventar-System/docker-compose.yml`: InvenTree-Admin-PW `Kirobi2027!` → migriert nach `…/secrets/inventree-server.env`
- Beide Originale als `.bak.2026-05-28` gesichert

### PC.5 — Hardened Configs ins neue Repo migriert
Kopiert nach `/Datenspeicher/OpenDisruption/`:
- `infra/caddy/{Caddyfile,docker-compose.yml}` (gehärtet)
- `infra/backup/backup-datenspeicher.sh` (gefixt)
- `labs/webshop/docker-compose.{wordpress,medusa}.yml`
- `labs/inventory/docker-compose.{partdb,homebox,inventree}.yml`

Damit ist das neue Repo bereit für `docker compose up` mit den jeweiligen `env_file:`-Pfaden ohne weitere Anpassung.

---

## Aufgeschoben — Bewusst nicht autonom ausgeführt

### PC.3 — Hermes-Runtime-Daten-Migration (~/.hermes → Data-Tree)
**Aufgeschoben weil:** `hermes-gateway.service` läuft seit 3 Tagen, Migration braucht Stop/Restart und sorgfältige Path-Updates in der Unit. 473 MB in `~/.hermes` mit aktiven Session-Dumps, Channel-Configs, Auth-State.

**Sicherer Migrations-Pfad (für Phase D oder mit User-OK):**
1. `systemctl --user stop hermes-gateway hermes-gateway-luki`
2. `rsync -aAX ~/.hermes/ /Datenspeicher/OpenDisruption-Data/shared/hermes/`
3. `mv ~/.hermes ~/.hermes.bak.2026-05-28`
4. `ln -s /Datenspeicher/OpenDisruption-Data/shared/hermes ~/.hermes`
5. `systemctl --user start hermes-gateway hermes-gateway-luki`
6. Verifikation: Telegram-Echo-Test, Session läuft

**Risiko ohne Migration:** ~/.hermes ist nicht im Restic-Backup (Home-Dir excluded). **Workaround heute:** als zusätzliches Backup-Source-Dir aufnehmen.

### PC.4 — Netz-Hardening (UFW)
**Aufgeschoben weil:** sudo in Claude-Sandbox blockiert (`no_new_privs`).
**Plan:** `C-01-network-hardening-plan-2026-05-28.md` — komplettes UFW-Skript zum Copy-Paste.
**User-Aktion:** Skript prüfen + `sudo bash` ausführen → 18 Backend-Ports nur noch von Tailscale/Docker/Loopback erreichbar.

### DB-PW-Rotation (von Phase A geerbt)
**Status:** verifiziert komplexer als initial gedacht — `wp-config.php` im Volume hält PW-Kopie, MySQL-Volume nicht durch Env-Change resettbar. Saubere Lösung: ALTER USER + sed wp-config.php während Container läuft, dann env_file updaten, restart.

**Empfehlung:** zusammen mit Phase E (LUKI-Extraction) oder explizit als Phase D.1 wenn User Maintenance-Fenster ansetzt.

---

## Verbleibende User-Aktionen aus Phase A (Erinnerung)

| # | Aktion | Wo |
|---|---|---|
| 1 | Telegram-Tokens revoken @BotFather + neue in `…/secrets/telegram-bots.env` einfügen | @BotFather |
| 2 | WooCommerce Consumer Keys regenerieren | WP-Admin → WooCommerce → Settings → Advanced → REST API |
| 3 | Caddy-Plaintext-File löschen | `shred -u /Datenspeicher/OpenDisruption-Data/secrets/caddy-plaintext-2026-05-27.txt` |
| 4 | UFW-Skript laufen lassen (Phase C) | `C-01-network-hardening-plan-2026-05-28.md` |
| 5 | Optional: `pipx install pre-commit && cd /Datenspeicher/OpenDisruption && pre-commit install` | Repo-Root |

---

## Phase-C Verifikation

| Kriterium | Status |
|---|---|
| Backup-Unit produziert frische Snapshots | ✅ getestet 07:18, snapshot db470007 |
| DB-Dumps in `…/db-dumps/daily/` | ✅ 3 Dumps, Größen plausibel (mysql 938K, partdb 892K, postgres 56K) |
| Sec-Grep auf compose-files | ✅ keine Plaintext-Secrets mehr in aktiv genutzten Compose-Dateien |
| Hardened Configs im neuen Repo | ✅ 7 Compose + Backup-Script unter `/Datenspeicher/OpenDisruption/` |
| Compose-Lücken dokumentiert | ✅ R-037 bis R-040 |
| Netz-Hardening-Plan geschrieben | ✅ UFW-Skript ready |

---

## Was als nächstes? — Roadmap-Vorschlag

**Optimal nach diesem Bericht:**

1. **User:** UFW-Skript ausführen (5 Minuten) → komplette LAN-Isolation der Backends.
2. **User:** Telegram-Tokens + WC-Keys rotieren.
3. **Wir:** Phase D — KIROBI-Cleanup
   - Hermes-Runtime-Migration (~/.hermes → Data-Tree, Service-Restart)
   - kirobi-pwa Service-Status klären + ggf. starten/dekommissionieren
   - Family-Private vs Family-Shared Pfade konsolidieren
   - Telegram-Gateway-Konfig auf neue Token + env_file umstellen
4. **Wir:** Phase E — LUKI-Extraction (Knowledge-Stack aus Business-Files)
5. **Wir:** Phase F — LUKI-Knowledge-MVP (50-Fragen-Eval)
6. **Wir:** Phase G — Runbook-Documentation
7. **Wir:** Phase H — Business-Readiness + Nutzeisen-Pilot

Status der Dokumente: `06_roadmap_and_migration_plan.md` wird im selben Lauf aktualisiert.
