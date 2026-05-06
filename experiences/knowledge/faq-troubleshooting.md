---
zone: WORKSPACE
type: faq
version: 1.0
---

# FAQ und Troubleshooting

## Häufige Probleme

### Problem: Ollama startet nicht
**Symptom:** `make status` zeigt Ollama als "unhealthy"  
**Mögliche Ursachen:**
1. NVIDIA-Treiber nicht installiert
2. Docker GPU-Support fehlt
3. Port 11434 bereits belegt

**Lösung:**
```bash
# GPU-Support prüfen
nvidia-smi
# Docker GPU-Test
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
# Logs prüfen
make logs | grep ollama
```

### Problem: Flowise lädt nicht
**Symptom:** Port 3001 nicht erreichbar  
**Lösung:** PostgreSQL-Healthcheck prüfen – Flowise startet erst wenn Postgres healthy ist.

### Problem: Qdrant-Collections leer
**Symptom:** Keine Ergebnisse bei Vektorsuche  
**Lösung:** Collections manuell anlegen über Qdrant-Dashboard (Port 6333).

### Problem: Open-WebUI Authentifizierung
**Symptom:** Kann mich nicht anmelden  
**Lösung:** Ersten Start: Admin-Account unter http://localhost:3000 erstellen.

## Nützliche Befehle

```bash
# Alle Container-Logs in Echtzeit
docker compose logs -f

# Einzelnen Service neu starten
docker compose restart flowise

# Qdrant Collections auflisten
curl http://localhost:6333/collections

# Ollama Modelle auflisten
curl http://localhost:11434/api/tags
```
