---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Public Assets (PWA)

Statische Dateien der Kirobi Family PWA — direkt vom Browser abrufbar,
ohne Build-Schritt. Enthält Icons, Manifest und Fallback-Seiten.

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `manifest.json` | PWA-Manifest (Name, Icons, Theme-Farben) |
| `icon.svg` | Quell-Icon (Vektorgrafik) |
| `icon-192.png` / `icon-512.png` | Standard-PWA-Icons |
| `icon-192-maskable.png` / `icon-512-maskable.png` | Maskierbare Icons für Android |
| `apple-touch-icon.png` | Icon für iOS Home-Screen |
| `favicon.ico` | Browser-Tab-Icon |
| `offline.html` | Fallback-Seite wenn offline |
| `robots.txt` | Crawler-Direktiven |

## Icons neu generieren

```bash
make pwa-icons
```
