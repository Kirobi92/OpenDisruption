# Agent Installation — Quick Start

> **The whole installation is one command.** Pick the section that matches
> who you are.

---

## 🤖 If you are a coding agent (Claude / GPT / Cursor / Copilot / …)

1. Load `AGENT-SYSTEM-PROMPT.md` into your system prompt **verbatim**.
2. Run:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh \
     | bash -s -- --auto --yes --profile=auto
   ```

3. Read `.kirobi/install.json` for hardware/profile facts.
4. From now on, follow `AGENT-DECISION-MATRIX.md` for every action and
   `AGENT-RECOVERY.md` when something breaks.

That’s it. Target autonomy: **95–100 %** for green-zone tasks.

---

## 👤 If you are a human

### Recommended

```bash
curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh | bash
```

You will be asked exactly **one** question (target directory). Everything
else is auto-detected.

### Air-gapped / paranoid

```bash
git clone https://github.com/Kirobi92/OpenDisruption.git
cd OpenDisruption
less install.sh                       # read it first
bash install.sh --dry-run             # see what it will do
bash install.sh                       # run for real
```

### Re-run after pulling new commits

```bash
cd OpenDisruption
git pull
bash install.sh --no-clone --auto
```

### Stop / uninstall (data preserved)

```bash
bash install.sh --uninstall
```

To also wipe data: `cd OpenDisruption && docker compose down -v`.

---

## What it installs

- Ollama (local LLM runtime, GPU-accelerated when possible)
- Open WebUI (browser chat for Ollama)
- Qdrant (vector store, 7 zone-aware collections)
- Postgres 16 (relational storage + auth schema)
- Flowise (visual workflow builder)
- Caddy (reverse proxy + automatic local TLS at `kirobi.local`)
- The Family PWA (`apps/web`)
- Auth + API services (`services/auth`, `services/api`)
- Supporting infra: mDNS, healthchecks, backup hooks

Defaults are **local-first**: every port binds to `127.0.0.1`. Set
`KIROBI_BIND_HOST=0.0.0.0` in `.env` to expose on your LAN.

---

## Supported platforms

| Platform | Status |
|----------|--------|
| Ubuntu 22.04 / 24.04, Debian 12, Pop!_OS | ✅ first-class |
| Fedora 40+, Arch / Manjaro | ✅ supported |
| macOS (Apple Silicon) | ⚠️ CPU profile only — no NVIDIA passthrough |
| Windows | 🟡 only via WSL2 (Ubuntu) |
| Raspberry Pi / ARM SBCs | 🟡 `--profile=minimal` |

GPU support: NVIDIA (CUDA 12+) is the happy path. AMD (ROCm) is auto-detected.
Intel iGPU and CPU-only fall back gracefully.

---

## Troubleshooting

- See **`AGENT-RECOVERY.md`** — exhaustive playbook.
- Installer log: `/tmp/opendisruption-install-*.log`.
- Live status: `make status` and `docker compose logs -f <service>`.
- Re-validate environment: `bash infra/scripts/validate-env.sh`.

If you’re still stuck, open an issue with `.kirobi/install.json` attached
(it contains no secrets, only hardware facts).
