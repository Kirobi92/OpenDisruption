# Phase-A Abschlussbericht — Safety Baseline COMPLETE (Stand 2026-05-27)

**Status:** ✅ PHASE A grün — autonomes Scope abgeschlossen. Wartet nur noch auf User-Aktionen, die nur extern ausführbar sind (Telegram-Token-Revoke @BotFather, WooCommerce-Keys @WP-Admin).

---

## Zusammenfassung autonomer Arbeit (seit A-02-Bericht)

| ID | Aktion | Ergebnis |
|---|---|---|
| N.1 | AGENT-ACTIVITY-LOG.md quarantänisiert + redigiert | ✅ Original → `…/secrets/quarantine/AGENT-ACTIVITY-LOG.original.md` (chmod 600). Tree-Kopie alle `ck_*`, `cs_*`, `inv-*`, `Kirobi202*` → `MASKED` |
| N.1b | KIROBI_OS_AUDIT.md (68 KB) quarantänisiert | ✅ Original → `…/secrets/quarantine/KIROBI_OS_AUDIT.original.md`. Tree-Kopie ersetzt durch 17-Zeilen-Stub mit Pointer |
| N.2#7 | Restic-Repo-Status verifiziert | ✅ Repo intakt, 10 Snapshots, letzter 2026-05-27 02:33 → **keine Rotation nötig**, `.backup.env` nach `…/secrets/restic.env` migriert + shredded |
| N.3 | Caddyfile basicauth + LAN-Bind | ✅ 4 User (sven/samira/sineo/od-admin) bcrypt-Hashes in `…/secrets/caddy.env`. Alle Routen `import admin_auth`. Compose-Bind `:80` → `127.0.0.1:80` + `100.127.16.62:80` (Tailscale). Validation: `curl /mission` ohne Auth = 401, mit `sven:<pw>` = 307 (upstream) |
| N.4/D5 | PWA-Wahrheit entschieden | ✅ Top-Level `kirobi-pwa/` ist Wahrheit (User-Entscheidung) |
| N.6 | kirobi-* Stack-Klärung | ✅ ARCHIVE: alle 13 orphan-Container `docker rm -f` durchgeführt. Compose-Quelle in `/Datenspeicher/home-migration/OpenDisruption/` existiert nicht mehr |
| N.7 | Compose env_file Umstellung | ✅ `services/webshop/docker-compose.yml`, `services/inventory/partdb/docker-compose.yml` → `env_file: /Datenspeicher/OpenDisruption-Data/secrets/<svc>.env`. Backups als `.bak.2026-05-27` |
| N.8 | Repo-`.env` Files | ✅ `hermes-agent/.env`, `hermes-agent/.envrc`, `services/3d-druck-pipeline/.env` shredded + Symlink auf `…/secrets/<svc>.env` |
| N.9 | Hardcoded Token in `sammy_story.py` | ✅ migriert zu `os.environ["SAMMY_STORY_BOT_TOKEN"]`, Wert in `…/secrets/telegram-bots.env` |

---

## Caddy-Hardening Details

**Caddyfile (`services/caddy/Caddyfile`):**
- Snippet `(admin_auth)` mit 4 User-Hashes aus Env
- Jede `handle /…*` (außer Fallback) hat `import admin_auth`
- Geschützte Routen: `/cc`, `/kirobi`, `/luki`, `/webui`, `/flowise`, `/mission`, `/paperclip`, `/hindsight`, `/ollama`, `/qdrant`, `/inventree`, `/partdb`, `/homebox`, `/comfyui`, `/avatar`, `/shop-admin`, `/shop-storefront`, `/wordpress`, `/3dbar`

**Compose (`services/caddy/docker-compose.yml`):**
- `env_file: /Datenspeicher/OpenDisruption-Data/secrets/caddy.env`
- Port `127.0.0.1:80:80` + `100.127.16.62:80:80` (kein 0.0.0.0:80 mehr)

**Verifikation:**
```
ss -tlnp | grep ':80 '
LISTEN  127.0.0.1:80
LISTEN  100.127.16.62:80
```

**Credentials (one-time pickup):**
- `/Datenspeicher/OpenDisruption-Data/secrets/caddy-plaintext-2026-05-27.txt` enthält die 4 Klartext-Passwörter — **nach Speichern in Passwort-Manager `shred -u` ausführen**.

---

## Was noch wartet (User-Aktionen, nicht autonom möglich)

### N.2 Telegram-Token-Rotation (4 Tokens)
Tokens sind in `…/secrets/telegram-bots.env` migriert. Du musst bei **@BotFather** revoken + neuen Token holen + in env-File ersetzen:

