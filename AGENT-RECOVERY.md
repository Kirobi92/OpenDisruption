# Agent Recovery Playbook

> What to do when an installation, an autonomous run, or a service goes
> sideways. Read top-to-bottom: the first matching scenario is the one to
> use.

---

## 0. Universal first response

```
1. STOP.            → no further mutating actions
2. CAPTURE.         → save logs (see §1)
3. DIAGNOSE.        → run the triage commands (see §2)
4. PICK A LADDER.   → find your scenario below, climb the smallest rung first
5. DOCUMENT.        → append outcome to experiences/learnings/agent-errors.md
```

---

## 1. Capture (always do this first)

```bash
# Snapshot of everything an analyst will need:
mkdir -p .kirobi/incidents/$(date +%Y%m%d-%H%M%S) && cd "$_"
docker compose ps                       > containers.txt 2>&1 || true
docker compose logs --tail=500 --no-color > compose.log    2>&1 || true
cp ../../.kirobi/install.json .                                    || true
tail -n 500 ../../kirobi-core/core-events.log > core-events.tail   || true
ls /tmp/opendisruption-install-*.log | tail -n1 | xargs -I{} cp {} install.log
uname -a > host.txt; df -h >> host.txt; free -h >> host.txt 2>/dev/null
```

The `.kirobi/incidents/<ts>/` directory is now an evidence bundle. **Never
include `.env`, `sacred/*`, `extracts/family-private/*`, or `experiences/family/*`
in incident exports.**

---

## 2. Triage commands

| Question | Command |
|----------|---------|
| Are containers running? | `docker compose ps` |
| Are they healthy? | `bash infra/scripts/healthcheck.sh` |
| Is `.env` valid? | `bash infra/scripts/validate-env.sh` |
| Is the compose file parseable? | `docker compose config --quiet` |
| What did the installer do? | `cat .kirobi/install.json` |
| Is a service crash-looping? | `docker compose logs --tail=200 <svc>` |
| Disk full? | `df -h` |
| RAM exhausted? | `free -h && docker stats --no-stream` |
| GPU visible to container? | `docker compose exec ollama nvidia-smi` |
| Postgres reachable? | `docker compose exec postgres pg_isready` |
| Qdrant reachable? | `curl -fsS http://127.0.0.1:6333/healthz` |

---

## 3. Recovery ladders (smallest rung first)

### 3.1 Installer aborted

| Rung | Action |
|------|--------|
| 1 | Re-read the last 50 lines of `/tmp/opendisruption-install-*.log`. |
| 2 | Resolve the missing prerequisite (the installer prints the command). |
| 3 | Re-run with `bash install.sh --no-clone --auto --verbose`. |
| 4 | If a partial state is suspected: `bash install.sh --no-clone --no-pull --no-models --no-start` to re-render only `.env` and folders. |
| 5 | Last resort: `mv ~/OpenDisruption ~/OpenDisruption.bak.$(date +%s)` and reinstall. Volumes (`docker volume ls`) survive. |

### 3.2 A single container is unhealthy

```bash
docker compose logs --tail=200 <svc>
docker compose restart <svc>          # rung 1
docker compose up -d --force-recreate <svc>   # rung 2
docker compose pull <svc> && docker compose up -d <svc>  # rung 3
```

If still failing, check the health-specific section below.

### 3.3 Ollama errors

| Symptom | Fix |
|---------|-----|
| `CUDA error: out of memory` | switch to a smaller model in `.env` (`OLLAMA_DEFAULT_MODEL=llama3.1:8b`), `docker compose restart ollama` |
| `nvidia-smi: command not found` inside container | install nvidia-container-toolkit on host, restart Docker |
| Models missing after restart | `bash infra/scripts/pull-models.sh` |
| `connection refused` from app to Ollama | check `OLLAMA_BASE_URL=http://ollama:11434` (service name, not localhost) |

### 3.4 Qdrant errors

| Symptom | Fix |
|---------|-----|
| `404 collection not found` | `make integration-test` re-seeds collections; or run the bootstrap script in `services/retrieval/` |
| `Wrong vector dimension` | check `metadata/COLLECTION-MAPPING.md`; never mix 768 and 1024 in the same collection |
| Storage corrupt after kill -9 | restore Qdrant volume from `archive/snapshots/`, restart |

