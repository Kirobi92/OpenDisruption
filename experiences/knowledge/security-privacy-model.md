---
zone: WORKSPACE
type: wissen
version: 1.0
---

# Sicherheits- und Datenschutz-Modell

## Kern-Prinzip: Local-First

Alle sensiblen Daten bleiben auf lokalem Hardware. Cloud-Services nur für nicht-sensible, öffentliche Inhalte.

## Zonen-Übersicht

| Zone | Beschreibung | Cloud erlaubt? |
|------|-------------|----------------|
| PUBLIC | Öffentliche Inhalte | Ja |
| WORKSPACE | Arbeits-Inhalte | Nein |
| FAMILY_PRIVATE | Familiäre Inhalte | **Nie** |
| QUARANTINE | Nicht klassifizierte Inhalte | Nein |
| SACRED | Höchst-sensible Inhalte | **Nie, mit HitL** |

## Was niemals in die Cloud geht

- Familiäre Gespräche und Dokumente
- Medizinische Informationen
- Finanzielle Details
- Persönliche Identifikationsdaten
- Kinder-bezogene Inhalte (Sineo)

## Backup-Sicherheit

Backups sind verschlüsselt (AES-256). Backup-Keys werden separat gespeichert.
