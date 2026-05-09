# Developer Runbook: Kirobi / Disruptive OS

**Version:** 1.1
**Date:** 2026-05-05
**Classification:** WORKSPACE
**Audience:** Developers, operators, contributors

---

## Local Python Core (`kirobi_core`)

The repository ships a **pure-stdlib Python package** at `kirobi_core/`
that implements the local-first orchestrator, interview engine,
backlog generator, doctor health-check and a **safe autonomous loop**
(dry-run by default). It runs on any Python 3.10+ without `pip
install` and without the Docker stack — useful for CI, dev laptops
and the "tonight clone & run" path.

### Entry points

```bash
python -m kirobi_core version           # version string
python -m kirobi_core doctor            # environment health check
python -m kirobi_core doctor --live     # also probe the running stack
python -m kirobi_core status            # one-shot stack status table
python -m kirobi_core status --json     # machine-readable status
python -m kirobi_core scan              # JSON repo summary
python -m kirobi_core backlog --limit 5 # priorised tasks as JSON
python -m kirobi_core registry          # parsed AGENTREGISTRY.md
python -m kirobi_core interview         # guided onboarding (CLI)
python -m kirobi_core autonomous-once   # one dry-run iteration
python -m kirobi_core autonomous-loop --interval 900 \
        --quiet-hours "22:00-07:00"     # supervised loop
```

The same commands are exposed via `make`:

| Make target              | Description                                                  |
|--------------------------|--------------------------------------------------------------|
| `make bootstrap`         | `.env` + `doctor` + `scan` (no Docker required)              |
| `make doctor`            | Environment health checks                                    |
| `make scan`              | Repository scan summary                                      |
| `make backlog`           | Generate the prioritised backlog (`LIMIT=N`)                 |
| `make interview`         | Guided onboarding interview (`PROFILE=name`)                 |
| `make autonomous-once`   | One safe iteration; report under `.kirobi/reports/`          |
| `make autonomous-loop`   | Loop with `INTERVAL=`, `ITERATIONS=`, `QUIET_HOURS=`         |
| `make status`            | Live stack probes (Ollama / Qdrant / Postgres / API …)       |
| `make integration-test`  | Repo-Gate: unit tests + compose/scripts/PWA checks           |
| `make test`              | Run the stdlib-first `pytest tests/unit` baseline; optional service tests auto-skip without service deps |

### Stack integration

* `kirobi_core.services` speaks directly to the running services with
  stdlib `urllib` only — no `httpx`, no `requests`. Ollama and Qdrant
  also expose model and collection metadata through the probes.
* `kirobi_core.bridge` converts `kirobi_core.backlog.Task` objects into
  the pydantic `Task` shape that `services/orchestrator/supervisor.py`
  expects.
* `services/orchestrator/supervisor.py` automatically detects
  `kirobi_core` on `PYTHONPATH`. When `KIROBI_SEED_BACKLOG=true` is set
  the supervisor seeds its task queue from the local backlog on
  startup (limited by `KIROBI_SEED_LIMIT`, default `5`).
* `docker-compose.yml` binds every service port to
  `KIROBI_BIND_HOST` (default `127.0.0.1`). Set it to `0.0.0.0` only
  when LAN access is intentional.
* `infra/scripts/bootstrap.sh backup` honours `BACKUP_TARGET_DIR` and
  `BACKUP_RETENTION_DAYS` from `.env` and snapshots `canon/`,
  `experiences/` and `kirobi-core/` together.

### Safety model

* **Dry-run by default**: `autonomous-once` / `autonomous-loop` never
  modify repository files. They produce a JSON report with the planned
  routing decisions per task.
* **Zone-gated writes**: every proposed action goes through
  `kirobi_core.zones.can_write`, which only allows `PUBLIC` and
  `WORKSPACE` paths. `FAMILY_PRIVATE`, `QUARANTINE` and `SACRED`
  always require explicit human approval.
* **Sandboxed**: `kirobi_core.zones.is_inside_repo` makes sure no
  autonomous file operation can escape the repository root.
* **Audit log**: every routing decision and loop iteration is appended
  as JSON-Lines to `kirobi-core/core-events.log`. The file is kept
  locally and ignored by Git so runtime writes do not keep the worktree
  dirty. Secrets are redacted automatically.
