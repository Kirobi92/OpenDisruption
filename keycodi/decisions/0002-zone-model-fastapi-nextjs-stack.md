---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-08
reviewed_by: pending
version: 1.0
---

# ADR 0002 — Zone-Modell für FastAPI/Next.js Stack

**Datum:** 2026-05-08
**Status:** proposed
**Phase:** 0
**Issue / PR:** pending
**Sven-Sign-off:** required

---

## Kontext

OpenDisruption nutzt das Fünf-Zonen-Modell `PUBLIC`, `WORKSPACE`, `FAMILY_PRIVATE`, `QUARANTINE` und `SACRED` als harte Sicherheitsgrenze für Inhalte, Agenten, Datenflüsse und externe Kommunikation. Der FastAPI/Next.js Stack muss dieses Modell konsistent abbilden: FastAPI als verbindliche Policy-Schicht, Next.js als transparente Nutzeroberfläche.

Das Dateisystem bleibt der **System of Record**. Postgres und Qdrant sind abgeleitete Indizes und müssen jederzeit aus zonierten Quellen rebuildfähig bleiben. Jede API-Route, jeder Upload, jede Suche, jeder RAG-/Embedding-Flow und jede UI-Aktion muss deshalb einen expliziten Zone-Kontext führen.

Besonders kritisch sind:

- `SACRED` darf niemals über Standard-API-, UI-, Search-, RAG-, Upload- oder Embedding-Flows verarbeitet werden.
- `FAMILY_PRIVATE` und `SACRED` dürfen niemals an Cloud-LLMs, externe APIs, Telegram, Webhooks oder externe Logs gesendet werden.
- `QUARANTINE` bleibt untrusted und darf ohne Human-Review nicht eingebettet, in RAG genutzt oder nach `extracts/`, `canon/` oder niedrigere Zonen promoviert werden.
- Frontends dürfen keine Sicherheitsentscheidung treffen. Sie dürfen Zone, Risiko und Intent anzeigen, aber die finale Entscheidung liegt immer serverseitig.
- Unbekannte Zone, unbekannter Pfad, unbekannter Actor oder fehlender Policy-Kontext bedeutet: **deny / fail-closed**.

---

## Optionen

### Option A — Service-lokale Zone-Policy

Jeder FastAPI-Service pflegt eigene Zone-Enums, Berechtigungsprüfungen, Datenflussregeln und Fehlermeldungen.

- **Pro:** Schnell initial umzusetzen; Services bleiben scheinbar unabhängig.
- **Pro:** Kleine Änderungen können lokal erfolgen.
- **Contra:** Policy-Drift zwischen `auth`, `api`, `retrieval`, `embeddings`, `ingest` und weiteren Services ist wahrscheinlich.
- **Contra:** Sicherheitsänderungen müssen mehrfach synchronisiert werden; Audit und Tests werden unübersichtlich.
- **Risiko:** Hoch — widersprüchliches Verhalten kann Downgrades oder unzulässige Egress-Pfade erzeugen.

### Option B — Zentrale Backend-Policy mit Frontend als UX-Schicht

Eine zentrale Zone-Komponente, z. B. in `kirobi_core.zones`, definiert Zone-Typisierung, Pfadklassifikation, erlaubte Aktionen, Datenflüsse, Egress-Regeln und Fail-Closed-Defaults. FastAPI-Services nutzen diese Policy über Dependencies, Middleware oder Service-Helfer. Next.js zeigt Zonen, Warnungen und erlaubte Aktionen an, bleibt aber reine Intent- und Darstellungsschicht.

- **Pro:** Eine verbindliche Policy-Quelle; weniger Drift und besser testbar.
- **Pro:** Backend-Enforcement schützt auch direkte API-Aufrufe, Agenten, Skripte und interne Service-Calls.
- **Pro:** Frontend kann Nutzer würdevoll führen, ohne Sicherheitsautorität zu werden.
- **Contra:** Die zentrale Policy-Komponente wird sicherheitskritisch und braucht Review.
- **Risiko:** Mittel — fehlende Zone-Metadaten blockieren legitime Aktionen, bis sie korrekt klassifiziert sind.

