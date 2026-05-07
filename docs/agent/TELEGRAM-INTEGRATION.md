# Telegram Integration — Zone Boundary & Opt-In Contract

**Version:** 0.2 (Phase 0 — decision recorded, design only)
**Zone:** WORKSPACE
**Status:** Option A chosen by Sven — **IMPLEMENTATION STILL DEFERRED TO PHASE 5**
**Owner:** kirobi-architect
**Last Updated:** 2026-05-06

---

## 1. The conflict this document resolves

The original problem statement proposes six Telegram bots (`@KEYBRODI_bot`, `@OpenCode_bot`, `@OpenClaw_bot`, `@Hermes_bot`, `@Obsidian_bot`, `@KIDI_bot`) with a daily "Teambesprechung" channel where agents share working state.

`/CLAUDE.md` §3 ("ABSOLUTE PROHIBITIONS") states explicitly:

> **NEVER send FAMILY_PRIVATE or SACRED content to:**
> - … any external service (webhooks, APIs, logging services)

Telegram **is** an external service. The agents listed above legitimately produce content in every zone, including FAMILY_PRIVATE (Obsidian vault, ContextDB entries derived from family experiences). A naive integration would violate `CLAUDE.md` on day one.

This document defines the only configuration in which Telegram may ship.

---

## 2. Decision required from the human (Sven)

Sven chose:

> **Option A — Restricted bridge.**

Before any Telegram code is written (Phase 5), this choice remains binding unless Sven opens a separate policy-change PR:

- **Option A — Restricted bridge (default proposal).** Telegram is enabled, but a hard zone gate at the boundary rejects any payload tagged above WORKSPACE. FAMILY_PRIVATE/SACRED/QUARANTINE never traverse the Telegram path. `CLAUDE.md` is **not** amended.
- **Option B — Drop Telegram.** Telegram is removed from the rollout entirely. A local chat UI (within the existing Caddy/PWA surface) is the user-facing channel. `CLAUDE.md` is **not** amended.
- **Option C — Amend `CLAUDE.md`.** Not recommended. Would require a separate threat-model review and is out of scope for this rollout.

This PR (Phase 0) records the choice and configures safe placeholders only. Runtime bot code, Redis ACL scripts and cron integration remain deferred to Phase 5.

---

## 3. Option A — Restricted bridge mechanics

### 3.1 Default state

- `KIROBI_TELEGRAM_ENABLED=false` in `.env.example`.
- Compose entries for Telegram bots live behind a `--profile telegram` flag.
- `infra/scripts/daily-team-meeting.sh` is **not** installed as a cron entry by `bootstrap.sh`. Adding it requires running an explicit opt-in script.

### 3.2 Single zone gate

All outbound Telegram traffic passes through one chokepoint (Phase 5 file location: `agents/_telegram/zone_filter.py`). The gate:

1. Inspects every outbound message's `zone` field.
2. **Rejects** anything where `zone in {FAMILY_PRIVATE, SACRED, QUARANTINE}`.
3. Logs every rejection to `kirobi-core/core-events.log` with reason `TELEGRAM_ZONE_REJECT` and the offending key (not the payload).
4. Has no override flag. There is no `--force` path.

### 3.3 ContextDB reader is restricted

The Telegram service connects to Redis with a dedicated ACL user that has read access only to:

```
ctx:PUBLIC:*
ctx:WORKSPACE:*
```

This is defense in depth: even if the application-level zone gate is bypassed by a bug, the Redis ACL prevents the bot from seeing FAMILY_PRIVATE/SACRED keys at all.

### 3.4 Token storage — chosen safest option: Docker Secrets

Bot tokens live in Docker Secrets (or an equivalent host-local secret manager in production). `.env.example` ships only `*_FILE` placeholders pointing to `/run/secrets/...` and never contains token values:

```
KIROBI_TELEGRAM_ENABLED=false
KIROBI_TELEGRAM_TOKEN_SOURCE=docker_secret
KIROBI_TELEGRAM_KEYBRODI_TOKEN_FILE=/run/secrets/telegram_keybrodi_token
KIROBI_TELEGRAM_OPENCODE_TOKEN_FILE=/run/secrets/telegram_opencode_token
KIROBI_TELEGRAM_OPENCLAW_TOKEN_FILE=/run/secrets/telegram_openclaw_token
KIROBI_TELEGRAM_HERMES_TOKEN_FILE=/run/secrets/telegram_hermes_token
KIROBI_TELEGRAM_OBSIDIAN_TOKEN_FILE=/run/secrets/telegram_obsidian_token
KIROBI_TELEGRAM_KIDI_TOKEN_FILE=/run/secrets/telegram_kidi_token
KIROBI_TELEGRAM_CHANNEL_ID_FILE=/run/secrets/telegram_channel_id
```

`install.sh` (Phase 6) **does not** prompt for tokens interactively. It validates that required secret files exist before allowing the `telegram` profile to start.

### 3.5 Network egress

Hosts running the Telegram service set `KIROBI_EGRESS_ALLOWED=true`. ContextDB writes for FAMILY_PRIVATE/SACRED refuse on such hosts (see `CONTEXT-WINDOW.md` §6.5). This forces a deployment topology where:

- The Telegram service runs in a separate container with limited network policy.
- FAMILY_PRIVATE/SACRED-writing agents run on a host or container marked `KIROBI_EGRESS_ALLOWED=false`.

### 3.6 Daily team meeting

If installed, the cron job:

- Runs at 09:00 in the host's local timezone (matching the existing Daily Notes convention).
- Calls `infra/scripts/daily-team-meeting.sh`, which only emits PUBLIC/WORKSPACE-tagged summaries.
- Is **opt-in**: `bootstrap.sh` does not install it. A separate `make telegram-cron-enable` target installs it; `make telegram-cron-disable` removes it.

### 3.7 Menus

Per-bot menus follow the structure in the original problem statement, with one change: any menu item that would surface zone-restricted content is hidden when `KIROBI_TELEGRAM_ENABLED=false` or when the user requesting the menu lacks the corresponding read permission in `services/auth/`.

---

## 4. What is forbidden under all options

- Sending raw ContextDB payloads to Telegram without going through the zone gate.
- Storing tokens in any tracked file.
- Logging payloads (only keys, zones, and reason codes).
- Running the Telegram service on the same container/host as a FAMILY_PRIVATE/SACRED-writing agent without network egress restriction.
- Auto-enabling the daily cron during install.

---

## 5. Tests required before Phase 5 ships

- Unit: every zone in `{FAMILY_PRIVATE, SACRED, QUARANTINE}` is rejected by `zone_filter`.
- Unit: payloads with mismatched key/value zones are rejected.
- Unit: ACL-restricted Redis reader cannot read `ctx:FAMILY_PRIVATE:*` or `ctx:SACRED:*` (mocked).
- Integration (manual checklist): no token in `.env.example`; `KIROBI_TELEGRAM_ENABLED=false` by default; cron not installed by `bootstrap.sh`.

---

## 6. Changelog

```
0.1  2026-05-06  Initial draft. No option chosen yet.
0.2  2026-05-07  Sven chose Option A. Safest token storage set to Docker Secrets / *_FILE placeholders.
```

---

## 7. Cross-references

- `CLAUDE.md` §3 — the prohibition this document reconciles
- `docs/agent/CONTEXT-WINDOW.md` — Redis ACL and egress guard
- `docs/agent/MULTI-AGENT-ARCHITECTURE.md` — overall topology
- `metadata/ZONE-POLICY-MATRIX.md` — authoritative zone permissions
