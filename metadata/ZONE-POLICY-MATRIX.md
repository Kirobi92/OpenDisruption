# Zonen-Policy-Matrix: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE (Diese Datei selbst) | **Sensitivität:** Hoch

---

## Zonen-Übersicht

| Zone | Symbol | Farbe | Vertrauensstufe | Beschreibung |
|------|--------|-------|----------------|-------------|
| `PUBLIC` | 🌍 | Grün | 1 (niedrigste) | Öffentlich teilbar |
| `WORKSPACE` | 💼 | Blau | 2 | Arbeits-Kontext |
| `FAMILY_PRIVATE` | 👨‍👩‍👦 | Gelb | 3 | Familiäre Inhalte |
| `QUARANTINE` | ⚠️ | Orange | 4 | Unsicher/Ungeprüft |
| `SACRED` | 🔐 | Rot | 5 (höchste) | Streng vertraulich |

---

## Lese-Berechtigungen

| Agent | PUBLIC | WORKSPACE | FAMILY_PRIVATE | QUARANTINE | SACRED |
|-------|--------|-----------|---------------|------------|--------|
| kirobi-core | ✅ | ✅ | ✅ (logged) | ✅ | ❌* |
| kirobi-architect | ✅ | ✅ | ❌ | ❌ | ❌ |
| kirobi-coder | ✅ | ✅ | ❌ | ❌ | ❌ |
| kirobi-ops | ✅ | ✅ | ❌ | ✅ | ❌ |
| kirobi-observer | ✅ | ✅ | ✅ (summary) | ✅ | ❌ |
| hermes-extractor | ✅ | ✅ | ❌ | ✅ | ❌ |
| samira-heart | ✅ | ✅ | ✅ | ❌ | ❌* |
| sineo-creator | ✅ | ✅ | ✅ (Sineo) | ❌ | ❌ |
| research-crew | ✅ | ✅ | ❌ | ❌ | ❌ |
| creative-agent | ✅ | ✅ | ❌ | ❌ | ❌ |
| voice-agent | ✅ | ✅ | ✅ (delegiert) | ❌ | ❌ |
| installer-agent | ✅ | ✅ | ❌ | ❌ | ❌ |
| enterprise-agent | ✅ | ✅ | ❌ | ❌ | ❌ |
| opencode | ✅ | ✅ | ❌ | ❌ | ❌ |
| openclaw | ✅ | ✅ | ❌ | ✅ | ❌ |
| hermes-reasoner | ✅ | ✅ | ❌ | ❌ | ❌ |
| obsidian | ✅ | ✅ | ✅ (lokal, kein Egress) | ❌ | ❌ |
| kidi | ✅ | ✅ | ❌ (nur via obsidian-Brücke, lokal) | ❌ | ❌ |
| keybrodi | ✅ | ✅ | ❌ | ❌ | ❌ |
| Sven (Mensch) | ✅ | ✅ | ✅ | ✅ | ✅ |

*kirobi-core und samira-heart können SACRED lesen mit expliziter Freigabe von Sven; SACRED-Inhalte bleiben für alle übrigen Agenten tabu.

> **Telegram-Boundary (siehe `docs/agent/TELEGRAM-INTEGRATION.md`):** Selbst wenn ein Agent oben FAMILY_PRIVATE lesen darf, ist die Weitergabe an Telegram (oder jeden anderen externen Dienst) hart untersagt. Der Telegram-Zonen-Gate akzeptiert ausschließlich PUBLIC und WORKSPACE.

---

## Schreib-Berechtigungen

| Agent | PUBLIC | WORKSPACE | FAMILY_PRIVATE | QUARANTINE | SACRED |
|-------|--------|-----------|---------------|------------|--------|
| kirobi-core | ✅ | ✅ | ✅ (logged) | ✅ | ❌ |
| kirobi-architect | ✅ | ✅ | ❌ | ❌ | ❌ |
| kirobi-coder | ✅ | ✅ | ❌ | ❌ | ❌ |
| kirobi-ops | ✅ | ✅ | ❌ | ✅ | ❌ |
| kirobi-observer | ✅ (reports) | ✅ (analytics) | ❌ | ❌ | ❌ |
| hermes-extractor | ✅ | ✅ | ❌ | ✅ | ❌ |
| samira-heart | ✅ | ❌ | ✅ | ❌ | ❌ |
| sineo-creator | ✅ | ✅ (Sineo) | ✅ (Sineo) | ❌ | ❌ |
| research-crew | ✅ | ✅ | ❌ | ❌ | ❌ |
| creative-agent | ✅ | ✅ | ❌ | ❌ | ❌ |
| voice-agent | ❌ | ❌ | ❌ | ❌ | ❌ |
| installer-agent | ✅ | ✅ | ❌ | ❌ | ❌ |
| enterprise-agent | ✅ | ✅ | ❌ | ❌ | ❌ |
| opencode | ✅ | ✅ | ❌ | ❌ | ❌ |
| openclaw | ✅ | ✅ | ❌ | ✅ | ❌ |
| hermes-reasoner | ✅ | ✅ | ❌ | ❌ | ❌ |
| obsidian | ✅ | ✅ | ✅ (lokaler Vault, Human-Approval) | ❌ | ❌ |
| kidi | ✅ | ✅ | ❌ | ❌ | ❌ |
| keybrodi | ✅ (Metriken) | ✅ (Metriken/Events) | ❌ | ❌ | ❌ |
| Sven (Mensch) | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## Embedding-Policy

| Zone | Embedding erlaubt | Embedding-Ziel | Cloud-Embedding |
|------|-----------------|---------------|-----------------|
| PUBLIC | ✅ | qdrant:public | ✅ (optional) |
| WORKSPACE | ✅ | qdrant:workspace | ⚠️ (mit Bestätigung) |
| FAMILY_PRIVATE | ✅ | qdrant:family (lokal) | ❌ |
| QUARANTINE | ❌ | Kein Embedding bis Freigabe | ❌ |
| SACRED | ✅ (verschlüsselt) | qdrant:sacred (encrypted) | ❌ |

---

## Datenfluss-Policy

### Erlaubte Datenflüsse

```
sources/ → [hermes-extractor] → extracts/ → [kirobi-core] → clusters/ → [kirobi-core] → canon/
                              ↘ quarantine/ (bei Fehler)
```

### Verbotene Datenflüsse

```
❌ FAMILY_PRIVATE → Cloud-APIs
❌ SACRED → Irgendein Agent ohne Human-Freigabe
❌ QUARANTINE → extracts/ oder canon/ ohne Review
❌ SACRED → WORKSPACE (Downgrade verboten)
```

---

## Audit-Logging-Anforderungen

| Aktion | PUBLIC | WORKSPACE | FAMILY_PRIVATE | SACRED |
|--------|--------|-----------|---------------|--------|
| Lesen | Nein | Nein | Ja (Agent-ID) | Ja (Zeitstempel+Grund) |
| Schreiben | Nein | Ja (Summary) | Ja (vollständig) | Ja (vollständig+Bestätigung) |
| Löschen | Ja | Ja | Ja | Ja (Human-Signature) |
| Export | Nein | Ja | Ja | Ja (Human-Signature) |
| Cloud-Sync | N/A | Ja | Verboten | Verboten |
