# Beitragen zu Kirobi / Disruptive OS

Danke für dein Interesse, zum Projekt beizutragen! Diese Richtlinien gelten für menschliche Beitragende **und** für KI-Agenten.

---

## Für menschliche Beitragende

### Vor dem ersten Commit

1. Lies die [PROJECT-CHARTER.md](PROJECT-CHARTER.md) um die Vision zu verstehen
2. Verstehe das [Zonen-System](metadata/SECURITY-CLASSIFICATION.md)
3. Mache dich mit der [Verzeichnisstruktur](metadata/FOLDERMANIFEST.md) vertraut
4. Prüfe die [offenen Issues](https://github.com/Kirobi92/OpenDisruption/issues)

### Workflow

```bash
# 1. Repo forken und klonen
git clone https://github.com/DEIN-USERNAME/OpenDisruption.git
cd OpenDisruption

# 2. Feature-Branch erstellen
git checkout -b feature/beschreibung-deines-features

# 3. Änderungen machen (in deutscher Sprache, außer technische Terms)

# 4. Commit erstellen
git add .
git commit -m "typ: kurze beschreibung"

# 5. Push und Pull Request
git push origin feature/beschreibung-deines-features
```

### Commit-Konventionen

Wir folgen [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: neue Funktion hinzugefügt
fix: Fehler behoben
docs: Dokumentation aktualisiert
chore: Wartungsaufgaben
refactor: Code-Refactoring
test: Tests hinzugefügt oder angepasst
infra: Infrastruktur-Änderungen
agent: Agent-Konfiguration oder -Prompts
```

### Was kann beigetragen werden?

**Willkommen:**
- Verbesserungen an PUBLIC und WORKSPACE Zone
- Neue Integrationen und Connectors
- Infrastruktur-Verbesserungen
- Dokumentationsverbesserungen
- Tests und Validierungen
- Bug Reports und Feature Requests

**Nicht akzeptiert:**
- Änderungen an SACRED oder FAMILY_PRIVATE Inhalten
- Inhalte mit persönlichen Daten Dritter
- Proprietäre oder lizenzrechtlich problematische Inhalte
- Backdoors, Telemetry oder Privacy-Verletzungen

### Code-Qualitäts-Standards

- **Sprache:** Kommentare und Dokumentation auf Deutsch
- **Sprache:** Technische Terms und Code auf Englisch
- **Markdown:** Konsistente Formatierung (Überschriften, Tabellen, Code-Blöcke)
- **Shell-Skripte:** `set -euo pipefail` an Anfang, kommentiert
- **YAML:** Validiert mit `docker-compose config` bzw. YAML-Linter
- **Keine Secrets:** Niemals echte Passwörter oder API-Keys committen

---

## Für KI-Agenten (Agent Guidelines)

### Agenten-Beitrags-Protokoll

Kirobi-Agenten können autonom Inhalte erstellen und modifizieren, aber müssen dabei folgende Regeln einhalten:

#### Zonen-Compliance
- Agenten dürfen nur in ihren autorisierten Zonen schreiben
- Keine Aktion in SACRED ohne explizite menschliche Freigabe
- Jede Aktion in FAMILY_PRIVATE erfordert Logging

#### Metadaten-Pflicht
Jedes von einem Agenten erstellte Dokument muss folgende Frontmatter enthalten:

```yaml
---
created_by: [agent-name]
created_at: [ISO-8601-Timestamp]
zone: [PUBLIC|WORKSPACE|FAMILY_PRIVATE|QUARANTINE|SACRED]
reviewed_by: [human-name oder "pending"]
version: [semantic version]
---
```

#### Verbotene Aktionen für Agenten
- Keine Änderungen an `PROJECT-CHARTER.md` ohne Human-Review
- Keine Modifikation der Agenten-Registry ohne Bestätigung
- Kein Löschen von Inhalten in `canon/` ohne explizite Freigabe
- Keine Ausführung von Shell-Befehlen außerhalb des `infra/`-Scopes

#### Qualitäts-Anforderungen für Agenten-Outputs
- Alle Ausgaben müssen mit dem aktuellen Kontext aus Qdrant abgeglichen sein
- Halluzinationen sind als `[UNSICHER - review needed]` zu markieren
- Externe Quellen müssen als Referenzen angegeben werden
- Konflikte mit bestehenden Canon-Dokumenten müssen gemeldet werden

---

## Pull Request Prozess

1. **Beschreibung:** Erkläre was, warum und wie
2. **Zone-Angabe:** Gib an, welche Sicherheitszonen betroffen sind
3. **Tests:** Beschreibe wie die Änderungen getestet wurden
4. **Screenshots/Logs:** Bei UI/Config-Änderungen Screenshots beifügen

### PR-Template

```markdown
## Was wurde geändert?
[Beschreibung]

## Warum wurde es geändert?
[Begründung]

## Welche Zonen sind betroffen?
- [ ] PUBLIC
- [ ] WORKSPACE
- [ ] FAMILY_PRIVATE (erfordert Sven's Review)
- [ ] SACRED (nicht via PR)

## Wie wurde getestet?
[Testbeschreibung]
```

---

## Fragen & Diskussion

- **Issues:** Für Bugs und Feature Requests
- **Discussions:** Für konzeptionelle Fragen
- **Direktkontakt:** Bei SACRED/FAMILY_PRIVATE-Themen ausschließlich direkt

---

*Danke für deinen Beitrag! Jeder Commit macht das System besser.* 🚀