* **Quiet hours**: `--quiet-hours "22:00-07:00"` skips iterations
  inside the configured window, including midnight wrap-around.
* **Sensitive interview answers** are written to a separate file
  under `extracts/family-private/profiles/` (or another zone you
  pick); the main profile only stores a pointer.

### Tests

```bash
make test         # stdlib-first baseline; service-contract tests skip without FastAPI/httpx/asyncpg extras
```

Tests live under `tests/unit/`. The fresh-clone baseline only needs
`pytest`; service-contract tests are collected automatically once the
optional service-stack dependencies are installed. Add `pytest -k <name>`
for focused runs.

---

## Quick Start

### Prerequisites

```bash
# Required
- Docker & Docker Compose v2+
- Git 2.40+
- NVIDIA GPU with CUDA 12.0+ (recommended)
- 32+ GB RAM
- 500+ GB SSD
- Linux (Ubuntu 22.04+ recommended)

# Optional
- Make
- Python 3.10+ (for scripts)
- Node.js 18+ (nur für Arbeit an `apps/web`, `apps/dashboard` oder `apps/voice`)
```

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/Kirobi92/OpenDisruption.git
cd OpenDisruption

# 2. Read mandatory documentation
cat CLAUDE.md          # Mandatory for AI agents
cat README.md          # System overview
cat ARCHITECTURE.md    # Architecture guide

# 3. Initialize system
make init              # Creates folders, copies .env.example to .env

# 4. Configure environment
nano .env              # Update passwords and settings

# 5. Start services
make up                # Starts all Docker containers

# optional: nur die kanonische Family-PWA
make pwa-up

# optional: zentrales UI-Bundle inkl. Open WebUI/Flowise
make webui-up

# 6. Pull models
make pull-models       # Downloads Ollama models (takes time!)

# 7. Verify status
make status            # Check all services are healthy
```

### First-Time Model Setup

```bash
# Essential models for MVP
docker exec -it kirobi-ollama ollama pull llama3.1:8b      # Fast, versatile
docker exec -it kirobi-ollama ollama pull mistral:7b       # Good balance
docker exec -it kirobi-ollama ollama pull nomic-embed-text # Embeddings

# Optional (large, but powerful)
docker exec -it kirobi-ollama ollama pull llama3.1:70b     # Supervisor
docker exec -it kirobi-ollama ollama pull deepseek-r1:32b  # Reasoning
docker exec -it kirobi-ollama ollama pull qwen2.5-coder:32b # Code
```

---

## Daily Operations

### Starting the System

```bash
# Start all services
make up

# Start specific service
docker compose up -d ollama

# View startup logs
make logs

# Verify health
make status
```

### Stopping the System

```bash
# Stop all services (keeps data)
make down

# Stop specific service
docker compose stop ollama

# Stop and remove containers (keeps volumes)
docker compose down

# Nuclear option: stop and delete ALL data
make reset  # ⚠️ WARNING: Deletes everything!
```

### Accessing Services

```bash
# Family PWA (canonical product surface)
open http://localhost:3002
# or via Caddy/mDNS
open http://kirobi.local/

# Admin dashboard
open http://localhost:3003

# Voice UI
open http://localhost:3004

# Open WebUI (auxiliary)
open http://localhost:3000

# Flowise (workflow builder)
open http://localhost:3001

# Qdrant dashboard (vector DB)
open http://localhost:6333/dashboard

# Ollama API (direct)
curl http://localhost:11434/api/tags
```

---

## Common Tasks

### Adding a New Document

```bash
# 1. Determine zone classification
# PUBLIC / WORKSPACE / FAMILY_PRIVATE / QUARANTINE / SACRED

# 2. Place file in appropriate location
cp new-doc.md extracts/workspace/

# 3. Add frontmatter (if markdown)
---
zone: WORKSPACE
created: 2026-05-05
author: sven
tags: [documentation, example]
---

# Document content here

# 4. (Future) Run ingestion pipeline to embed in Qdrant
# Currently manual, will be automated
```

### Updating Models

```bash
# Check current models
make list-models

# Pull updated model
docker exec -it kirobi-ollama ollama pull llama3.1:8b

# Remove old model
docker exec -it kirobi-ollama ollama rm llama3.1:7b

