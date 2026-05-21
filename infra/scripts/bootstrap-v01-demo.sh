#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="${OPEN_DISRUPTION_DATA_ROOT:-/Datenspeicher/OpenDisruption_Datenstruktur}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GLOBAL_BOOTSTRAP="$REPO_ROOT/infra/scripts/bootstrap-global-data-structure.sh"
USER_BOOTSTRAP="$REPO_ROOT/infra/scripts/bootstrap-user-folder-structure.sh"
DEMO_ROOT="$ROOT_DIR/OpenDisruption-v0.1"
DEMO_USER="Demo-User"
DEMO_USER_ROOT="$ROOT_DIR/Benutzer-Ordner/$DEMO_USER"

write_file() {
  local path="$1"
  mkdir -p "$(dirname "$path")"
  cat > "$path"
}

seed_demo_user() {
  write_file "$DEMO_USER_ROOT/Profil.md" <<'EOF'
# Demo User

Der Demo User ist die exemplarische Persona fuer OpenDisruption v0.1.

## Kurzprofil
- nutzt OpenDisruption fuer persoenliches Wissensmanagement, Uploads, Reflexion und Zielarbeit
- sammelt Chat-Exporte, Dokumente, Medien und Life-Logs lokal
- baut mit Hermes schrittweise einen digitalen Zwilling auf

## Fokus
1. Ordnung aus Rohdaten erzeugen
2. semantisch suchbares Langzeitwissen aufbauen
3. persoenliche Optimierung mit KI-Begleitung
EOF

  write_file "$DEMO_USER_ROOT/agent/profil.yaml" <<'EOF'
display_name: Demo User
last_updated: '2026-05-15'
persona:
  identity: Ich bin Hermes fuer den Demo User und zeige den Zielzustand von OpenDisruption v0.1.
  anti_hallucination: |
    Ich nutze nur verifizierte oder explizit als Demo markierte Informationen.
    Wenn mir Fakten fehlen, stelle ich Rueckfragen statt Inhalte zu erfinden.
  capabilities:
    - Chat-Exporte und Dokumente strukturieren
    - persoenliches Wissen verdichten
    - Tagebuch und Selbstreflexion begleiten
    - Projekte, Medien und Dokumente verknuepfen
    - einen belastbaren Digital Twin vorbereiten
  model:
    primary: qwen2.5:14b
    fallback: openai/gpt-4.1-mini
facts:
  - category: identity
    fact: Demo User ist eine Musterpersona fuer OpenDisruption v0.1.
    confidence: verified
  - category: goals
    fact: Der Fokus liegt auf lokaler Wissensstruktur, persoenlicher Assistenz und Digital-Twin-Aufbau.
    confidence: verified
unknown_facts:
  - question: Welche Lebensbereiche sollen als naechstes tiefer personalisiert werden?
    priority: high
EOF

  write_file "$DEMO_USER_ROOT/00-Inbox/02-Chat-Exporte/OpenAI/2026-05-15-chat-export-demo.md" <<'EOF'
# Chat Export Demo

Quelle: OpenAI Export  
Status: roh importiert

## Enthalten
- Zielplanung fuer persoenliche Projekte
- Fragen zu Wissensstruktur und Uploads
- Reflexion ueber Alltag, Fokus und Ziele

## Naechster Schritt
- Aussagen extrahieren
- verifizierte Fakten nach `01-Wissen/`
- offene Themen als Projekte oder Tagebuchfortsetzung erfassen
EOF

  write_file "$DEMO_USER_ROOT/00-Inbox/03-Dokumente-Roh/PDF/2026-05-15-vertragsmappe-demo.md" <<'EOF'
# Dokumentenpaket Demo

Dieses Demo-Dokument repraesentiert einen PDF- oder Scan-Import.

## Typische Inhalte
- Vertrage
- Rechnungen
- amtliche Nachweise
- Bildungs- und Versicherungsunterlagen

## Pipeline
1. Rohablage
2. OCR / Extraktion
3. Metadaten
4. Ablage in `Dokumente/`
5. semantische Auffindbarkeit
EOF

  write_file "$DEMO_USER_ROOT/00-Inbox/04-Medien-Roh/Fotos/2026-05-15-familienfotos-demo.md" <<'EOF'
# Medienimport Demo

Hier landet Rohmaterial aus Kamera, Cloud-Export oder Messenger.

## Spaetere Verwendung
- Familienchronik
- Erinnerungsnarrative
- visuelle Suche
- Verknuepfung mit Ereignissen, Orten und Personen
EOF

  write_file "$DEMO_USER_ROOT/01-Wissen/01-Identitaet-und-Biografie/biografie-kurzprofil.md" <<'EOF'
# Biografie Kurzprofil

Der Demo User repraesentiert eine Person, deren gesamter Lebenskontext lokal und strukturiert in OpenDisruption gepflegt wird.

## Relevante Achsen
- Identitaet
- Rollen
- Ziele
- Werte
- Lebensereignisse
- Beziehungen
EOF

  write_file "$DEMO_USER_ROOT/01-Wissen/12-Stammbaum/stammbaum-skizze.md" <<'EOF'
# Stammbaum Skizze

Diese Datei zeigt, wie OpenDisruption Familienwissen strukturieren kann.

## Elemente
- Personen
- Beziehungen
- Ereignisse
- Dokumentquellen
- offene Luecken fuer spaetere Klaerung
EOF

  write_file "$DEMO_USER_ROOT/01-Wissen/13-Digitaler-Zwilling/digital-twin-brief.md" <<'EOF'
# Digital Twin Brief

Der digitale Zwilling entsteht nicht durch Fantasie, sondern durch verdichtete, verifizierte Muster.

## Ziel
- persoenliche Praeferenzen erkennen
- Entscheidungen besser vorbereiten
- Wissen, Ziele, Routinen und Emotionen verknuepfen
- kontextstarke Assistenz fuer Alltag, Kreativitaet und Entwicklung schaffen

## Eingangsquellen
- Chatverlaeufe
- Dokumente
- Medien
- Tagebuch
- Projekte
- Referenzen
EOF

  write_file "$DEMO_USER_ROOT/02-Projekte/Business/opendisruption-v01-launch.md" <<'EOF'
# OpenDisruption v0.1 Launch

## Ziel
Die erste sichtbare, zusammenhaengende Demo von OpenDisruption mit:
- Datenspeicherstruktur
- Frontends
- Agentenprofilen
- Beispielwissen
- Upload- und Suchpfaden

## Definition of Done
- Datenstruktur vorhanden
- Demo-Seiten in Web und Dashboard sichtbar
- Beispielinhalte in mindestens einem Demo-User
- nachvollziehbare Erklaerung fuer Menschen und KI-Agenten
EOF

  write_file "$DEMO_USER_ROOT/03-Erfahrungen/Tagebuch/2026-05-15-v01-start.md" <<'EOF'
# Tagebuch — v0.1 Start

Heute wurde die erste richtige OpenDisruption-v0.1-Demo sichtbar gemacht.

## Beobachtung
Die Kombination aus Struktur, Agentenprofilen und lokaler Frontend-Navigation zeigt erstmals, wie persoenliches Leben, Wissen und KI-Orchestrierung zusammenwachsen koennen.

## Learning
Die Dateistruktur muss dem Endzustand vorauslaufen, auch wenn einzelne Parser und Automationen erst spaeter dazukommen.
EOF

  write_file "$DEMO_USER_ROOT/Dokumente/01-Identitaet-und-Personenstand/geburtsurkunde-demo.md" <<'EOF'
# Geburtsurkunde Demo

Platzhalter fuer hochgeladene oder eingescannte Personenstandsdokumente.

## Hinweise
- Originaldatei bleibt unveraendert
- OCR und Metadaten werden getrennt abgelegt
- spaetere semantische Suche nur zonenkonform
EOF

  write_file "$DEMO_USER_ROOT/Dokumente/02-Familie-und-Stammbaum/stammbuch-demo.md" <<'EOF'
# Stammbuch Demo

Platzhalter fuer Familien- und Heiratsdokumente.

## Zweck
- Familienzusammenhaenge dokumentieren
- Nachweise strukturiert ablegen
- Stammbaumwissen und Lebensereignisse verknuepfen
EOF

  write_file "$DEMO_USER_ROOT/Medien/Fotos/Familienalbum/familienalbum-demo.md" <<'EOF'
# Familienalbum Demo

Kuratiertes Fotoalbum fuer bedeutende Erinnerungen, Personen und Ereignisse.
EOF

  write_file "$DEMO_USER_ROOT/Medien/Audio/Sprachmemos/sprachmemo-demo.md" <<'EOF'
# Sprachmemo Demo

Sprachmemos dienen als schneller Capture-Kanal fuer Gedanken, Aufgaben, Emotionen und Story-Fragmente.
EOF

  write_file "$DEMO_USER_ROOT/agent/digital-twin/system-prompt-demo.md" <<'EOF'
# Digital Twin System Prompt Demo

## Rolle
Du bist der reflektierende, faktenbasierte digitale Zwilling des Demo Users.

## Regeln
- nur bestaetigte oder als Demo markierte Informationen verwenden
- keine Fantasie-Biografie erzeugen
- Unsicherheit explizit benennen
- Vorschlaege aus Zielen, Routinen, Stimmung und Kontext ableiten
EOF

  write_file "$DEMO_USER_ROOT/agent/ingest/manifests/demo-ingest-batches.json" <<'EOF'
{
  "batches": [
    {
      "source": "chat-export-openai",
      "target": "00-Inbox/02-Chat-Exporte/OpenAI",
      "status": "seeded-demo"
    },
    {
      "source": "document-bundle",
      "target": "00-Inbox/03-Dokumente-Roh/PDF",
      "status": "seeded-demo"
    },
    {
      "source": "media-bundle",
      "target": "00-Inbox/04-Medien-Roh/Fotos",
      "status": "seeded-demo"
    }
  ]
}
EOF
}