### 3.5 Postgres errors

| Symptom | Fix |
|---------|-----|
| `password authentication failed` | check `POSTGRES_PASSWORD` in `.env` matches the volume; if reset is intended, `docker compose down`, `docker volume rm <stack>_postgres_data`, restart |
| `database "kirobi" does not exist` | `docker compose exec postgres psql -U kirobi -c "CREATE DATABASE kirobi;"` |
| auth schema missing | restart the `auth` service — it self-bootstraps the schema |

### 3.6 Caddy / reverse proxy

| Symptom | Fix |
|---------|-----|
| `kirobi.local` not resolvable | `bash infra/scripts/setup-mdns.sh`, ensure avahi/`mDNSResponder` is running |
| TLS warnings on first visit | trust the local Caddy CA: `docker compose exec caddy caddy trust` |
| 502 from Caddy | upstream service is down — see §3.2 |

### 3.7 GPU not detected

```bash
bash infra/scripts/detect-gpu.sh
bash infra/scripts/detect-system.sh --json | grep gpu
```

If host sees the GPU but the container does not:

```bash
# Linux + NVIDIA
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
docker compose up -d ollama
```

### 3.8 Disk full

```bash
docker system df            # who is using space?
docker image prune -f       # safe
docker builder prune -f     # safe
docker volume ls            # NEVER prune blindly — volumes are your data
bash infra/scripts/backup.sh   # snapshot before any destructive cleanup
```

### 3.9 Secrets accidentally committed

1. **STOP — do not push.**
2. Notify Sven immediately.
3. Rotate the leaked secret at the source (Ollama is local; OpenAI/Flowise
   keys must be revoked at the provider).
4. The human (not the agent) runs `git filter-repo` or BFG to strip history.
5. Force-push only after Sven’s explicit OK.

### 3.10 Suspected data loss in protected zone

1. **STOP all writes.**
2. List newest snapshots: `ls -lt archive/snapshots/`.
3. Restore the affected sub-tree only:
   `tar -xzf archive/snapshots/<file>.tar.gz -C /tmp/restore && diff -r …`
4. Move the verified restore back into place. Never blanket-overwrite.
5. Document in `experiences/learnings/agent-errors.md`.

### 3.11 Suspected security incident (intrusion / exfil / injection)

1. **STOP and isolate.** Take the host off the LAN if feasible.
2. **Do not delete evidence.** `kirobi-core/core-events.log`, `compose.log`,
   any incoming `sources/inbox/*` file are evidence.
3. Snapshot the state (see §1).
4. Wait for Sven. The agent does **not** unilaterally remediate security
   incidents.

---

## 4. Total reset (nuclear option)

Only when everything else has failed and Sven approves.

```bash
cd $HOME/OpenDisruption
bash infra/scripts/backup.sh             # snapshot current state
docker compose down                      # keep volumes
mv ../OpenDisruption ../OpenDisruption.broken.$(date +%s)
curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh \
  | bash -s -- --auto
# Volumes persist; the new checkout reattaches automatically.
```

To also wipe data: append `&& docker compose down -v` to the `down` command
**after** the backup completes successfully.

---

## 5. Post-mortem template

Append this to `experiences/learnings/agent-errors.md`:

```markdown
## Incident YYYY-MM-DD — <one-line summary>

- **Trigger** : <command / event>
- **Symptom** : <what failed>
- **Zone**    : <highest zone touched>
- **Detection time** : <how fast / how>
- **Root cause** : <why>
- **Fix**     : <what worked>
- **Prevention** : <code/doc change needed>
- **Evidence** : `.kirobi/incidents/<ts>/`
```

---

## 6. When to escalate to a human immediately

- Any `SACRED` access attempt that you did not explicitly initiate.
- Any outbound network call you cannot fully account for.
- Any `git push --force` or history rewrite suggestion.
- Any irreversible action when the human is offline.
- Any conflict between `AGENT-DECISION-MATRIX.md` and the user’s request.

When in doubt: **stop and ask**. Asking is the fastest possible recovery.