# Check disk usage
docker exec -it kirobi-ollama ollama list
```

### Managing Qdrant Collections

```bash
# List collections
curl http://localhost:6333/collections | jq

# Create collection (example)
curl -X PUT http://localhost:6333/collections/kirobi_test \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    }
  }'

# Delete collection
curl -X DELETE http://localhost:6333/collections/kirobi_test

# Get collection info
curl http://localhost:6333/collections/kirobi_workspace | jq
```

### Database Operations

```bash
# Connect to PostgreSQL
make db-shell

# Or manually
docker compose exec postgres psql -U kirobi -d kirobi

# Common queries
SELECT * FROM agents LIMIT 10;
SELECT * FROM documents WHERE zone = 'WORKSPACE';
SELECT * FROM events ORDER BY timestamp DESC LIMIT 20;

# Backup database
docker compose exec postgres pg_dump -U kirobi kirobi > backup.sql

# Restore database
cat backup.sql | docker compose exec -T postgres psql -U kirobi -d kirobi
```

### Viewing Logs

```bash
# All services
make logs

# Specific service
make logs-service SERVICE=ollama
# or
docker compose logs -f ollama

# System events (Kirobi-specific)
cat kirobi-core/core-events.log

# Last 50 lines
tail -50 kirobi-core/core-events.log

# Follow in real-time
tail -f kirobi-core/core-events.log
```

### Restarting Services

```bash
# Restart all
make restart

# Restart specific service
make restart-service SERVICE=flowise
# or
docker compose restart flowise

# Hard restart (recreate container)
docker compose up -d --force-recreate flowise
```

---

## Troubleshooting

### Service Won't Start

**Symptom:** `docker compose up` fails

**Diagnosis:**

```bash
# Check logs
docker compose logs [service-name]

# Check if port is already in use
sudo lsof -i :3002  # Family PWA
sudo lsof -i :3003  # Dashboard
sudo lsof -i :3004  # Voice UI
sudo lsof -i :3000  # Open WebUI
sudo lsof -i :11434 # Ollama
sudo lsof -i :6333  # Qdrant

# Check Docker status
systemctl status docker

# Check disk space
df -h
```

**Solutions:**

```bash
# Kill process on port
sudo kill -9 [PID]

# Restart Docker
sudo systemctl restart docker

# Free up disk space
docker system prune -f

# Check and fix .env file
cat .env  # Verify no syntax errors
```

### Ollama Model Not Loading

**Symptom:** Model returns errors or is very slow

**Diagnosis:**

```bash
# Check GPU availability
nvidia-smi

# Check Ollama logs
docker compose logs ollama

# Check model is downloaded
docker exec kirobi-ollama ollama list
```

**Solutions:**

```bash
# Re-download model
docker exec -it kirobi-ollama ollama pull llama3.1:8b

# Check GPU is accessible to container
docker compose exec ollama nvidia-smi

# Restart Ollama
docker compose restart ollama

# If still failing, use CPU mode
# Edit docker-compose.yml, comment out GPU section
```

### Qdrant Not Responding

**Symptom:** Vector search fails or times out

**Diagnosis:**

```bash
# Check Qdrant is running
docker compose ps qdrant

# Check Qdrant logs
docker compose logs qdrant

# Test connectivity
curl http://localhost:6333/
```

**Solutions:**

```bash
# Restart Qdrant
docker compose restart qdrant

# Check volume health
docker volume inspect kirobi_qdrant_data

# If corrupted, rebuild (⚠️ loses data)
docker compose down
docker volume rm kirobi_qdrant_data
make up
# Re-index all documents
```

### PostgreSQL Connection Errors

**Symptom:** Services can't connect to database

**Diagnosis:**

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Test connection
docker compose exec postgres pg_isready -U kirobi
```

**Solutions:**

```bash
# Restart PostgreSQL
docker compose restart postgres

# Check credentials in .env
cat .env | grep POSTGRES

# Manual connection test
docker compose exec postgres psql -U kirobi -d kirobi

# If corrupt, restore from backup
cat backup.sql | docker compose exec -T postgres psql -U kirobi -d kirobi
```

### Disk Space Full

**Symptom:** Services crashing, writes failing

**Diagnosis:**

