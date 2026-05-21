#!/usr/bin/env bash

set -Eeuo pipefail

BASE_DIR="${BENUTZER_BASE:-/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner}"
TEMPLATE_NAME="${TEMPLATE_NAME:-_Muster-Benutzerstruktur}"
MODE="${1:-all-existing}"
TARGET_USER="${2:-}"

declare -a STRUCTURE=(
  "00-Inbox/01-Schnellerfassung"
  "00-Inbox/02-Chat-Exporte/OpenAI"
  "00-Inbox/02-Chat-Exporte/Anthropic"
  "00-Inbox/02-Chat-Exporte/Google"
  "00-Inbox/02-Chat-Exporte/GitHub-Copilot"
  "00-Inbox/02-Chat-Exporte/Meta"
  "00-Inbox/02-Chat-Exporte/Perplexity"
  "00-Inbox/02-Chat-Exporte/xAI"
  "00-Inbox/02-Chat-Exporte/Andere"
  "00-Inbox/03-Dokumente-Roh/PDF"
  "00-Inbox/03-Dokumente-Roh/Office"
  "00-Inbox/03-Dokumente-Roh/Tabellen"
  "00-Inbox/03-Dokumente-Roh/Datenbanken"
  "00-Inbox/03-Dokumente-Roh/EPUB-und-EBooks"
  "00-Inbox/03-Dokumente-Roh/Archive-und-Container"
  "00-Inbox/03-Dokumente-Roh/OCR-Scans"
  "00-Inbox/04-Medien-Roh/Fotos"
  "00-Inbox/04-Medien-Roh/Videos"
  "00-Inbox/04-Medien-Roh/Audio"
  "00-Inbox/04-Medien-Roh/Musik"
  "00-Inbox/05-Web-und-Research-Importe"
  "00-Inbox/06-Messenger-und-Soziale-Kanaele"
  "00-Inbox/07-Review-Queue"
  "00-Inbox/08-Import-Protokolle"
  "01-Wissen/01-Identitaet-und-Biografie"
  "01-Wissen/02-Werte-Ziele-und-Prinzipien"
  "01-Wissen/03-Persoenlichkeit-und-Praeferenzen"
  "01-Wissen/04-Faehigkeiten-Wissen-und-Lernen"
  "01-Wissen/05-Gesundheit-und-Wohlbefinden"
  "01-Wissen/06-Beziehungen-und-Familie"
  "01-Wissen/07-Arbeit-Business-und-Finanzen"
  "01-Wissen/08-Kreativitaet-und-Medien"
  "01-Wissen/09-Systeme-Geraete-und-Accounts"
  "01-Wissen/10-Orte-Reisen-und-Lebensumfeld"
  "01-Wissen/11-Timeline-und-Lebensereignisse"
  "01-Wissen/12-Stammbaum"
  "01-Wissen/13-Digitaler-Zwilling"
  "02-Projekte/Privat"
  "02-Projekte/Familie"
  "02-Projekte/Business"
  "02-Projekte/Kreativitaet"
  "02-Projekte/Lernen"
  "02-Projekte/Haus-und-Alltag"
  "02-Projekte/Reisen-und-Events"
  "02-Projekte/Gesundheit-und-Routinen"
  "02-Projekte/Automationen-und-Experimente"
  "03-Erfahrungen/Tagebuch"
  "03-Erfahrungen/Selbstreflexion"
  "03-Erfahrungen/Emotionen-und-Stimmungen"
  "03-Erfahrungen/Gespraeche-und-Beziehungsdynamiken"
  "03-Erfahrungen/Coaching-und-Mediation"
  "03-Erfahrungen/Entscheidungen-und-Retrospektiven"
  "03-Erfahrungen/Learnings"
  "03-Erfahrungen/Dankbarkeit-und-Rituale"
  "04-Referenzen/Menschen-und-Kontakte"
  "04-Referenzen/Organisationen-und-Kunden"
  "04-Referenzen/Konten-und-Mitgliedschaften"
  "04-Referenzen/Vertraege-und-Services"
  "04-Referenzen/Geraete-und-Inventar"
  "04-Referenzen/Vorlagen-und-Checklisten"
  "04-Referenzen/Prompt-Bibliothek"
  "04-Referenzen/Quellen-und-Literatur"
  "05-Archiv/Import-Snapshots"
  "05-Archiv/Superseded"
  "05-Archiv/Altdaten"
  "05-Archiv/Exporte"
  "Dokumente/01-Identitaet-und-Personenstand"
  "Dokumente/02-Familie-und-Stammbaum"
  "Dokumente/03-Gesundheit-und-Vorsorge"
  "Dokumente/04-Finanzen-Steuern-und-Versicherungen"
  "Dokumente/05-Arbeit-Business-und-Vertraege"
  "Dokumente/06-Bildung-Zertifikate-und-Lizenzen"
  "Dokumente/07-Wohnen-Haushalt-und-Mobilitaet"
  "Dokumente/08-Reisen-und-Buchungen"
  "Dokumente/09-Rechtliches-und-Nachweise"
  "Dokumente/10-Scans-OCR-und-Ablage"
  "Dokumente/99-Vertraulich-SACRED"
  "Medien/Fotos/Kamera-Uploads"
  "Medien/Fotos/Familienalbum"
  "Medien/Fotos/Belege-und-Scans"
  "Medien/Fotos/Erinnerungen"
  "Medien/Videos/Rohmaterial"
  "Medien/Videos/Familienmomente"
  "Medien/Videos/Projekte"
  "Medien/Videos/Screenrecordings"
  "Medien/Audio/Sprachmemos"
  "Medien/Audio/Meetings"
  "Medien/Audio/Musik-Ideen"
  "Medien/Audio/Podcasts"
  "Medien/Musik/Tracks"
  "Medien/Musik/Samples"
  "Medien/Musik/Referenzen"
  "Medien/Design-und-3D/Bilder"
  "Medien/Design-und-3D/Grafiken"
  "Medien/Design-und-3D/3D-Modelle"
  "agent/memory/entities"
  "agent/memory/observations"
  "agent/memory/summaries"
  "agent/hermes-runtime/sessions"
  "agent/hermes-runtime/exports"
  "agent/workflows"
  "agent/prompts"
  "agent/ingest/queue"
  "agent/ingest/manifests"
  "agent/ingest/mappings"
  "agent/ingest/processed"
  "agent/ingest/failed"
  "agent/analytics"
  "agent/digital-twin"
  ".obsidian"
)

