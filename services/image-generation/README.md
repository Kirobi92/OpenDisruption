---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Service: image-generation

KI-Bildgenerierung via Ollama — generiert Bilder auf Basis von Text-Prompts und speichert sie zone-konform.

## Was dieser Service tut

Nimmt einen Text-Prompt entgegen, leitet ihn an Ollama weiter und speichert das Ergebnis als PNG-Datei unter `/data/images/{zone}/{uuid}.png`. Metadaten (Prompt, Modell, Pfad, Zone) werden in PostgreSQL persistiert.

**Wichtig:** Mit `llava:7b` (Standard) wird kein echtes Bild gerendert — llava ist ein Vision-Analyse-Modell. Es wird ein Platzhalter-PNG mit dem generierten Text gespeichert. Für echte Pixel-Ausgabe ist ein Diffusion-Modell erforderlich.

## API-Endpoints

| Method | Pfad | Beschreibung |
|--------|------|--------------|
| `GET` | `/health` | DB- und Ollama-Status |
| `POST` | `/generate` | Bild generieren (Prompt, Modell, Zone, Größe) |
| `GET` | `/images` | Alle generierten Bilder (optional: `?zone=WORKSPACE`) |
| `GET` | `/images/{id}` | Metadaten eines einzelnen Bildes |

## Konfiguration (Env-Variablen)

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `OLLAMA_HOST` | `http://ollama:11434` | Ollama-Endpunkt |
| `POSTGRES_*` | — | Datenbankverbindung (User, Password, Host, Port, DB) |
| `IMAGE_STORAGE_PATH` | `/data/images` | Ablageort für generierte Bilder |
| `KIROBI_PUBLIC_ORIGINS` | — | CORS-Whitelist (leer = LAN-Regex) |

## Starten / Testen

```bash
# Im Container
docker compose up image-generation

# Health-Check
curl http://localhost:8011/health

# Bild generieren
curl -X POST http://localhost:8011/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Ein Sonnenuntergang", "model": "llava:7b", "zone": "WORKSPACE"}'
```

## Bekannte Einschränkungen

- `llava:7b` generiert Text, kein Bild — Platzhalter-PNG als Fallback
- Pillow ist optional: ohne Pillow wird ein hartkodiertes 1×1-PNG gespeichert
- Keine Authentifizierung am Service selbst — Absicherung erfolgt über Caddy