```bash
# Check disk usage
df -h
du -sh /var/lib/docker
du -sh OpenDisruption

# Check Docker volume sizes
docker system df -v
```

**Solutions:**

```bash
# Remove old containers and images
docker system prune -a -f

# Remove old models
docker exec kirobi-ollama ollama rm [old-model]

# Clean up /archive/ and /quarantine/
rm -rf archive/old-snapshots/*

# Move logs to external storage
# Or implement log rotation
```

### Agent Misbehaving

**Symptom:** Agent gives wrong answers, violates zones

**Diagnosis:**

```bash
# Check agent prompt
cat kirobi-core/core-prompts/[agent]-prompt.md

# Check event log for violations
grep "ZONE_VIOLATION" kirobi-core/core-events.log
grep "[agent-name]" kirobi-core/core-events.log

# Check if safety prefix is applied
# Manual inspection needed
```

**Solutions:**

```bash
# Re-read CLAUDE.md and safety prompts
# Update agent system prompt
nano kirobi-core/core-prompts/[agent]-prompt.md

# Restart affected services
docker compose restart flowise

# If serious, disable agent temporarily
# Document incident in experiences/learnings/agent-errors.md
```

---

## Backup & Recovery

### Manual Backup

```bash
# Backup entire system
./infra/scripts/bootstrap.sh backup

# Or manually backup components
# 1. File system (git-tracked files)
git bundle create kirobi-backup.bundle --all

# 2. Docker volumes
docker run --rm -v kirobi_qdrant_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/qdrant-backup.tar.gz /data

docker run --rm -v kirobi_postgres_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/postgres-backup.tar.gz /data

docker run --rm -v kirobi_ollama_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/ollama-backup.tar.gz /data

# 3. Environment config (⚠️ contains secrets)
cp .env .env.backup
# Encrypt before storing
gpg -c .env.backup
```

### Automated Backup

```bash
# Configured via .env
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
BACKUP_TARGET_DIR=/mnt/backup/kirobi
BACKUP_RETENTION_DAYS=30
BACKUP_ENCRYPT=true
BACKUP_ENCRYPTION_KEY=CHANGE_ME

# Check backup status
ls -lh /mnt/backup/kirobi/

# Test backup
./infra/scripts/bootstrap.sh backup

# Verify backup contents
tar -tzf /mnt/backup/kirobi/backup-2026-05-05.tar.gz | head
```

### Restore from Backup

```bash
# ⚠️ WARNING: This will overwrite current data

# 1. Stop all services
make down

# 2. Restore git-tracked files
git clone [backup-location] OpenDisruption-restore
cd OpenDisruption-restore

# 3. Restore Docker volumes
docker run --rm -v kirobi_qdrant_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/qdrant-backup.tar.gz -C /

docker run --rm -v kirobi_postgres_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/postgres-backup.tar.gz -C /

docker run --rm -v kirobi_ollama_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/ollama-backup.tar.gz -C /

# 4. Restore .env
gpg -d .env.backup.gpg > .env

# 5. Start services
make up

# 6. Verify
make status
```

---

## Performance Optimization

### Model Selection for Speed

```bash
# Fast (< 5 sec response)
llama3.1:8b
mistral:7b
qwen2.5-coder:7b

# Balanced (5-15 sec response)
llama3.1:13b
mixtral:8x7b
deepseek-r1:32b (reasoning tasks)

# Powerful but slow (15-60+ sec response)
llama3.1:70b
qwen2.5-coder:32b
```

### GPU Optimization

```bash
# Check current GPU usage
nvidia-smi

# Configure in .env
OLLAMA_GPU_MEMORY_FRACTION=0.9  # Use 90% of GPU
OLLAMA_NUM_PARALLEL=2           # Run 2 models simultaneously

# Monitor GPU utilization
watch -n 1 nvidia-smi
```

### Qdrant Performance Tuning

```yaml
# In qdrant config (future)
storage:
  mmap_enabled: true
  disk_cache_size_mb: 2048

collection:
  vectors:
    on_disk: false  # Keep in RAM for speed
  optimizer:
    max_segment_size_kb: 200000
```

### PostgreSQL Performance

```sql
# Check slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

# Add indexes (when needed)
CREATE INDEX idx_documents_zone ON documents(zone);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);

# Vacuum regularly
VACUUM ANALYZE;
```