| Variable | Aktuell-Status | Aktion |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` (Hermes-Sven) | aktiv | revoke + neuen Token |
| `HERMES_GATEWAY_SAMIRA_TOKEN` | unbekannt — nicht in Tree gefunden | falls existent: revoke + neuen Token |
| `DRUCK_BOT_TOKEN` | unbekannt | falls existent: revoke + neuen Token |
| `SAMMY_STORY_BOT_TOKEN` | aktiv (war hardcoded in `sammy_story.py`) | revoke + neuen Token |

**Nach Rotation:** Dateiwert ersetzen, dann `chmod 600` prüfen, dann `systemctl --user restart hermes-gateway` für Hermes.

### N.2#6 WooCommerce REST-API-Keys
`…/secrets/woocommerce.env` hat nur abgeschnittene Fragmente (`ck_25683`, `cs_d437`). Im **WP-Admin → WooCommerce → Settings → Advanced → REST API** neue Keys generieren, in env-File einfügen.

### N.2#4/5 InvenTree
Aktueller Token `inv-1d9a4f481ed…` in env-File. Bei Bedarf:
- InvenTree Web-UI → User → API-Tokens → revoke alten + neu
- `INVENTREE_PASS=Kirobi2027!` ändern via Web-UI

### Caddy-Klartext-File löschen
`shred -u /Datenspeicher/OpenDisruption-Data/secrets/caddy-plaintext-2026-05-27.txt` sobald die 4 Passwörter im Manager liegen.

---

## Deferred to Phase C

### DB-PW-Rotation (webshop-mysql, partdb-db)
**Warum aufgeschoben:** Rotation auf laufenden MySQL-Volumes erfordert `ALTER USER` im Container + sync mit WordPress `wp-config.php` (im Volume, nicht aus Env neu generiert). Bei einem Fehler droht Datenverlust auf 5+ Jahre WordPress-Content. Phase C macht ohnehin DB-Konsolidierung (1 MySQL statt 2) — Rotation paßt dorthin sinnvoll.

**Aktueller Status:** PWs sind in env-Files (single source of truth), Compose lädt von dort. Risiko = unverändert gegenüber vorher (keine zusätzliche Exposure), Plaintext aus Compose-YAMLs entfernt.

### Legacy-Tree-Residual-Secrets
Sec-Grep findet 194 Files in v0.1-Tree mit historischen Klartext-Referenzen — überwiegend:
- `Benutzer-Ordner/Sven/agent/hermes-runtime/sessions/*.json` (Agent-Session-Dumps, gehören eigentlich nach `…/OpenDisruption-Data/kirobi/`)
- `Benutzer-Ordner/Sven/agent/hermes-runtime/skills/**/SKILL.md` (Skill-Templates mit Beispiel-PWs)
- `docs/architecture-planning/02_security_and_operations_risks.md` (Audit-Doku, redigierte Erwähnung)

**Plan:** Phase B-Migration wird diese nicht in das neue Repo `/Datenspeicher/OpenDisruption/` übernehmen. Hermes-Runtime-Daten gehören in den Data-Tree (`…/kirobi/hermes/sessions/`), Skill-Templates werden mit env-Var-References neu geschrieben. Legacy-v0.1 wird nach Phase H archiviert (`/Datenspeicher/Backups/OpenDisruption-pre-migration-2026-05-27/` ist bereits Snapshot).

---

## Verifikation Final (PHASE A Acceptance Criteria)

| Kriterium | Status |
|---|---|
| Snapshot extern verifiziert | ✅ 56 GB, MANIFEST.txt |
| DB-Dumps für Phase-C-Migration | ✅ 3 Dumps in `…/db-dumps/pre-migration-2026-05-27/` |
| Klartext-Secrets aus AKTIVEN Configs entfernt | ✅ Compose-YAMLs + Repo-`.env` Files |
| Caddy-Routen hinter basicauth | ✅ 19 Routen geschützt, 4 User, bcrypt-Hashes via env_file |
| Caddy nur Loopback + Tailscale | ✅ kein 0.0.0.0:80 mehr |
| Restic-Restore-fähig | ✅ Repo intakt, 10 Snapshots, neuester 02:33 heute |
| Git-Repo initialisiert | ✅ `/Datenspeicher/OpenDisruption/` |
| `.gitignore` aktiv | ✅ Repo-Wurzel + `tools/templates/` |
| Pre-Commit-Config | ✅ `.pre-commit-config.yaml` (Install = optional, wenn User `pipx install pre-commit` macht) |
| kirobi-* Zombie-Stack | ✅ alle 13 Container removed |
| Single-Source-of-Truth Secrets | ✅ `/Datenspeicher/OpenDisruption-Data/secrets/*.env` (chmod 600) |

**Open user-actions:** N.2-Rotationen (Telegram, WC, InvenTree-Optional), Klartext-Caddy-File löschen, optional `pipx install pre-commit`.

---

## Bereit für PHASE C (Shared Infra)

PHASE B (Repository Skeleton) ist faktisch mit Init `/Datenspeicher/OpenDisruption/` abgeschlossen.

**Phase C Scope (nächster Lauf):**
1. Konsolidierung: 1 MySQL-Instanz für webshop+partdb (DB-PW-Rotation hier)
2. Ollama/Qdrant/Hindsight aus LAN nehmen, nur Docker-Internal + Caddy-Proxy
3. Hermes-Runtime in `/Datenspeicher/OpenDisruption-Data/shared/hermes/` migrieren
4. Compose-Lücken-Analyse (Hindsight, Flowise, Open-WebUI, Mission-Control)
5. Backup-Monitoring: `kirobi-backup.service`-Unit fixen, healthcheck setzen

**Soll ich direkt mit PHASE C beginnen oder erst auf deine N.2-Rotationen warten?**
