---
zone: WORKSPACE
type: capability-matrix
version: 1.0
---

# Installer Agent: Capability Matrix

## Was der Installer kann

| Fähigkeit | Beschreibung | Automatisch |
|-----------|-------------|-------------|
| Voraussetzungs-Check | Docker, GPU, Speicher prüfen | ✅ |
| .env-Generierung | Aus Template generieren | ✅ |
| Docker-Start | Services starten | ✅ |
| Healthcheck | Alle Services testen | ✅ |
| Modell-Download | Ollama-Modelle herunterladen | ✅ |
| Qdrant-Init | Collections anlegen | ✅ |
| Erstes Onboarding | Nutzer einführen | Halb |

## Was der Installer NICHT tut

- Keine sensiblen Daten sammeln
- Keine Cloud-Verbindungen während Installation (außer Modell-Download)
- Keine System-Modifikationen außerhalb des Kirobi-Verzeichnisses
- Keine automatischen Updates ohne Nutzer-Einwilligung

## Unterstützte Betriebssysteme

| OS | Unterstützt | Einschränkungen |
|----|-------------|-----------------|
| Ubuntu 22.04+ | ✅ Vollständig | Keine |
| Debian 12+ | ✅ Vollständig | Keine |
| macOS 14+ | ⚠️ Eingeschränkt | Kein GPU-Support |
| Windows 11 (WSL2) | ⚠️ Eingeschränkt | WSL2 erforderlich |
