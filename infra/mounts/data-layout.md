# Daten-Layout: Kirobi Mounts

**Zone:** WORKSPACE | **Version:** 1.0

---

## Host-System Verzeichnis-Layout

```
/var/kirobi/                    # Hauptdaten-Verzeichnis
├── data/
│   ├── ollama/                 # Ollama Modell-Daten (bind mount)
│   ├── qdrant/                 # Qdrant Vektordatenbank
│   ├── postgres/               # PostgreSQL Daten
│   ├── openwebui/              # Open WebUI Daten
│   └── flowise/                # Flowise Daten
├── backups/
│   ├── qdrant/                 # Qdrant Snapshots
│   ├── postgres/               # PostgreSQL Dumps
│   ├── canon/                  # Canon-Backups
│   └── experiences/            # Experiences-Backups
└── logs/                       # System-Logs
```

## Docker Volume Mapping

| Volume | Host-Pfad | Container-Pfad |
|--------|-----------|----------------|
| `ollama_data` | `/var/kirobi/data/ollama` | `/root/.ollama` |
| `qdrant_data` | `/var/kirobi/data/qdrant` | `/qdrant/storage` |
| `postgres_data` | `/var/kirobi/data/postgres` | `/var/lib/postgresql/data` |
| `openwebui_data` | `/var/kirobi/data/openwebui` | `/app/backend/data` |
| `flowise_data` | `/var/kirobi/data/flowise` | `/root/.flowise` |

## Speicherplanung

| Komponente | Min | Empfohlen | Wächst mit |
|-----------|-----|-----------|-----------|
| Ollama Modelle | 10 GB | 100+ GB | Neuen Modellen |
| Qdrant | 1 GB | 50+ GB | Eingebetteten Docs |
| PostgreSQL | 500 MB | 10 GB | Sessions, Logs |
| Open WebUI | 100 MB | 5 GB | Chat-Historie |
| Flowise | 100 MB | 2 GB | Workflows |
