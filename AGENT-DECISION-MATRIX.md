# Agent Decision Matrix

> Authoritative rules an autonomous agent uses to decide whether to **act**,
> **act + log**, **ask**, or **refuse** for any operation against
> OpenDisruption. Pair this with `AGENT-SYSTEM-PROMPT.md`.

---

## 1. The 4-axis classification

For every contemplated action, classify it on these four axes:

| Axis | Values |
|------|--------|
| **Zone** | `PUBLIC` · `WORKSPACE` · `FAMILY_PRIVATE` · `QUARANTINE` · `SACRED` |
| **Reversibility** | `reversible` (git/compose can undo) · `recoverable` (needs backup) · `irreversible` |
| **External I/O** | `none` · `outbound-public` · `outbound-private-data` |
| **Privilege** | `unprivileged` · `sudo` · `network-admin` · `data-destructive` |

The **highest** value on each axis wins. When unsure, escalate one step.

---

## 2. The matrix

| # | Zone | Reversibility | External I/O | Privilege | Verdict | Notes |
|---|------|---------------|--------------|-----------|---------|-------|
| 1 | PUBLIC | reversible | none | unprivileged | **ACT** | silent |
| 2 | PUBLIC | reversible | outbound-public | unprivileged | **ACT + LOG** | log url + payload size |
| 3 | PUBLIC | recoverable | any | unprivileged | **ACT + LOG** | ensure backup ref in log |
| 4 | PUBLIC | irreversible | any | any | **ASK** | always |
| 5 | WORKSPACE | reversible | none | unprivileged | **ACT** | silent |
| 6 | WORKSPACE | reversible | outbound-public | unprivileged | **ACT + LOG** | – |
| 7 | WORKSPACE | reversible | outbound-private-data | unprivileged | **ASK** | might leak code/secrets |
| 8 | WORKSPACE | recoverable | any | any | **ASK** | – |
| 9 | WORKSPACE | irreversible | any | any | **ASK** | – |
| 10 | FAMILY_PRIVATE | reversible | none | unprivileged | **ACT + LOG** | local-only |
| 11 | FAMILY_PRIVATE | recoverable | none | unprivileged | **ASK** | – |
| 12 | FAMILY_PRIVATE | any | outbound-public | any | **REFUSE** | local models only |
| 13 | FAMILY_PRIVATE | any | outbound-private-data | any | **REFUSE** | – |
| 14 | FAMILY_PRIVATE | irreversible | any | any | **ASK + double-confirm** | – |
| 15 | QUARANTINE | any | any | any | **REFUSE** | move to extracts/ first after human review |
| 16 | SACRED | any | any | any | **REFUSE** unless explicit Sven OK in this session | even reads |
| 17 | any | any | any | sudo | **ASK** | always |
| 18 | any | any | any | data-destructive | **ASK + dry-run-first** | always |

`SACRED` reads with explicit approval are still allowed only via the
`kirobi-core` agent and must be logged.

---

## 3. Inputs to the classification

### 3.1 Determining the zone

1. Inspect every input path against the table in `AGENT-SYSTEM-PROMPT.md` §1
   and against `metadata/ZONE-POLICY-MATRIX.md`.
2. Inspect every output path the same way.
3. Inspect file frontmatter — explicit `zone: SACRED` overrides folder.
4. Inspect Qdrant collection name — `kirobi_family*` ⇒ `FAMILY_PRIVATE`.
5. **The highest zone wins.** Defaults: unknown file = `SACRED`; web fetch =
   `PUBLIC`; user message = `WORKSPACE`.

### 3.2 Determining reversibility

| Reversible | Recoverable | Irreversible |
|------------|-------------|--------------|
| `git revert`, `git restore` | restore from `archive/snapshots/` or container volume | overwrites with no backup, `rm -rf`, `DROP TABLE`, `docker compose down -v`, third-party API write |

### 3.3 Determining external I/O

- **none**: stdin/stdout, local files, local Docker network.
- **outbound-public**: GET to a public registry/docs site, no payload.
- **outbound-private-data**: any POST/PUT to a non-localhost host, OR any
  request whose body or headers contain non-PUBLIC data.