---

## Development Workflow

### Making Changes to Core Files

```bash
# 1. Create branch
git checkout -b feature/my-change

# 2. Read relevant docs first
cat CLAUDE.md
cat metadata/ZONE-POLICY-MATRIX.md

# 3. Make changes
nano kirobi-core/core-identity.md

# 4. Test locally
make restart
# Verify changes work

# 5. Commit with clear message
git add kirobi-core/core-identity.md
git commit -m "feat(core): update agent identity prompt"

# 6. Push and create PR
git push origin feature/my-change
```

### Adding a New Agent

```bash
# 1. Update agent registry
nano metadata/AGENTREGISTRY.md
# Add new agent entry

# 2. Create agent prompt
nano kirobi-core/core-prompts/new-agent-prompt.md

# 3. Update permissions
nano metadata/ZONE-POLICY-MATRIX.md
# Add read/write permissions

# 4. Create Flowise workflow (optional)
# Open http://localhost:3001
# Create new flow for agent

# 5. Test agent
# Use Open WebUI to interact
# Verify zone access is correct

# 6. Document
nano experiences/learnings/new-agent-notes.md
```

### Updating Security Policies

```bash
# ⚠️ Security-critical - review carefully

# 1. Read current policies
cat CLAUDE.md
cat metadata/ZONE-POLICY-MATRIX.md
cat SECURITY.md

# 2. Make changes
nano metadata/ZONE-POLICY-MATRIX.md

# 3. Update dependent docs
nano CLAUDE.md  # Update section 5 if permissions changed

# 4. Test enforcement
# Verify agents respect new policies

# 5. Document in commit
git commit -m "security(zones): restrict agent X from FAMILY_PRIVATE

Rationale: Agent X does not need family data access.
Impact: Agent X can no longer read /extracts/family-private/
Testing: Verified agent returns permission denied"

# 6. Log to events
echo "[$(date)] SECURITY_POLICY_UPDATE: Updated ZONE-POLICY-MATRIX.md" \
  >> kirobi-core/core-events.log
```

---

## Testing

### Manual Testing

```bash
# repo gate
python3 -m pytest tests/unit -q
make integration-test

# stack health
make status

# Test Family PWA
# 1. Open http://localhost:3002 or http://kirobi.local/
# 2. Login with bootstrap user from .env
# 3. Verify /chat, /search, /upload, /settings, /status

# Test Dashboard
# 1. Open http://localhost:3003
# 2. Verify service cards and task feed load

# Test Voice UI
# 1. Open http://localhost:3004
# 2. Verify microphone permission and API reachability

# Optional auxiliary UIs
open http://localhost:3000   # Open WebUI
open http://localhost:3001   # Flowise
```

### Smoke Tests (Future)

```bash
# When implemented
make test-smoke

# Should verify:
# - All services start
# - Models are accessible
# - Databases are reachable
# - Basic queries work
```

### Integration Tests (Future)

```bash
# When implemented
make test-integration

# Should verify:
# - Agent orchestration
# - Zone enforcement
# - RAG pipeline
# - Backup/restore
```

### Security Tests (Future)

```bash
# When implemented
make test-security

# Should verify:
# - Prompt injection resistance
# - Zone violations blocked
# - Secrets not leaked
# - Audit logging works
```

---

## Monitoring

### System Health

```bash
# Quick status
make status

# Detailed health
./infra/scripts/healthcheck.sh

# Resource usage
docker stats

# Disk usage
du -sh .
docker system df
```

### Application Metrics

```bash
# Ollama stats
curl http://localhost:11434/api/tags

# Qdrant stats
curl http://localhost:6333/telemetry | jq

# PostgreSQL stats
docker compose exec postgres psql -U kirobi -d kirobi \
  -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

### Event Monitoring

```bash
# Follow events in real-time
tail -f kirobi-core/core-events.log

# Search for specific events
grep "ZONE_VIOLATION" kirobi-core/core-events.log
grep "ERROR" kirobi-core/core-events.log
grep "kirobi-coder" kirobi-core/core-events.log

# Count events by type
cat kirobi-core/core-events.log | cut -d' ' -f3 | sort | uniq -c
```

---

## Security Operations

### Reviewing Audit Logs

```bash
# Check zone access
grep "ZONE_ACCESS" kirobi-core/core-events.log

