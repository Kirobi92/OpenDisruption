# Changelog

## v10 — 2026-05-20 (Kirobi Debug APK 4,3 MB)

### Neue Features

#### 📊 Dashboard-Modul (Match-Log Qualitäts-Dashboard)
- `/api/dashboard` Endpoint im SystemModule integriert — zeigt letzte 10 Snapshots der Paperclip Reverse-Sync-Qualität
- Snapshot-Tabelle mit `matched_count`, `skip_count`, `marked_rate`, `assessment` (🔴/🟡/🟢) und Timestamp
- Trend-Pfeil (↑/↓/–) basierend auf letzten 2 Snapshots
- Ø MARKED-Rate + Min/Max-Range als Summary

#### 🎨 Sparkline-Chart (SVG-basiert, inline)
- Mini-Sparkline über alle verfügbaren Snapshots — rein SVG, keine externe Chart-Bibliothek
- Farbkodierung via `markedRateColor()`: grün ≥50%, gelb ≥20%, rot <20%
- Endpunkt-Kreis + aktueller Wert rechts am Chart sichtbar
- Y-Achse normalisiert auf tatsächlichen Min/Max-Bereich der Snapshots

#### 🌙 Tag/Nacht-Modus (dynamische Idle-Schwelle)
- Kirobi Backend erkennt Tageszeit automatisch:
  - Tag (06:00–22:00): `KIROBI_IDLE_LIMIT_DAY_S` (Standard: 600s)
  - Nacht (22:00–06:00): `KIROBI_IDLE_LIMIT_NIGHT_S` (Standard: 300s)
- Aktueller Modus (`Tag`/`Nacht`) + Schwellwert live im SystemModule sichtbar
- Rückwärtskompatibel mit alter `KIROBI_AUDIO_IDLE_LIMIT_S` Variable

#### 🔔 Alert-History
- Letzte 10 Alerts persistent in `alert_history.json` gespeichert (überlebt Neustarts)
- `/api/alerts` Endpoint: GET (History) + DELETE (einzeln per Timestamp oder alles löschen)
- Swipe-to-dismiss in APK v11: einzelne Alerts per Links-Swipe (>60px) oder ✕-Button quittieren
- Letzter Alert-Timestamp + „kein Alert" Indikator im SystemModule

#### ⚙️ ENV-Konfiguration (alle Schwellwerte konfigurierbar)
- Frontend: `VITE_MARKED_RATE_GREEN` (Standard: 50) + `VITE_MARKED_RATE_YELLOW` (Standard: 20)
- `.env.example` für Frontend erstellt mit allen `VITE_*`-Variablen dokumentiert
- Backend: `KIROBI_IDLE_LIMIT_DAY_S`, `KIROBI_IDLE_LIMIT_NIGHT_S` in `backend/.env.example` dokumentiert
- `kirobi-backend.service` systemd-Unit aktualisiert mit neuen ENV-Werten

### Technische Verbesserungen
- `/api/status` liefert jetzt `idle_limit_mode` + `idle_limit_s` + `last_alert_ts`
- `_active_connections` via Pipecat Transport-Hooks live gezählt (kein hardcoded-Wert mehr)
- GitHub Actions CI-Workflow: pytest bei jedem Push auf `main` (Python 3.11, Test-Modus gemockt)
- Alle Frontend-Module per Lazy-Loading (6 Bundles: agents, avatar, creative, family, inventory, system)

### Builds
| Datei | Größe | Typ |
|-------|-------|-----|
| `Kirobi-v10-debug.apk` | 4,3 MB | Debug (Telegram-Auslieferung) |
| `Kirobi-v10-release.apk` | — | Release-Kandidat (signiert) |

### SHA256 (v10-debug)
```
04541c00f7f2ba2d1a375bb664fa715aaaa2779c1302b2f5f03197b58fce88a4
```

---

## 2026-05-19 — Kirobi 24H Autonomy Sprint

### Task 7 operational review documentation fix

- Clarified that `Kirobi-v8-debug.apk` is the current delivered APK for this task.
- Clarified that Medusa/Webshop is an optional upstream dependency, not a guaranteed running Kirobi service.
- Clarified that `/api/commerce/status` can be reachable/OK while the Medusa upstream for `/api/commerce/products` is down.
- Documented that `/api/commerce/products` requires a reachable Medusa service plus `MEDUSA_PUBLISHABLE_KEY`; `503` is expected when the key is intentionally absent or Medusa is unavailable.
- Updated build instructions to select Node 22 before running `npm run build`.
- Removed stale unreferenced `Kirobi-v9-debug.apk`; v8 remains the current delivered APK.

### v8 Debug APK

APK:

```text
/Datenspeicher/OpenDisruption_v0.1/Benutzer-Ordner/Sven/Projekte/kirobi-avatar/Kirobi-v8-debug.apk
```

SHA256:

```text
07e091083331d7723084cb013eb7dc51dd6fb5b0a77767aa822e71de553de8ba
```

Added:

- Live voice persona hook wired into the real `backend/pipecat_server.py` runtime.
- Session-safe WebSocket event broadcaster for voice/persona events.
- Family API local/LAN/token guard.
- Sineo safety hardening for persona context and switching.
- `COMFY_URL` environment configuration for ComfyUI.
- `MEDUSA_PUBLISHABLE_KEY` environment configuration; no hardcoded publishable key.
- Creative/System frontend modules now share the backend resolver.

Verified:

