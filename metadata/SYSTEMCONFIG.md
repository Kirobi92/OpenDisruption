# System-Konfiguration: Kirobi / Disruptive OS

**Version:** 1.0 | **Letzte Aktualisierung:** 2024 | **Zone:** WORKSPACE

---

## Hardware-Konfiguration

### Empfohlene Mindestanforderungen
| Komponente | Minimum | Empfohlen |
|-----------|---------|-----------|
| CPU | 8 Kerne | 16+ Kerne |
| RAM | 32 GB | 64+ GB |
| SSD (System) | 256 GB | 512+ GB |
| SSD (Daten) | 500 GB | 2+ TB |
| GPU | GTX 1080 (8GB VRAM) | RTX 4090 (24GB VRAM) |
| Netzwerk | 100 Mbit/s | 1 Gbit/s |

### Kirobi Hardware (Referenzsystem)
- **CPU:** AMD Ryzen 9 7950X (16 Kerne / 32 Threads)
- **RAM:** 128 GB DDR5-6000
- **GPU:** NVIDIA RTX 4090 (24 GB VRAM)
- **SSD:** 2x 2TB NVMe (System + Daten)
- **OS:** Ubuntu 22.04 LTS

---

## Software-Stack

### Core Services
| Service | Version | Port | Zweck |
|---------|---------|------|-------|
| Ollama | latest | 11434 | LLM-Hosting |
| Open WebUI | latest | 3000 | Chat-Interface |
| Qdrant | latest | 6333/6334 | Vektor-Datenbank |
| PostgreSQL | 16 | 5432 | Relationale Datenbank |
| Flowise | latest | 3001 | Workflow-Orchestrierung |

### Optionale Services
| Service | Port | Zweck |
|---------|------|-------|
| Langfuse | 3002 | LLM-Observability |
| OpenObserve | 5080 | System-Monitoring |
| Perplexica | 3010 | Web-Recherche |
| Stable Diffusion | 7860 | Bildgenerierung |
| AnythingLLM | 3100 | Alternative UI |

---

## Modell-Konfiguration

### Standard-Modell-Zuweisung
```yaml
routing:
  supervisor: llama3.1:70b
  reasoning: deepseek-r1:32b
  coding: qwen2.5-coder:32b
  general: llama3.1:8b
  fast: phi3.5:3.8b
  embedding: nomic-embed-text
  vision: llava:13b
```

### Kontext-Längen
```yaml
context_lengths:
  llama3.1-70b: 131072
  llama3.1-8b: 131072
  deepseek-r1-32b: 65536
  qwen2.5-coder-32b: 32768
  phi3.5: 128000
```

---

## Netzwerk-Konfiguration

### Docker Network
- **Name:** `kirobi-net`
- **Typ:** Bridge
- **Subnet:** 172.20.0.0/16 (auto-assigned)
- **DNS:** Docker-intern + Host-DNS

### Port-Mapping (Standard)
```
Host:11434  → kirobi-ollama:11434
Host:3000   → kirobi-open-webui:8080
Host:3001   → kirobi-flowise:3000
Host:6333   → kirobi-qdrant:6333
Host:6334   → kirobi-qdrant:6334 (gRPC)
Host:5432   → kirobi-postgres:5432
```

### Firewall-Regeln (empfohlen)
- Ports nur lokal (127.0.0.1) binden, nicht öffentlich
- Reverse Proxy (nginx/traefik) für externe Zugriffe
- Keine direkten DB-Ports nach außen

---

## Sicherheits-Konfiguration

### Secrets-Management
- Alle Passwörter in `.env` (nie committen)
- `.env` mit `chmod 600` schützen
- Backup-Keys separat sichern (Passwort-Manager)

### Zonen-Enforcement
```yaml
zones:
  PUBLIC:
    embedding: true
    cloud_sync: allowed
    external_api: allowed
  WORKSPACE:
    embedding: true
    cloud_sync: with_confirmation
    external_api: allowed
  FAMILY_PRIVATE:
    embedding: local_only
    cloud_sync: never
    external_api: never
  QUARANTINE:
    embedding: false
    cloud_sync: never
    external_api: never
  SACRED:
    embedding: encrypted_local_only
    cloud_sync: never
    external_api: never
```

---

## Performance-Konfiguration

### Ollama-Optimierungen
```bash
OLLAMA_NUM_PARALLEL=2        # Parallele Anfragen
OLLAMA_MAX_LOADED_MODELS=3   # Gleichzeitig geladene Modelle
OLLAMA_KEEP_ALIVE=5m         # Modell im RAM halten
```

### Qdrant-Optimierungen
```yaml
optimizers_config:
  default_segment_number: 2
  max_segment_size: 200000
  memmap_threshold: 50000
  indexing_threshold: 20000
  flush_interval_sec: 5
  max_optimization_threads: 2
```

### PostgreSQL-Optimierungen
```sql
max_connections = 100
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
```
