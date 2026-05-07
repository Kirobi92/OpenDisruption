# Runbook — Phase 5: Telegram-Integration (GATED)

**Zone:** WORKSPACE
**Spezifikation:** `docs/agent/TELEGRAM-INTEGRATION.md`
**Milestones:** `keycodi/MILESTONES.md` § Phase 5

---

## Vorbedingungen (alle müssen erfüllt sein)

- Phase 4 ist `🟢 done`. KEYBRODI routet stabil.
- Sven hat **Option A** (Restricted Bridge) bestätigt — sonst wird diese Phase übersprungen.
- Sven hat Token-Storage-Verfahren bestätigt (env-Datei, Docker-Secret oder externer Manager).
- Mindestens ein erfolgreicher Test-Lauf des Zone-Filters in einer Sandbox liegt vor.

Wenn auch nur **eine** Bedingung offen ist: Phase 5 startet nicht. KeyCodi springt zu Phase 6.

## Schritte (nur bei Option A)

### 1. Zone-Filter-Choke-Point

Datei: `agents/_telegram/zone_filter.py`

API: `filter_outbound(message: dict) -> dict | None`
- `None` zurück, wenn `message.zone in {FAMILY_PRIVATE, SACRED, QUARANTINE}`.
- Log-Eintrag `TELEGRAM_ZONE_REJECT` mit Key + Zone (kein Payload!).
- Kein `--force`, kein Override, keine Env-Bypass.

Tests zuerst: `tests/unit/agents/_telegram/test_zone_filter.py` — alle 5 Zonen geprüft.

### 2. Bot-Handler

Sechs Container, jeder eigenes Service in `docker-compose.yml`, hinter Profile `telegram`:

- `tg-keybrodi`
- `tg-opencode`
- `tg-openclaw`
- `tg-hermes`
- `tg-obsidian`
- `tg-kidi`

Jeder Container:

- Läuft mit `KIROBI_EGRESS_ALLOWED=true` (auf separater Network-Policy).
- Nutzt seinen eigenen Token aus `${KIROBI_TELEGRAM_*_TOKEN}`.
- Verbindet sich zu Redis mit dediziertem ACL-User (siehe Schritt 3).

### 3. Redis-ACL

Konfigurations-Skript `infra/scripts/redis-telegram-acl.sh`:

- Legt User `kidi_telegram` an mit `+@read +get +scan ~ctx:PUBLIC:* ~ctx:WORKSPACE:*`.
- Verweigert `~ctx:FAMILY_PRIVATE:*`, `~ctx:SACRED:*`, `~ctx:QUARANTINE:*`.
- Wird im Compose-`redis`-Init-Script ausgeführt.

Test (manuell, dokumentiert): `redis-cli AUTH kidi_telegram <pw>; SCAN 0 MATCH ctx:FAMILY_PRIVATE:*` → leer / Permission denied.

### 4. Daily Team Meeting

Skript `infra/scripts/daily-team-meeting.sh`:

- Sammelt PUBLIC/WORKSPACE-Notizen aus dem Shared-Vault des Tages.
- Schickt Zusammenfassung über `tg-keybrodi` durch den Zone-Filter.
- **Nicht** automatisch via Cron installiert.
- Opt-in: `make telegram-cron-enable` legt Cron-Eintrag an, `make telegram-cron-disable` entfernt ihn.

### 5. Env

`.env.example` (nur Platzhalter):

```
KIROBI_TELEGRAM_ENABLED=false
KIROBI_TELEGRAM_KEYBRODI_TOKEN=CHANGEME
KIROBI_TELEGRAM_OPENCODE_TOKEN=CHANGEME
KIROBI_TELEGRAM_OPENCLAW_TOKEN=CHANGEME
KIROBI_TELEGRAM_HERMES_TOKEN=CHANGEME
KIROBI_TELEGRAM_OBSIDIAN_TOKEN=CHANGEME
KIROBI_TELEGRAM_KIDI_TOKEN=CHANGEME
KIROBI_TELEGRAM_CHANNEL_ID=CHANGEME
```

`.gitignore`: `.env` ist bereits ausgeschlossen — verifizieren.

### 6. Tests

- Pro Bot mindestens ein Smoke-Test (mocked).
- Refusal-Tests pro Zone.
- ACL-Tests (mocked / dokumentiert).
- Token-Leak-Test: `grep -R "TELEGRAM.*=.*[A-Za-z0-9]" -- :^.env.example :^docs/` → muss leer sein.

### 7. Sicherheits-Review

- CodeQL-Lauf grün.
- Sven manuell sign-off vor Merge.
- Eintrag als ADR in `keycodi/decisions/`.

## Definition of Done

`KIROBI_TELEGRAM_ENABLED=false` ist Default. Jeder Reject-Pfad ist getestet. Kein Token im Repo. Keine Cron-Installation by default.

## Mögliche Stolpersteine

- Bots versehentlich auf demselben Host wie obsidian-Agent (FAMILY_PRIVATE-Vault). → Compose-Constraint!
- Override-Schalter wird gewünscht → strikt ablehnen, ADR schreiben.
- Webhook statt Long-Polling → braucht öffentlichen Endpunkt → höheres Risiko, ADR notwendig.

## Übergang

Nach `🟢 done`: `runbooks/phase-6-installer.md`.