- Backend `py_compile` OK for `backend/persona.py`, `backend/server.py`, `backend/pipecat_server.py`, `backend/pipeline/pipeline.py`, and `backend/routers/*.py` using the voice venv.
- `kirobi-backend.service` restarted and active.
- API smoke tests OK: `/health`, `/api/system/status`, `/api/family/persona/context`, persona switch `sineo` and back to `sven`, `/api/creative/comfyui/status`, `/api/commerce/status`.
- Frontend `npm run build` OK.
- Capacitor `npx cap sync android` OK.
- Android Gradle `assembleDebug` OK with `JAVA_HOME=/Datenspeicher/jdk21` and `ANDROID_SDK_ROOT=/Datenspeicher/android-sdk`.
- Debug APK copied to project root and SHA256 computed.

### v7 Debug APK

APK:

```text
/Datenspeicher/OpenDisruption_v0.1/Benutzer-Ordner/Sven/Projekte/kirobi-avatar/Kirobi-v7-debug.apk
```

SHA256:

```text
d7ffb6c5d6c67c0caf1e30a48f4e06e7a88411000d0392ba11c2b34d8766a3cd
```

Added:

- System tab Live-Logstream UI.
- Backend SSE endpoint `GET /api/system/logs/{service}` for allowlisted systemd services.
- Backend ComfyUI image proxy so generated images work from Android/LAN.
- Documentation in `README.md`.

Verified:

- Backend health OK.
- System status OK for Kirobi backend/audio/frontend, ComfyUI, InvenTree, Hindsight, Open WebUI, Ollama.
- Frontend TypeScript/Vite build OK.
- Capacitor sync OK.
- Gradle debug APK build OK.
- APK delivered to Sven via Telegram.

### v6 Debug APK

APK:

```text
/Datenspeicher/OpenDisruption_v0.1/Benutzer-Ordner/Sven/Projekte/kirobi-avatar/Kirobi-v6-debug.apk
```

SHA256:

```text
a85232975ec9c3c3f217ac10da4882672b859c6984a78fad66acaab683e6f932
```

Added:

- ComfyUI Prompt-Submit in Kreativ tab.
- ComfyUI jobs/gallery endpoint and UI.
- Medusa/Webshop product list in Inventar tab.
- Local 3D print-job list and filament fallback.
- Familien-Hub with persona switch, notes, tasks, expenses.
- Backend routers: `creative`, `commerce`, `family`.

Verified:

- ComfyUI status returns checkpoints.
- Test image generated through ComfyUI using local RTX 3090.
- Medusa `/store/products` reachable.
- Family/task/expense/print-job POST endpoints working.

### v5 Debug APK

APK:

```text
/Datenspeicher/OpenDisruption_v0.1/Benutzer-Ordner/Sven/Projekte/kirobi-avatar/Kirobi-v5-debug.apk
```

SHA256:

```text
66473e90b23df4ec43359db0dcef69da151b7aa3f251fd7a7253eb9bacdf68f0
```

Added:

- Knowledge upload/search UI in Kreativ tab.
- Backend Knowledge API: upload/files/search.
- Local TXT/MD/PDF indexing through Ollama embeddings and Qdrant.

### v4 Debug APK

APK:

```text
/Datenspeicher/OpenDisruption_v0.1/Benutzer-Ordner/Sven/Projekte/kirobi-avatar/Kirobi-v4-debug.apk
```

SHA256:

```text
27682aaac9425556cd7153bf072613e6c5769a5e193687a9765074bf6507f709
```

Added:

- Bottom navigation shell.
- Chat/Kreativ/Inventar/Familie/System tabs.
- System monitor MVP with GPU + service status.
- User-level systemd hardening for Kirobi backend and frontend.

## Operational Fixes

- Fixed `kirobi-backend.service` StartLimitIntervalSec placement from `[Service]` to `[Unit]`.
- Fixed backend restart endpoint to use `systemctl --user`, matching user-level services.
- Corrected Hermes gateway unit ownership: generic `hermes-gateway.service` now points to Sven runtime, while `hermes-gateway-samira.service` remains Samira runtime. Disabled stale failed `hermes-gateway-sven.service` to remove duplicate confusion.

## Known Remaining Work

- Bambu P1S live integration requires printer credentials/IP.
- Medusa admin order/product creation requires admin/auth setup.
- Persona switch and voice/system-prompt wiring into the live Pipecat pipeline are implemented in v8.
- Avatar chunk warning remains a performance optimization item, not a blocker for APK build.

### v9 Debug APK

APK:

```text
/Datenspeicher/OpenDisruption_v0.1/Benutzer-Ordner/Sven/Projekte/kirobi-avatar/Kirobi-v9-debug.apk
```

SHA256:

```text
3393f3e4bdf80ace0652d79d4becd080153b93ea299a95fa8cd86cb4137d7fdb
```

Added:

- Alert-History Backend: `GET /api/alerts` gibt letzte 5 Alerts zurück.
- SystemModule UI: Alert-Liste mit Timestamp und Severity.
- Telegram-Watchdog-Alerts für kritische System-Events.

---

## 2026-05-20 — Kirobi v10.0 Release

### v10 Release-Build

APK:

```text
/Datenspeicher/OpenDisruption_v0.1/Benutzer-Ordner/Sven/Projekte/kirobi-avatar/Kirobi-v10-release.apk
```

SHA256:

```text
30191632eacad466d1f66078447a1ced216f1e9d9f6a21c5feb350ab988a7730
```

GitHub Release: https://github.com/Kirobi92/Frontend/releases/tag/v10.0

### Neue Features in v10:
- Alert-History im SystemModule (letzte 5 Alerts, /api/alerts)
- Alert-Clear per DELETE-Button
- Idle-Limit-Mode (Tag/Nacht) sichtbar
- Watchdog-Alert Telegram-Notifications
- Chat-Modul mit Paperclip-Agenten verbunden
- FamilyModule: Samira+Sineo-Profile
- Wissensgraph: Obsidian-Vault integriert