### Option C — Geteiltes Enforcement in Frontend und Backend

Next.js blockiert Aktionen frühzeitig; FastAPI prüft zusätzlich serverseitig. Beide Schichten enthalten eigene Policy-Logik.

- **Pro:** Sehr gute Nutzerführung; weniger unnötige API-Requests.
- **Contra:** Doppelte Logik läuft auseinander, wenn Regeln nicht strikt generiert oder zentral verteilt werden.
- **Contra:** Entwickler könnten Frontend-Regeln fälschlich als sicherheitsverbindlich behandeln.
- **Risiko:** Mittel bis hoch — UX-Checks können Policy-Checks maskieren.

### Option D — Frontend-zentriertes Zone-Enforcement

Next.js entscheidet primär, welche Aktionen erlaubt sind; FastAPI vertraut auf UI-Kontext und Client-Parameter wie `zone`.

- **Pro:** Schnellste UX-Iteration.
- **Contra:** Browser-Logik ist umgehbar; APIs können direkt angesprochen werden.
- **Contra:** Kein belastbarer Schutz für Agenten, Skripte, RAG, Embeddings oder interne Service-Kommunikation.
- **Risiko:** Kritisch — Sicherheitsgrenze läge im Client.

---

## Entscheidung

**Wir wählen Option B — zentrale Backend-Policy mit Frontend als erklärender UX-Schicht.**

FastAPI ist die verbindliche Sicherheitsinstanz, weil nur der Server zuverlässig alle Zugriffe, Uploads, Suchanfragen, RAG-Kontexte, Embeddings und Egress-Pfade kontrollieren kann. Next.js darf Zonen sichtbar machen, Nutzer vor riskanten Aktionen warnen und Intent übertragen, aber keine finale Autorisierung übernehmen. Dadurch bleibt das Zone-Modell testbar, auditierbar und unabhängig von Client-Verhalten.

Die zentrale Policy folgt vier nicht verhandelbaren Regeln:

1. **Fail-Closed:** Fehlende oder unbekannte Zone, unbekannter Pfad, unbekannter Actor, unbekannter Target-Typ oder Policy-Fehler führen zu `403` und Audit-Event.
2. **No Downgrade:** Daten dürfen niemals stillschweigend in niedrigere Zonen fließen. Die effektive Output-Zone ist mindestens so restriktiv wie die höchste Input-Zone.
3. **No Sensitive Egress:** `FAMILY_PRIVATE` und `SACRED` verlassen niemals das lokale System; `WORKSPACE`-Egress benötigt explizite Bestätigung; `PUBLIC`-Egress bleibt auditierbar.
4. **SACRED Sonderfall:** `SACRED` ist kein normaler API-Fall. Admin-Rolle bedeutet nicht SACRED-Zugriff. Standard-Flows lehnen `SACRED` ab; Ausnahmen erfordern explizite, zeitlich begrenzte Sven-Freigabe und Audit-Grund.

---

## Policy-Schnittstellen

### Zentrale Typisierung

```python
class Zone(str, Enum):
    PUBLIC = "PUBLIC"
    WORKSPACE = "WORKSPACE"
    FAMILY_PRIVATE = "FAMILY_PRIVATE"
    QUARANTINE = "QUARANTINE"
    SACRED = "SACRED"
```

Jedes Datenobjekt, jeder Job und jede sicherheitsrelevante API-Aktion führt mindestens:

```json
{
  "resource_id": "string",
  "path": "string | null",
  "zone": "WORKSPACE",
  "action": "read|write|delete|embed|export|egress|promote|search|rag",
  "actor_id": "string",
  "actor_type": "user|agent|service",
  "target": "local|postgres|qdrant|ollama|cloud|telegram|webhook"
}
```

### FastAPI-Enforcement

