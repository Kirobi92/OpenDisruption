---
zone: WORKSPACE
type: wissen
version: 1.0
---

# Kirobi System-Architektur: Betriebswissen

## Zusammenfassung
Kirobi ist ein lokales, agenten-gestütztes Wissens-Betriebssystem. Alle Daten bleiben lokal. Agenten kommunizieren über definierte Protokolle.

## Kern-Komponenten

### Ollama (Port 11434)
- Läuft lokale LLMs
- Direkt-Zugriff nur für genehmigte Agenten
- Modelle in `infra/mounts/models/ollama/`

### Open-WebUI (Port 3000)
- Haupt-Oberfläche für menschliche Interaktion
- Authentifizierung: Lokal, kein Cloud-Login
- Gespräche werden lokal gespeichert

### Qdrant (Port 6333/6334)
- Vektor-Datenbank für semantische Suche
- Collections pro Zone getrennt
- Nur lokale Verbindungen

### PostgreSQL (Port 5432)
- Strukturierte Daten für Flowise
- Kein direkter Außen-Zugriff

### Flowise (Port 3001)
- Visual-Builder für Agent-Workflows
- Flows in `integrations/flows/`
- Backup-Routine täglich

## Wichtige Befehle
```bash
make up        # Alles starten
make down      # Alles stoppen
make logs      # Logs anzeigen
make status    # Status aller Services
make backup    # Backup starten
```
