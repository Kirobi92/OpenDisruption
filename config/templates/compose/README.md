---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# config/templates/compose

Docker Compose Profil-Templates für verschiedene Hardware- und Einsatzszenarien.
Der Installer wählt das passende Profil und schreibt es als `docker-compose.override.yml` oder setzt `COMPOSE_FILE` in `.env`.

## Wichtige Dateien

- `profile-minimal.yml` — Minimalprofil ohne Voice und Supervisor
- `profile-cpu.yml` — CPU-only, kein GPU-Beschleunigung
- `profile-amd.yml` — AMD ROCm GPU-Unterstützung
- `profile-nvidia.yml` — NVIDIA CUDA GPU-Unterstützung
- `profile-voice-full.yml` — Vollständiges Voice-Processing (benötigt Docker Compose ≥ 2.24)
- `profile-development.yml` — Entwicklungsmodus mit Hot-Reload und Debug-Ports
- `profile-production.yml` — Produktionshärtung mit Resource-Limits
