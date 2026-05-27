# 03 — Domain Boundary Model

**Datum:** 2026-05-26 · Klassifikation jeder relevanten Komponente in genau eine Ziel-Domäne + Empfehlung.

**Domänen:** `OPENDISRUPTION_ROOT` · `KIROBI_FAMILY` · `LUKI_BUSINESS` · `SHARED_INFRA` · `LABS` · `ARCHIVE` · `DELETE_LATER`
**Empfehlungen:** `KEEP` · `FIX` · `EXTRACT_TO_LUKI` · `KEEP_IN_KIROBI` · `MOVE_TO_SHARED_INFRA` · `MOVE_TO_LABS` · `FREEZE` · `ARCHIVE` · `DELETE_LATER` · `REBUILD_SMALLER` · `SECURITY_REVIEW_REQUIRED` · `UNKNOWN_NEEDS_MANUAL_CHECK`

## A) Komponenten-Zuordnung

| Komponente | Aktuelle Domäne | Ziel-Domäne | Begründung | Risiko bei Vermischung | Empfehlung | Evidenz |
|---|---|---|---|---|---|---|
| Caddy | gemischt | SHARED_INFRA | einziger HTTP-Entry | LAN-Exposition wenn ungetrennt | MOVE_TO_SHARED_INFRA + SECURITY_REVIEW_REQUIRED | `services/caddy/` |
| Hermes-Agent (Source) | gemischt | SHARED_INFRA | Agent-Laufzeit für mehrere Produkte | – | MOVE_TO_SHARED_INFRA + REBUILD_SMALLER (Runtime auslagern) | `hermes-agent/` |
| Hermes Gateway Sven/Samira (systemd) | KIROBI | KIROBI_FAMILY | private Telegram-Bots | Botleak in Business-Stack | KEEP_IN_KIROBI | systemd units |
| Kirobi-PWA | KIROBI | KIROBI_FAMILY | Family-Portal | – | KEEP_IN_KIROBI + FIX (HOST 127.0.0.1) | `kirobi-pwa/` |
| Qdrant (Systembetrieb) | SHARED | SHARED_INFRA | Vektor-DB für KIROBI+LUKI separate Collections | Datenleck zwischen Familie/Geschäft | MOVE_TO_SHARED_INFRA + FIX (zwei Collections strikt getrennt) | `Systembetrieb-und-Indizes/qdrant/` |
| Qdrant LEGACY (10 GB) | SHARED | ARCHIVE | Duplikat ohne Compose | Inkonsistenz | ARCHIVE (nach Inhaltsverifikation) | `services/qdrant/` |
| Ollama (host) | SHARED | SHARED_INFRA | LLM-Server | – | MOVE_TO_SHARED_INFRA + FIX (Compose+systemd) | host |
| Open WebUI | LABS | LABS | Spielwiese | priv. Konvers. in Geschäftslog | MOVE_TO_LABS + REBUILD_SMALLER (Compose nachziehen) oder FREEZE | `services/open-webui/` (6.9 GB) |
| Flowise | LABS | LABS | Flow-Builder | – | MOVE_TO_LABS oder FREEZE | `services/flowise/` |
| Hindsight | LABS | LABS | Session-Archiv-Suche | priv. Sessions geleakt | MOVE_TO_LABS + SECURITY_REVIEW_REQUIRED oder FREEZE | `services/hindsight/` |
| Mission Control | LABS | LABS | Ops-Dashboard | Admin-Routen offen | MOVE_TO_LABS + SECURITY_REVIEW_REQUIRED | `services/mission-control/` |
| ComfyUI | LABS | LABS | Bildgenerierung | Modelle/Outputs im Home-Tree | MOVE_TO_LABS + REBUILD_SMALLER | `Benutzer-Ordner/Sven/local-ai/ComfyUI` |
| Homebox | LABS | LABS | Haushalts-Inventar | Privat-Inventar | MOVE_TO_LABS oder KEEP_IN_KIROBI (privat) | `services/inventory/homebox/` |
| Part-DB | LABS | LABS | Elektronik-Bauteile | – | MOVE_TO_LABS + FIX (Default-Admin-PW) | `services/inventory/partdb/` |
| InvenTree | gemischt | LUKI_BUSINESS oder LABS | aktuell für 3D-Druck-Bar genutzt | Geschäftsdaten in Privatkontext | EXTRACT_TO_LUKI **oder** MOVE_TO_LABS (Entscheidung Nutzer: gehört Nutzeisen/eNVenta dazu?) | externer Docker |
| Webshop (WordPress+MySQL) | LABS | LABS | 3D-Druck-Bar-Shop | DB-Übernahme | MOVE_TO_LABS + SECURITY_REVIEW_REQUIRED + FIX (Secrets, Volumes) | `services/webshop/`, `data/webshop-*` |
| 3D-Druck-Bar-Website | LABS | LABS | Status-Seite | – | MOVE_TO_LABS | `services/3d-druck-bar-website/` |
| 3D-Druck-Pipeline | LABS | LABS | Druck-Orchestrierung | Secrets im .env | MOVE_TO_LABS + SECURITY_REVIEW_REQUIRED | `services/3d-druck-pipeline/` |
| IONOS Integration | LABS | LABS | Hosting-API | – | MOVE_TO_LABS oder FREEZE | `services/ionos-integration/` |
| Status Reporter | SHARED | SHARED_INFRA | Health | – | MOVE_TO_SHARED_INFRA oder UNKNOWN_NEEDS_MANUAL_CHECK | `services/status-reporter/` |
| Static Website | LABS | LABS | Landing | – | MOVE_TO_LABS oder ARCHIVE | `services/website/` |
| `Benutzer-Ordner/Sven/` (Privates) | gemischt | KIROBI_FAMILY | privater Bereich | viele Geschäftsfragmente | KEEP_IN_KIROBI + FIX (Extraktion: hermes-runtime, local-ai, agent → SHARED) | dir |
| `Benutzer-Ordner/Sven/hermes-runtime/` | KIROBI | SHARED_INFRA | Agent-Runtime im Privatordner | – | MOVE_TO_SHARED_INFRA | dir |
| `Benutzer-Ordner/Sven/local-ai/` (ComfyUI .venv etc.) | KIROBI | LABS | Modelle/venv | – | MOVE_TO_LABS + REBUILD_SMALLER | dir |
| `Benutzer-Ordner/Sven/Projekte/` | gemischt | gemischt | Mischmasch (kirobi-pwa, kirobi-avatar, Inventar-System, Scripts) | hoch | siehe Spezialfälle unten | dir |
| `Benutzer-Ordner/Samira/` | KIROBI | KIROBI_FAMILY | rein privat | sofortige Trennung notwendig | KEEP_IN_KIROBI | dir |
| `Benutzer-Ordner/Sineo/` | KIROBI | KIROBI_FAMILY | Kind, Schutzbedarf | hoch | KEEP_IN_KIROBI + SECURITY_REVIEW_REQUIRED (Zonenpolitik) | dir |
| `Benutzer-Ordner/LUKI/` | KIROBI (falsch platziert) | LUKI_BUSINESS | LUKI-Agent-Profile | – | EXTRACT_TO_LUKI | dir |
| `Benutzer-Ordner/Shared/` | KIROBI | KIROBI_FAMILY | Familien-Shared | – | KEEP_IN_KIROBI | dir |
| `Benutzer-Ordner/_Muster-Benutzerstruktur/` | KIROBI | OPENDISRUPTION_ROOT | Vorlage | – | KEEP (in `tools/templates/`) | dir |
| `Geteilte-Wissensbasis/01-Canon-und-Richtlinien/` | gemischt | OPENDISRUPTION_ROOT | Standards für beide Produkte | – | KEEP (in `docs/canon/`) | dir |
| `Geteilte-Wissensbasis/03-Familie-und-Beziehungen/` | gemischt | KIROBI_FAMILY | privat | LUKI-Mitlesen | EXTRACT (zu KIROBI) | dir |
| `Geteilte-Wissensbasis/04-Business-und-Kunden/` | gemischt | LUKI_BUSINESS | Geschäft | – | EXTRACT_TO_LUKI | dir |
| `Geteilte-Wissensbasis/06-Bewusstsein-und-Sinnmodelle/` | gemischt | OPENDISRUPTION_ROOT | Philosophie/Canon | – | KEEP (in `docs/canon/`) | dir |
| `Orchestrierung-und-Agenten/01-Hermes/` | KIROBI | SHARED_INFRA | Skills/Configs für Hermes | – | MOVE_TO_SHARED_INFRA (Skills) + KEEP_IN_KIROBI (private Skills) — split nötig | dir |
| `Orchestrierung-und-Agenten/03-Agent-Profile-und-Policies/` | gemischt | SHARED_INFRA | Allowlists/Policies | – | MOVE_TO_SHARED_INFRA + SECURITY_REVIEW_REQUIRED | dir |
| `Orchestrierung-und-Agenten/05-Audit-und-Beobachtung/` | gemischt | SHARED_INFRA | Audit-Logs | Secret-Leak möglich | MOVE_TO_SHARED_INFRA + SECURITY_REVIEW_REQUIRED (Inhaltsprüfung) | dir |
| `Integrationen-und-Importe/` | gemischt | SHARED_INFRA | Import-Mappings | – | KEEP (in `tools/integrations/`) | dir |
| `Systemkonfiguration/01-Umgebungen-und-Secrets-Hinweise/` | gemischt | SHARED_INFRA | Secrets-Doku | hoch | SECURITY_REVIEW_REQUIRED + MOVE_TO_SHARED_INFRA | dir |
| `Systemkonfiguration/02-Compose-Caddy-und-Routing/` | gemischt | SHARED_INFRA | Infra-Modell | – | MOVE_TO_SHARED_INFRA | dir |
| `Systemkonfiguration/04-Zonen-und-Sicherheitsregeln/` | gemischt | OPENDISRUPTION_ROOT | Policy-Doku | – | KEEP (in `docs/security/`) | dir |
| `Systemkonfiguration/05-Schemas-Mappings/` | gemischt | SHARED_INFRA | Schemas | – | MOVE_TO_SHARED_INFRA | dir |
| `Unternehmensstruktur/` | gemischt | LUKI_BUSINESS (+LABS für 3d-druck/lebenscoach) | Org-/Abteilungs-Wissen | – | EXTRACT_TO_LUKI (Hardware-/Software-Entwicklung/Web3) + MOVE_TO_LABS (3d-druck, lebenscoach) | dir |
| `Nutzeisen Prozessanalyse/` | LUKI-Material | LUKI_BUSINESS | LUKI-Knowledge-Quellen | – | EXTRACT_TO_LUKI (`products/luki/source-docs/`) | dir |
| `Backups-und-Exporte/` | gemischt | ARCHIVE | alte Reports | Secret-Leak | ARCHIVE + SECURITY_REVIEW_REQUIRED | dir |
| `Systembetrieb-und-Indizes/` (außer qdrant) | INFRA/Runtime | DELETE_LATER (in Runtime-Tree migrieren) | gehört nicht ins Repo | – | MOVE_TO_SHARED_INFRA (Runtime in `/Datenspeicher/OpenDisruption-Data/shared/indices/`) | dir |
| `data/webshop-mysql/`, `data/webshop-wordpress/` | INFRA/Runtime | DELETE_LATER (nach Volume-Migration) | Live-DB im Repo | CRITICAL | SECURITY_REVIEW_REQUIRED + MOVE_TO_SHARED_INFRA | dir |
| `node_modules/` (Root) | – | DELETE_LATER | Build-Artefakt | – | DELETE_LATER | dir |
| `.opencode/`, `.hermes/`, `.omo/` | – | DELETE_LATER (Tool-Caches, leben in $HOME) | Bloat | – | DELETE_LATER | dir |
| `.backup.env` | – | DELETE_LATER (nach Rotation in Secrets-Tree) | Secret | CRITICAL | SECURITY_REVIEW_REQUIRED | file |
| `geplante_ERP-eNVenta-verwendung_Nutzeisen.pdf` (Root) | – | DELETE_LATER (Duplikat) | – | – | DELETE_LATER | file |
| `opendisruption-data-dash.html` | – | ARCHIVE oder LABS | Standalone HTML | – | ARCHIVE | file |
| `package.json`, `package-lock.json`, `capacitor.config.json` (Root) | – | ARCHIVE | Capacitor-Reste | – | ARCHIVE (gehören zum kirobi-avatar/-pwa, dort konsolidieren) | file |
| `sammy_story.py`, `override.txt`, `requirements.compiled` (Root) | – | ARCHIVE oder DELETE_LATER | unklare Reste | – | UNKNOWN_NEEDS_MANUAL_CHECK | file |
| Root-MDs (`README`, `SYSTEM_MAP`, `AGENTS`, `MASTERPLAN`, `KIROBI_OS_AUDIT`, `AGENT-ACTIVITY-LOG`) | – | OPENDISRUPTION_ROOT (`docs/`) | Doku/Audits | Secret-Leak | KEEP (Doku) + SECURITY_REVIEW_REQUIRED (Audits mit Klartext-Secrets) | files |
| `/Datenspeicher/home-migration/OpenDisruption/` (Parallel-Tree) | – | ARCHIVE | Migrationsartefakt | Drift | ARCHIVE (nach Inhalts-Diff) | dir |
| `/Datenspeicher/OpenDisruption_Datenstruktur/` (Parallel-Datenwurzel) | – | UNKNOWN_NEEDS_MANUAL_CHECK | spiegelt Ordnernamen aus v0.1 | Drift | UNKNOWN_NEEDS_MANUAL_CHECK | dir |
| `/Datenspeicher/OpenDisruption_KI_Modelle/` | – | SHARED_INFRA (Modell-Store) | Ollama-/LLM-Modelle | – | MOVE_TO_SHARED_INFRA (außerhalb Repo, gehört zu Runtime) | dir |
| `Benutzer-Ordner/Sven/Projekte/kirobi-pwa` | KIROBI | KIROBI_FAMILY | Master-Repo der PWA — Konflikt mit Top-Level `kirobi-pwa/`! | Drift | UNKNOWN_NEEDS_MANUAL_CHECK (welche Version ist Wahrheit?) | AGENTS.md |
| `Benutzer-Ordner/Sven/Projekte/kirobi-avatar` | KIROBI | KIROBI_FAMILY oder LABS | Avatar (FastAPI/React/Android) | – | KEEP_IN_KIROBI (Family-Avatar) oder MOVE_TO_LABS | AGENTS.md |
| `Benutzer-Ordner/Sven/Projekte/Inventar-System/` | gemischt | LABS (3D-Druck) **oder** EXTRACT_TO_LUKI | enthält InvenTree/WC Sync-Skripte | hoch (Secrets) | UNKNOWN_NEEDS_MANUAL_CHECK + SECURITY_REVIEW_REQUIRED | AGENT-ACTIVITY-LOG |