`localhost`, `127.0.0.1`, `::1`, the `kirobi-net` Docker bridge, and
`*.kirobi.local` count as **none** (they are local).

### 3.4 Determining privilege

- **sudo / root**: `sudo`, `doas`, `su`, writing to `/etc`, `/usr`, `/var` or
  any system path; binding to ports < 1024 outside Caddy.
- **network-admin**: changing firewall, opening LAN ports, modifying
  `KIROBI_BIND_HOST`, editing Caddyfile to add public hostnames.
- **data-destructive**: `rm -rf`, `truncate`, `DROP`, `DELETE FROM`, schema
  migrations without down-migration, `docker compose down -v`, force-pushing.

---

## 4. Verdict semantics

### ACT
Execute immediately. No prompt. Still write a one-line entry in
`kirobi-core/core-events.log` if the action mutates state (file write,
container start, DB write).

### ACT + LOG
Execute immediately, but emit a structured log entry:

```
[2026-05-06T18:35:00Z] [agent-id] INFO action=write path=extracts/workspace/x.md
  zone=WORKSPACE bytes=2048 reason="user requested summary"
```

### ASK
Pause, present an **Action Approval Request**:

```
ACTION APPROVAL REQUEST
─────────────────────────
Intent       : <one sentence>
Files / cmd  : <exact paths or command line>
Zone         : <highest>
Reversibility: <reversible | recoverable | irreversible>
External I/O : <none | outbound-* | …>
Privilege    : <unprivileged | sudo | …>
Risk         : <low | medium | high>
Undo         : <how to undo, or "irreversible">

Approve? [y/N]
```

Only proceed on an explicit `y` from the human. Default = NO.

### REFUSE
Politely decline. Use the templates in `AGENT-SYSTEM-PROMPT.md` §7. Do not
work around the refusal (e.g. by chunking data and sending it piecemeal).

---

## 5. Ambiguity & escalation

When in doubt:

1. **Increase the zone one level** (PUBLIC→WORKSPACE→FAMILY→SACRED).
2. **Decrease the privilege one level** (act → ask).
3. **Prefer dry-run.** Every script must support `--dry-run`.
4. **Prefer additive over mutative.** New file > modify > delete.
5. **Prefer reversible.** Move to `archive/` instead of `rm -rf`.

If still unclear, **ASK**. Asking is always cheaper than recovering.

---

## 6. Worked examples

| Scenario | Zone | Rev. | Ext. | Priv. | Verdict |
|----------|------|------|------|-------|---------|
| Add a markdown note to `extracts/workspace/notes/` | WORKSPACE | reversible | none | un | ACT |
| `npm install` in `apps/web` | WORKSPACE | reversible | outbound-public | un | ACT + LOG |
| Send a file from `extracts/family-private/` to OpenAI for summarisation | FAMILY | recoverable | outbound-private-data | un | **REFUSE** (use local Ollama) |
| `docker compose down -v` | WORKSPACE | irreversible | none | data-destructive | **ASK** |
| Edit `Caddyfile` to add `kids.example.com` (public hostname) | WORKSPACE | reversible | none | network-admin | **ASK** |
| Read a file under `sacred/` | SACRED | reversible | none | un | **REFUSE** unless Sven approved this session |
| Run `pytest tests/unit -q` | WORKSPACE | reversible | none | un | ACT |
| `git push` | WORKSPACE | reversible | outbound-public | un | ACT + LOG (but never push secrets) |
| Move file from `quarantine/` to `extracts/workspace/` | QUARANTINE→WORKSPACE | reversible | none | un | **ASK** (zone change requires human review) |
| Create a fresh `.env` with random secrets | WORKSPACE | reversible | none | un | ACT (idempotent — only if missing) |

---

## 7. Logging contract

Every ACT + LOG, ASK and REFUSE must emit one line to
`kirobi-core/core-events.log`:

```
[ISO-8601] [agent-id] LEVEL key1=value1 key2="value with space" ...
```

Required keys: `action`, `zone`, `verdict`. Optional but encouraged:
`path`, `bytes`, `cmd`, `reason`, `risk`, `approver`.

Never log secret values, only their key names.