seed_global_demo_content() {
  write_file "$ROOT_DIR/Geteilte-Wissensbasis/01-Canon-und-Richtlinien/opendisruption-v01-vision.md" <<'EOF'
# OpenDisruption v0.1 Vision

OpenDisruption v0.1 zeigt erstmals als Demo:
- dateibasierte Lebensstruktur
- pro Benutzer personalisierte Agenten
- lokale Assistenz ueber Wissen, Dokumente, Medien und Reflexion
- den Weg vom Rohimport bis zum Digital Twin
EOF

  write_file "$ROOT_DIR/Integrationen-und-Importe/01-Chat-Importe/provider-katalog-v01.md" <<'EOF'
# Provider Katalog v0.1

Geplante oder vorbereitete Importquellen:
- OpenAI
- Anthropic
- Google
- GitHub Copilot
- Meta
- Perplexity
- xAI
- weitere Exportformate
EOF

  write_file "$ROOT_DIR/Orchestrierung-und-Agenten/01-Hermes/opendisruption-v01-orchestrierung.md" <<'EOF'
# Hermes in OpenDisruption v0.1

Hermes ist der persoenliche Laufzeitkern fuer:
- per-user Memory
- Fragen, Reflexion und Onboarding
- Dokument- und Wissenskontext
- spaetere taegliche Begleitung
EOF

  write_file "$ROOT_DIR/Systemkonfiguration/03-Modelle-und-Provider/v01-stack.md" <<'EOF'
# Modell- und Provider-Stack v0.1

## Primar
- lokale Ollama-Modelle

## Fallback
- GitHub Models

## Ziel
Lokale Datenhoheit mit optionaler, kontrollierter Erweiterung fuer nicht-sensitive Kontexte.
EOF

  write_file "$ROOT_DIR/Backups-und-Exporte/03-Berichte-und-Audits/v01-demo-readiness.md" <<'EOF'
# Demo Readiness v0.1

## Enthalten
- globale Datenstruktur
- Benutzer-Musterstruktur
- Ordnerdokumentation
- Demo-User mit Beispielinhalten
- Frontend-Routen fuer User- und Operator-Sicht
EOF
}