## B) Vermischungs-Hotspots (mit konkreter Aktion)

1. `Benutzer-Ordner/LUKI/` liegt im Family-Ordner → EXTRACT_TO_LUKI nach `products/luki/runtime/agent-profile/`.
2. `Benutzer-Ordner/Sven/hermes-runtime/` ist Shared-Infrastruktur in Privat-Tree → MOVE_TO_SHARED_INFRA nach `infra/hermes-runtime/`.
3. `Benutzer-Ordner/Sven/local-ai/ComfyUI/` (mit `.venv`) → MOVE_TO_LABS nach `labs/comfyui/` mit Volume außerhalb Repo.
4. `Geteilte-Wissensbasis/04-Business-und-Kunden/` → EXTRACT_TO_LUKI; `03-Familie-und-Beziehungen/` → KEEP_IN_KIROBI.
5. Top-Level `kirobi-pwa/` vs. `Benutzer-Ordner/Sven/Projekte/kirobi-pwa/` — **eine Quelle der Wahrheit nötig**; nach Phase-A-Diff entscheidet Nutzer.
6. `Nutzeisen Prozessanalyse/` ist LUKI-Quellmaterial — gehört nach `products/luki/source-docs/`.
7. `Unternehmensstruktur/` enthält Mix aus LUKI-relevanten Abteilungen (Hardware/Software/Web3) und Labs-Themen (3d-druck, lebenscoach) — split nötig.
8. `Orchestrierung-und-Agenten/05-Audit-und-Beobachtung/` muss geprüft werden, ob sie Klartext-Secrets enthalten (wie AGENT-ACTIVITY-LOG).
9. `services/qdrant/` (10 GB) vs. `Systembetrieb-und-Indizes/qdrant/` — konsolidieren auf einen Pfad mit getrennten Collections für `kirobi_*` und `luki_*`.
10. `data/webshop-*` ist Live-DB im Repo — gehört in Volume-Tree.

## C) Offene Entscheidungspunkte (Nutzer)

- **D1:** Soll InvenTree zu LUKI_BUSINESS gehören (ERP-Wissensbasis) oder bei LABS bleiben (nur 3D-Druck-Bar)?
- **D2:** Sollen `Webshop`/`3d-druck-*` als kommerzielles Nebenprojekt im Repo bleiben (LABS) oder in ein separates Repo ausgelagert werden?
- **D3:** `kirobi-avatar` (FastAPI/React/Android) — KIROBI-Family oder eigenständiges Lab?
- **D4:** Wer ist Owner der `Unternehmensstruktur/`-Bereiche „lebenscoach", „web3" (LABS oder LUKI)?
- **D5:** Welche Version von `kirobi-pwa` ist Wahrheit (Top-Level oder `Benutzer-Ordner/Sven/Projekte/`)?