Services nutzen gemeinsame Dependencies oder Service-Helfer, z. B.:

- `require_zone_read(actor, zone, resource)`
- `require_zone_write(actor, zone, resource)`
- `require_zone_export(actor, zone, target)`
- `require_embedding_allowed(actor, zone, target)`
- `require_rag_allowed(actor, zone, collections)`
- `require_egress_allowed(actor, zone, target)`
- `audit_zone_decision(actor, action, zone, result, reason)`

`auth` bleibt Quelle für Identität, Rollen, Agent-/User-Kontext und Zone-Permissions. Alle fachlichen Services prüfen trotzdem serverseitig; sie vertrauen nicht blind auf Client-Parameter.

### Fehlerkonvention

Policy-Fehler sind ruhig, eindeutig und ohne sensible Details:

```json
{
  "error": "zone_policy_denied",
  "message": "Diese Aktion ist für die angefragte Zone nicht erlaubt.",
  "request_id": "uuid",
  "audit_event_id": "uuid"
}
```

Fehlermeldungen enthalten keine Secrets, keine vollständigen Prompts, keine sensiblen Pfade und keine FAMILY_PRIVATE-/SACRED-Inhalte.

---

## Service-Regeln

### `services/auth`

- User- und Permission-Management ist default-deny und admin-only.
- Zone-Permissions werden explizit vergeben; `SACRED` wird nicht automatisch durch Admin-Rollen freigeschaltet.
- Login, Permission-Änderungen, Denials und SACRED-Zugriffsversuche werden auditiert.

### `services/api`

- Conversations und Uploads tragen eine serverseitig validierte Zone.
- Chat-RAG nutzt höchstens die Zone der Conversation und nur Zonen, für die der Actor Leserechte hat.
- RAG-Ergebnisse gelten als untrusted data und dürfen nicht als System-Instruktionen behandelt werden.
- Uploads brauchen serverseitige Validierung: erlaubte Zone, Größenlimit, MIME-/Typprüfung, Pfad-Traversal-Schutz und Quarantäne-Strategie.
- Keine stille Hoch- oder Runterstufung von Conversation-, Upload- oder Message-Zonen.

### `services/retrieval`

- `/search` und `/rag` vertrauen nicht allein dem vom Client gesetzten `zone`-Parameter.
- `ALL` bedeutet nur: alle für den Actor erlaubten Zonen, niemals pauschal alle Collections.
- Keine Cross-Zone-Suche in höherklassifizierte Collections.
- `SACRED` bleibt hart geschlossen und liefert immer `403`; es gibt keinen Config-Override.

### `services/embeddings`

- Qdrant-Collections bleiben strikt pro Zone getrennt.
- `QUARANTINE` darf nicht eingebettet werden, bis ein Human-Review erfolgt ist.
- `FAMILY_PRIVATE` wird nur lokal eingebettet.
- `SACRED` läuft nicht über normale `/store`-Flows; verschlüsselte lokale Sonderpfade brauchen explizite Sven-Freigabe.
- Cloud-Embedding ist nur für `PUBLIC` erlaubt und für `WORKSPACE` nur mit expliziter Bestätigung; nie für `FAMILY_PRIVATE`, `QUARANTINE` oder `SACRED`.

### `services/ingest`

- Unbekannte oder externe Uploads starten in `QUARANTINE` oder brauchen eine explizite, serverseitig geprüfte Zielzone.
- Promotion nach `extracts/`, `canon/`, Postgres oder Qdrant erfordert Review-Status und Audit-Event.
- Inhalte aus `sources/`, `imports/`, `web-research/` und RAG bleiben untrusted und dürfen nie als Instruktionen ausgeführt werden.

### `apps/web`, `apps/dashboard`, `apps/voice`

- Next.js zeigt Zone-Badges, Warnungen, deaktivierte Aktionen und Bestätigungsdialoge.
- Clientseitige Zone-Optionen sind UX, keine Policy.
- Frontends behandeln `403`/Policy-Fehler würdevoll und erklären, welche Schutzregel gegriffen hat.
- Browser-Code sendet keine FAMILY_PRIVATE- oder SACRED-Daten an externe Dienste.