# Check SACRED access (should be rare)
grep "SACRED" kirobi-core/core-events.log

# Check external API calls
grep "EXTERNAL_API_CALL" kirobi-core/core-events.log

# Check permission denials
grep "PERMISSION_DENIED" kirobi-core/core-events.log
```

### Incident Response

```bash
# If suspicious activity detected:

# 1. Capture evidence
cp kirobi-core/core-events.log \
   experiences/learnings/security-incidents/INC-$(date +%Y%m%d)/

# 2. Stop services if needed
make down

# 3. Create incident report
cp templates/incident-template.md \
   experiences/learnings/security-incidents/INC-$(date +%Y%m%d)/report.md

# 4. Fill out incident report
nano experiences/learnings/security-incidents/INC-$(date +%Y%m%d)/report.md

# 5. Follow incident response procedures (SECURITY.md)
```

### Rotating Secrets

```bash
# 1. Generate new secrets
openssl rand -base64 32  # For keys
pwgen 32 1               # For passwords

# 2. Update .env
nano .env

# 3. Restart affected services
docker compose down
docker compose up -d

# 4. Update any stored credentials
# (e.g., M365 OAuth tokens)

# 5. Test services still work
make status

# 6. Document rotation
echo "[$(date)] SECRET_ROTATION: Rotated OpenWebUI secret key" \
  >> kirobi-core/core-events.log
```

---

## Maintenance Tasks

### Weekly

- [ ] Review `kirobi-core/core-events.log` for anomalies
- [ ] Check disk space (`df -h`)
- [ ] Review `/quarantine/` folder, promote or delete
- [ ] Check for model updates (optional)

### Monthly

- [ ] Full system backup verification (test restore)
- [ ] Review and clean `/archive/`
- [ ] Update Docker images (`docker compose pull`)
- [ ] Review security policies
- [ ] Check for dependency updates

### Quarterly

- [ ] Security audit using `AUDIT-REPORT.md` template
- [ ] Review and update `THREAT-MODEL.md`
- [ ] Performance optimization review
- [ ] Major version upgrades (if needed)
- [ ] Disaster recovery drill

---

## Common Makefile Commands

```bash
make help           # Show all available commands
make init           # Initialize system (first time)
make up             # Start all services
make down           # Stop all services
make restart        # Restart all services
make logs           # View logs (all services)
make status         # Check system health
make pull-models    # Download Ollama models
make backup         # Create backup
make clean          # Clean Docker resources
make validate       # Validate docker-compose.yml
make list-models    # List installed Ollama models
make db-shell       # Open PostgreSQL shell
make qdrant-collections  # List Qdrant collections
```

---

## Emergency Contacts

**System Owner:** Sven Darusi

**For Critical Issues:**
1. Stop services: `make down`
2. Capture logs: `docker compose logs > emergency-logs.txt`
3. Create incident report: Use `/templates/incident-template.md`
4. Restore from backup if needed

**External Help:**
- Docker issues: https://docs.docker.com/
- Ollama issues: https://github.com/ollama/ollama/issues
- Qdrant issues: https://github.com/qdrant/qdrant/issues

---

## Appendix: Useful Commands

### Docker

```bash
# Remove all stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes (⚠️ data loss)
docker volume prune -f

# See container resource usage
docker stats --no-stream

# Execute command in container
docker compose exec [service] [command]

# Copy file from container
docker cp kirobi-ollama:/root/.ollama/models/manifest ./backup/
```

### Git

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all local changes
git reset --hard HEAD

# View file at specific commit
git show [commit-hash]:path/to/file

# Search commit history
git log --all --grep="security"

# Show changes in specific file
git log -p kirobi-core/core-policies.md
```

### System

```bash
# Check GPU
nvidia-smi
watch -n 1 nvidia-smi

# Check processes
ps aux | grep ollama
htop

# Check network
netstat -tlnp
ss -tlnp

# Check disk I/O
iostat -x 1

# Check memory
free -h
vmstat 1
```

---

**Document Version:** 1.0
**Last Updated:** 2026-05-05
**Maintained By:** System architects and operators

**For AI Agents:** Read `/CLAUDE.md` first before making any changes!
