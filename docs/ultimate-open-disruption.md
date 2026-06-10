# OpenDisruption Ultimate

OpenDisruption Ultimate ist die konsolidierte Zielversion des bestehenden
OpenDisruption-Monorepos: KIROBI fuer private Familien-KI, LUKI fuer Business-
und ERP-KI, gemeinsame lokale Infrastruktur, Labs fuer Experimente, Archive fuer
eingefrorene Altlasten und ein Agent-OS-Layer fuer planbare Umsetzung.

## Feature Planes

| Plane | Features | Harte Grenze |
|---|---|---|
| Family AI | KIROBI PWA, Telegram-Gateways, Family Canon, FAMILY_PRIVATE, FAMILY_SHARED | FAMILY_PRIVATE niemals Cloud, niemals LUKI |
| Business AI | LUKI Knowledge MVP, Source-Docs, Retrieval mit Quellenpflicht, Audit, Eval, Nutzeisen/eNVenta-Profil | Keine privaten Familienkontexte |
| Shared Infra | Caddy, Qdrant, Ollama, Postgres, Monitoring, Restic, Tailscale | Nur Caddy als HTTP-Entry |
| Agent OS | LazyCodex/OmO, Graphify, Hermes Runtime, Plan-to-work-Loops, Doctor | Agenten ersetzen keine Policy-Gates |
| Labs | 3D-Druck, ComfyUI, Open WebUI, Flowise, Hindsight, Mission Control, Webshop | Labs sind opt-in und duerfen keine Dauerlaeufer ohne Compose sein |
| Security | Secret-Quarantaene, Restore-Tests, Runtime-Daten ausserhalb Repo, Pre-Commit-Scans | Keine echten Secrets im Repo |
| Archive | Audits, alte Snapshots, qdrant-legacy, home-migration-tree | Nur read-only Referenz |

## Ausfuehrbare Control Plane

```bash
python3 tools/opendisruption_ultimate.py status --json
python3 tools/opendisruption_ultimate.py blueprint
```

`status --json` ist die maschinenlesbare Oberflaeche fuer Doctor, Graphify und
LazyCodex/OmO-Agenten. `blueprint` ist die kompakte menschliche Sicht.

## Definition von Ultimate

OpenDisruption ist erst Ultimate, wenn alle folgenden Bedingungen gleichzeitig
gelten:

1. Alle Domaenenordner existieren und haben eine klare README- oder Canon-Spur.
2. Runtime-Daten liegen ausschliesslich unter `/Datenspeicher/OpenDisruption-Data`.
3. Graphify kennt den Projektgraphen und wird nach Codeaenderungen aktualisiert.
4. LazyCodex/OmO ist als Harness verfuegbar, aber nur fuer Plan, Umsetzung und QA.
5. KIROBI- und LUKI-Kontexte bleiben technisch und dokumentarisch getrennt.
6. Jede produktive Aenderung folgt Backup, Change, Verification, Rollback-Punkt.
7. Fehlende Features erscheinen als `planned` oder `missing`, nicht als Wunschtext.

## Naechste Implementierungswellen

1. `tools/opendisruption_ultimate.py status --json` in `tools/doctor/`
   integrieren.
2. `packages/policy-gate` als echte Python/TypeScript-Library aufbauen.
3. LUKI Knowledge MVP aus `LUKI Operator Orchestrator` in `products/luki`
   produktfaehig spiegeln.
4. KIROBI PWA/Gateway-Wahrheit festlegen und doppelte historische Trees
   archivieren.
5. Shared-Infra Compose-Dateien fuer Caddy, Qdrant, Ollama, Postgres und
   Monitoring mit Healthchecks fuellen.
6. Labs als einzeln startbare, dokumentierte Compose-Stacks definieren.