---

## Konsequenzen

### Code-Auswirkungen

- `kirobi_core` wird zur kanonischen Heimat für Zone-Typen, Policy-Helfer und Pfadklassifikation.
- FastAPI-Routen müssen Zone-Checks serverseitig erzwingen, besonders Upload, Chat, Search, RAG, Embedding und Export.
- Next.js-Komponenten dürfen Zonenhinweise anzeigen, aber keine Policy-Quelle sein.
- Bestehende service-lokale Zone-Sets werden langfristig durch zentrale Typen ersetzt.

### Test-Auswirkungen

- Unit-Tests prüfen jede Kombination aus Zone, Aktion und Target für allow/deny.
- API-Tests prüfen Downgrade-Verbot, `SACRED`-Blockaden, QUARANTINE-Verbot für Embeddings/RAG und Approval-Pfade.
- Retrieval-Tests müssen sicherstellen, dass `PUBLIC` keine WORKSPACE-/FAMILY_PRIVATE-Collections durchsucht.
- Frontend-Tests prüfen Darstellung und Nutzerführung, nicht Sicherheitsgarantie.

### Doku-Auswirkungen

- API-Dokumentation muss Zone-Verhalten pro Schnittstelle benennen.
- Runbooks müssen erklären, wie Denials, QUARANTINE-Review und Sven-Freigaben auditiert werden.
- `.env.example`-Kommentare müssen externe API-Nutzung und Zone-Grenzen erklären, wenn Egress-Schalter ergänzt werden.

### Roadmap-Auswirkungen

- Zone-Enforcement bleibt Foundation-Arbeit und blockiert Features, die private, untrusted oder externe Datenflüsse verarbeiten.
- Jede neue App oder Service-Route muss ihren Zone-Kontext im Design benennen, bevor Code geschrieben wird.

### Sicherheits-Auswirkungen

- Die Angriffsfläche sinkt, weil Client-Parameter nicht als Autorität gelten.
- Audit-Logging erzeugt zusätzliche Betriebsdaten, die selbst geschützt werden müssen.
- Fail-Closed kann legitime Aktionen blockieren, wenn Metadaten fehlen — das ist akzeptiert und wird durch bessere Klassifikation gelöst, nicht durch permissive Defaults.

---

## Verworfene Optionen — kurz begründet

- **Option A:** Verworfen wegen Policy-Drift und widersprüchlicher Entscheidungen zwischen Services.
- **Option C:** Nur als UX-Ergänzung akzeptiert; als Architekturentscheidung zu fehleranfällig.
- **Option D:** Verworfen, weil Client-seitiges Enforcement keine echte Sicherheitsgrenze darstellt.
- **Default auf `WORKSPACE`:** Verworfen. Unbekanntes muss konservativ behandelt werden: deny bzw. wie `SACRED`.
- **SACRED in Retrieval mit Sonderfreigabe:** Verworfen. Retrieval bleibt für `SACRED` hart geschlossen (`403`).

---

## Referenzen

- `CLAUDE.md` §2, §3, §4, §7 — Zonen, Verbote, Pflichtverhalten, Prompt-Injection-Schutz
- `AGENTS.md` — Service-Graph, Ports, Style-Konventionen
- `metadata/ZONE-POLICY-MATRIX.md`
- `metadata/SECURITY-CLASSIFICATION.md`
- `kirobi-core/core-policies.md`
- `ARCHITECTURE.md` — ADR-002 Five-Zone Security Model
- `keycodi/decisions/0000-adr-template.md`
- `keycodi/decisions/0001-phase4-kidi-keybrodi-implementation-plan.md`
- `services/auth/`
- `services/api/`
- `services/retrieval/`
- `services/embeddings/`
- `services/ingest/`
- `apps/web/`
- `apps/dashboard/`
- `apps/voice/`