ensure_file() {
  local path="$1"
  local content="$2"
  if [[ ! -e "$path" ]]; then
    mkdir -p "$(dirname "$path")"
    printf '%s\n' "$content" > "$path"
  fi
}

root_readme() {
  local owner="$1"
  cat <<EOF
---
zone: WORKSPACE
owner: ${owner}
scope: user-root
created_by: OpenDisruption bootstrap-user-folder-structure.sh
version: 1.0
---

# Benutzerordner ${owner}

Dieser Ordner ist die kanonische Ablage fuer das personalisierte OpenDisruption-Leben dieses Benutzers.

## Zweck
- alle Rohimporte sicher aufnehmen
- Wissen, Erfahrungen, Dokumente und Medien sauber strukturieren
- Hermes und persoenliche Agenten mit verifizierten Fakten versorgen
- spaeter semantische Suche, Lebensanalyse und Digital-Twin-Aufbau ermoeglichen

## Hauptbereiche
- \`00-Inbox/\` -> alles Neue, Unsortierte, Exporte, Uploads, OCR, Chat-Logs
- \`01-Wissen/\` -> verifiziertes, verdichtetes Wissen ueber Leben, Kontexte und Muster
- \`02-Projekte/\` -> aktive Vorhaben und Umsetzungsarbeit
- \`03-Erfahrungen/\` -> Tagebuch, Reflexion, Emotionen, Learnings
- \`04-Referenzen/\` -> Kontakte, Konten, Vorlagen, Literatur, Geraete
- \`Dokumente/\` -> strukturierte Langzeitablage fuer Nachweise und vertrauliche Dateien
- \`Medien/\` -> Fotos, Videos, Audio, Musik, Design und 3D
- \`agent/\` -> Profil, Memory, Hermes-Runtime, Ingest-Queue und Digital-Twin-Artefakte

## Wichtig
- Das Dateisystem ist die kanonische Quelle.
- Nur bestaetigte Fakten duerfen in \`agent/profil.yaml\` oder Langzeit-Memory landen.
- Rohimporte werden zuerst in \`00-Inbox/\` abgelegt und erst danach extrahiert, klassifiziert und eingeordnet.
EOF
}

root_agents() {
  local owner="$1"
  cat <<EOF
---
zone: WORKSPACE
owner: ${owner}
scope: user-root
created_by: OpenDisruption bootstrap-user-folder-structure.sh
version: 1.0
---

# AGENTS.md - ${owner}

## Auftrag
Dieser Benutzerordner repraesentiert das komplette personalisierte OpenDisruption-Abbild von ${owner}: Wissen, Dateien, Medien, Erfahrungen, Beziehungen, Dokumente, Routinen und den entstehenden digitalen Zwilling.

## Arbeitsreihenfolge
1. Neue Inhalte zuerst in \`00-Inbox/\` aufnehmen.
2. Relevante Fakten extrahieren, verifizieren und in \`01-Wissen/\` oder \`agent/profil.yaml\` ueberfuehren.
3. Laufende Themen in \`02-Projekte/\`, persoenliche Reflexion in \`03-Erfahrungen/\`, stabile Referenzen in \`04-Referenzen/\`.
4. Originale und Nachweise in \`Dokumente/\`, Medien in \`Medien/\`, agentische Laufzeitdaten in \`agent/\`.

## Regeln
- Immer genau eine gezielte Klaerungsfrage stellen, wenn Kontext fehlt.
- Nie Fakten erfinden; unbestaetigte Aussagen bleiben in Rohnotizen oder Review-Queues.
- Sensible Dokumente bevorzugt in \`Dokumente/99-Vertraulich-SACRED/\` ablegen oder lokal kennzeichnen.
- Chat-Exporte und Fremd-Exporte zuerst roh sichern, dann stufenweise extrahieren.

## Zielbild
Am Ende soll dieser Ordner den Nutzer so vollstaendig und sauber abbilden, dass OpenDisruption daraus personalisierte Hilfe, semantische Suche, Selbstreflexion und einen belastbaren digitalen Zwilling aufbauen kann.
EOF
}

top_level_agents() {
  local owner="$1"
  local scope="$2"
  case "$scope" in
    "00-Inbox")
      cat <<EOF
---
zone: WORKSPACE
owner: ${owner}
scope: inbox
created_by: OpenDisruption bootstrap-user-folder-structure.sh
version: 1.0
---

# AGENTS.md - ${owner} / 00-Inbox

Dieser Bereich ist der sichere Eingang fuer Uploads, Chat-Exporte, OCR-Scans, Datenbank-Dumps, Medien und spontane Erfassung.

- Erst roh sichern, dann klassifizieren.
- Bei Imports immer Quelle, Datum, Format und vermuteten Kontext notieren.
- Nach dem Review Inhalte in Wissen, Dokumente, Medien, Projekte oder Erfahrungen ueberfuehren.
EOF
      ;;
    "01-Wissen")
      cat <<EOF
---
zone: WORKSPACE
owner: ${owner}
scope: knowledge
created_by: OpenDisruption bootstrap-user-folder-structure.sh
version: 1.0
---

# AGENTS.md - ${owner} / 01-Wissen

Hier entsteht belastbares Langzeitwissen ueber den Benutzer.

- Nur verdichtete, wiederverwendbare Erkenntnisse ablegen.
- Jede Erkenntnis braucht Quelle oder Herkunft.
- Identitaet, Werte, Muster, Lebensereignisse und Digital-Twin-Wissen hier pflegen.
EOF
      ;;
    "02-Projekte")
      cat <<EOF
---
zone: WORKSPACE
owner: ${owner}
scope: projects
created_by: OpenDisruption bootstrap-user-folder-structure.sh
version: 1.0
---

# AGENTS.md - ${owner} / 02-Projekte

Aktive Vorhaben gehoeren hier hinein.

- Nach Lebensbereichen trennen.
- Ziele, Status, naechste Schritte und Entscheidungen dokumentieren.
- Abgeschlossene Projekte in Erfahrungen oder Archiv ueberfuehren.
EOF
      ;;
    "03-Erfahrungen")
      cat <<EOF
---
zone: WORKSPACE
owner: ${owner}
scope: experiences
created_by: OpenDisruption bootstrap-user-folder-structure.sh
version: 1.0
---

# AGENTS.md - ${owner} / 03-Erfahrungen

Dieser Bereich sammelt gelebte Erfahrungen, Reflexionen, Tagebuch, Emotionen und Learnings.

- Fokus auf Selbstreflexion, Wachstum und Beziehungsmuster.
- Ereignisse moeglichst datiert festhalten.
- Nur stabile Learnings nach \`01-Wissen/\` heben.
EOF
      ;;
    "04-Referenzen")
      cat <<EOF
---
zone: WORKSPACE
owner: ${owner}
scope: references
created_by: OpenDisruption bootstrap-user-folder-structure.sh
version: 1.0
---

# AGENTS.md - ${owner} / 04-Referenzen

Hier liegen langfristig nuetzliche Referenzen: Menschen, Konten, Services, Literatur, Vorlagen, Geraete.

- Daten strukturiert und auffindbar halten.
- Keine losen Gedanken hier ablegen.
- Referenzen mit Projekten, Wissen und Dokumenten verlinken.
EOF
      ;;
    "05-Archiv")
      cat <<EOF
---
zone: WORKSPACE
owner: ${owner}
scope: archive
created_by: OpenDisruption bootstrap-user-folder-structure.sh
version: 1.0
---

# AGENTS.md - ${owner} / 05-Archiv

Archiv fuer Import-Snapshots, Exporte, Altdaten und ersetzte Inhalte.

- Nicht loeschen, sondern nachvollziehbar verschieben.
- Archiv bleibt lesbar, aber nicht der aktive Arbeitsbereich.
EOF
      ;;
    "Dokumente")
      cat <<EOF
---
zone: WORKSPACE
owner: ${owner}
scope: documents
created_by: OpenDisruption bootstrap-user-folder-structure.sh
version: 1.0
---

# AGENTS.md - ${owner} / Dokumente

Hier liegen Originale, Nachweise, Scans und strukturierte Dokumentenablage.

- Originale niemals ueberschreiben.
- Scans, OCR-Texte und Metadaten nachvollziehbar ablegen.
- Hochsensible Dateien bevorzugt in \`99-Vertraulich-SACRED/\`.
EOF
      ;;
    "Medien")
      cat <<EOF
---
zone: WORKSPACE
owner: ${owner}
scope: media
created_by: OpenDisruption bootstrap-user-folder-structure.sh
version: 1.0
---

# AGENTS.md - ${owner} / Medien

Fotos, Videos, Audio, Musik und kreative Artefakte werden hier geordnet.

- Rohmaterial und kuratierte Ergebnisse trennen.
- Wichtige Medien mit Ereignissen, Projekten oder Personen verknuepfen.
- Medien duerfen spaeter fuer Suche, Erinnerungen und Digital-Twin-Profile ausgewertet werden.
EOF
      ;;
    "agent")
      cat <<EOF
---
zone: WORKSPACE
owner: ${owner}
scope: agent-runtime
created_by: OpenDisruption bootstrap-user-folder-structure.sh
version: 1.0
---

# AGENTS.md - ${owner} / agent

Technische und semantische Benutzerpersonalisierung fuer Hermes und OpenDisruption.

- \`profil.yaml\` nur mit verifizierten Fakten pflegen.
- \`memory/\` fuer maschinenlesbares Langzeitgedaechtnis.
- \`ingest/\` fuer Import-Queues, Mapping und Fehlerfaelle.
- \`digital-twin/\` fuer abgeleitete Modelle und Persona-Synthesen.
EOF
      ;;
    *)
      return 0
      ;;
  esac
}

profile_yaml() {
  local owner="$1"
  cat <<EOF
display_name: ${owner}
last_updated: ''
persona:
  identity: Ich bin der persoenliche Hermes-Agent fuer ${owner}.
  anti_hallucination: |
    Ich spreche nur ueber bestaetigte Fakten.
    Wenn etwas fehlt, sage ich klar, dass ich es noch nicht weiss.
  capabilities:
    - Wissen strukturiert aufbauen
    - Dokumente und Medien einordnen
    - Tagebuch und Reflexion begleiten
    - Projekte und Lebensbereiche verknuepfen
    - Digital-Twin-Wissen verdichten
  model:
    primary: qwen2.5:14b
    fallback: openai/gpt-4.1-mini
facts: []
unknown_facts:
  - question: Was sollte OpenDisruption ueber ${owner} auf jeden Fall wissen?
    priority: high
EOF
}

hermes_config() {
  local owner="$1"
  cat <<EOF
model:
  default: qwen2.5:14b
  fallback: openai/gpt-4.1-mini
memory:
  enabled: true
  path: /opt/data
workspace:
  user_root: /opt/user
persona:
  name: Hermes ${owner}
  mission: Baue ein sauberes, faktenbasiertes Langzeitgedaechtnis fuer ${owner} auf.
EOF
}

knowledge_graph() {
  local owner="$1"
  cat <<EOF
{
  "entities": [
    {
      "name": "${owner}",
      "entityType": "person",
      "observations": []
    }
  ],
  "relations": []
}
EOF
}

seed_target() {
  local target_dir="$1"
  local owner="$2"

  mkdir -p "$target_dir"

  local rel
  for rel in "${STRUCTURE[@]}"; do
    mkdir -p "$target_dir/$rel"
  done

  ensure_file "$target_dir/README.md" "$(root_readme "$owner")"
  ensure_file "$target_dir/AGENTS.md" "$(root_agents "$owner")"
  ensure_file "$target_dir/Profil.md" "# Profil ${owner}" 

  ensure_file "$target_dir/00-Inbox/AGENTS.md" "$(top_level_agents "$owner" "00-Inbox")"
  ensure_file "$target_dir/01-Wissen/AGENTS.md" "$(top_level_agents "$owner" "01-Wissen")"
  ensure_file "$target_dir/02-Projekte/AGENTS.md" "$(top_level_agents "$owner" "02-Projekte")"
  ensure_file "$target_dir/03-Erfahrungen/AGENTS.md" "$(top_level_agents "$owner" "03-Erfahrungen")"
  ensure_file "$target_dir/04-Referenzen/AGENTS.md" "$(top_level_agents "$owner" "04-Referenzen")"
  ensure_file "$target_dir/05-Archiv/AGENTS.md" "$(top_level_agents "$owner" "05-Archiv")"
  ensure_file "$target_dir/Dokumente/AGENTS.md" "$(top_level_agents "$owner" "Dokumente")"
  ensure_file "$target_dir/Medien/AGENTS.md" "$(top_level_agents "$owner" "Medien")"
  ensure_file "$target_dir/agent/AGENTS.md" "$(top_level_agents "$owner" "agent")"

  ensure_file "$target_dir/agent/profil.yaml" "$(profile_yaml "$owner")"
  ensure_file "$target_dir/agent/memory/knowledge_graph.json" "$(knowledge_graph "$owner")"
  ensure_file "$target_dir/agent/hermes-runtime/config.yaml" "$(hermes_config "$owner")"
  ensure_file "$target_dir/.obsidian/README.md" "# Obsidian\n\nLokale Vault-spezifische Konfiguration fuer ${owner}."
}

seed_template() {
  seed_target "$BASE_DIR/$TEMPLATE_NAME" "<BENUTZERNAME>"
}

seed_existing_users() {
  local user_dir
  while IFS= read -r -d '' user_dir; do
    local owner
    owner="$(basename "$user_dir")"
    [[ "$owner" == "$TEMPLATE_NAME" ]] && continue
    [[ "$owner" == .* ]] && continue
    seed_target "$user_dir" "$owner"
  done < <(find "$BASE_DIR" -mindepth 1 -maxdepth 1 -type d -print0)
}

seed_one_user() {
  if [[ -z "$TARGET_USER" ]]; then
    echo "usage: $0 user <Name>" >&2
    exit 1
  fi
  seed_target "$BASE_DIR/$TARGET_USER" "$TARGET_USER"
}

mkdir -p "$BASE_DIR"

case "$MODE" in
  all-existing)
    seed_template
    seed_existing_users
    ;;
  template-only)
    seed_template
    ;;
  user)
    seed_template
    seed_one_user
    ;;
  *)
    echo "unknown mode: $MODE" >&2
    echo "expected: all-existing | template-only | user <Name>" >&2
    exit 1
    ;;
esac

echo "Benutzerstruktur erfolgreich vorbereitet unter: $BASE_DIR"