write_manifest() {
  local folder_count ordnerinfo_count demo_file_count
  folder_count="$(find "$ROOT_DIR" -type d | wc -l | tr -d ' ')"
  ordnerinfo_count="$(find "$ROOT_DIR" -type f -name 'ORDNERINFO.md' | wc -l | tr -d ' ')"
  demo_file_count="$(find "$DEMO_USER_ROOT" -type f | wc -l | tr -d ' ')"

  write_file "$DEMO_ROOT/manifest.json" <<EOF
{
  "version": "0.1",
  "name": "OpenDisruption v0.1 Demo",
  "tagline": "Die erste sichtbare, zusammenhaengende Demo von OpenDisruption als lokales Lebens-, Wissens- und Agentenbetriebssystem.",
  "dataRoot": "$ROOT_DIR",
  "demoUser": "$DEMO_USER",
  "stats": {
    "totalFolders": $folder_count,
    "ordnerInfoFiles": $ordnerinfo_count,
    "demoUserFiles": $demo_file_count
  },
  "pillars": [
    {
      "title": "Lebensdaten lokal strukturieren",
      "description": "Benutzerordner fuer Wissen, Dokumente, Medien, Projekte, Erfahrungen und Referenzen."
    },
    {
      "title": "Rohimporte in Wissen ueberfuehren",
      "description": "Chat-Exporte, Dokumente, OCR, Medien und weitere Formate landen zuerst im Inbox- und Importbereich."
    },
    {
      "title": "Per-user Hermes und Memory",
      "description": "Jeder Benutzer bekommt eigene Agentenprofile, Runtime-Konfiguration und persistentes Memory."
    },
    {
      "title": "Digital Twin vorbereiten",
      "description": "Timeline, Stammbaum, Verhaltensmuster und Persona-Briefs werden als belastbare Grundlage aufgebaut."
    }
  ],
  "frontendRoutes": [
    {
      "surface": "web",
      "label": "OpenDisruption v0.1 Demo",
      "path": "/opendisruption-v01"
    },
    {
      "surface": "dashboard",
      "label": "Demo Control View",
      "path": "/dashboard/demo"
    }
  ],
  "highlights": [
    {
      "title": "Demo User",
      "path": "$DEMO_USER_ROOT",
      "description": "Beispielhafter Benutzer mit Biografie, Inbox, Projekten, Dokumenten, Medien und Digital-Twin-Brief."
    },
    {
      "title": "Globale Wissensbasis",
      "path": "$ROOT_DIR/Geteilte-Wissensbasis",
      "description": "Gemeinsam nutzbare Richtlinien, Familien- und Businesskontexte sowie Quellen."
    },
    {
      "title": "Integrationen und Importe",
      "path": "$ROOT_DIR/Integrationen-und-Importe",
      "description": "Eingang fuer Chat-Exporte, Dokumente, Medien, OCR und externe Datenstroeme."
    },
    {
      "title": "Orchestrierung und Agenten",
      "path": "$ROOT_DIR/Orchestrierung-und-Agenten",
      "description": "Hermes, KeyCodi, Policies und Workflows fuer den operativen Agentenbetrieb."
    }
  ],
  "seedFiles": [
    "$DEMO_USER_ROOT/00-Inbox/02-Chat-Exporte/OpenAI/2026-05-15-chat-export-demo.md",
    "$DEMO_USER_ROOT/01-Wissen/13-Digitaler-Zwilling/digital-twin-brief.md",
    "$DEMO_USER_ROOT/03-Erfahrungen/Tagebuch/2026-05-15-v01-start.md",
    "$ROOT_DIR/Geteilte-Wissensbasis/01-Canon-und-Richtlinien/opendisruption-v01-vision.md",
    "$ROOT_DIR/Orchestrierung-und-Agenten/01-Hermes/opendisruption-v01-orchestrierung.md"
  ],
  "nextSteps": [
    "Parser fuer Office, Excel, EPUB, Datenbanken und Medienanalyse vervollstaendigen",
    "Live-Ingestion von Demo-Ordnern in Suchindizes anbinden",
    "Chat, Upload, Suche und Digital-Twin-Sicht ueber echte Benutzerfluesse verbinden",
    "Dashboard um Demo-Metriken, ingestierte Mengen und Personalisierungsfortschritt erweitern"
  ]
}
EOF

  write_file "$DEMO_ROOT/README.md" <<EOF
# OpenDisruption v0.1 Demo

Diese Demo macht den Zielzustand von OpenDisruption erstmals sichtbar:

- globale Datenstruktur
- per-user Lebensordner
- Beispielwissen
- Importpfade
- Agentenprofil und Digital-Twin-Vorbereitung
- Frontend-Routen fuer User- und Operator-Sicht

## Frontends
- Web: /opendisruption-v01
- Dashboard: /dashboard/demo

## Demo User
- $DEMO_USER_ROOT

## Datenwurzel
- $ROOT_DIR
EOF
}

main() {
  mkdir -p "$ROOT_DIR"
  bash "$GLOBAL_BOOTSTRAP" >/dev/null
  BENUTZER_BASE="$ROOT_DIR/Benutzer-Ordner" bash "$USER_BOOTSTRAP" user "$DEMO_USER" >/dev/null
  mkdir -p "$DEMO_ROOT"

  seed_demo_user
  seed_global_demo_content
  write_manifest

  echo "OpenDisruption v0.1 Demo vorbereitet unter: $DEMO_ROOT"
}

main "$@"
