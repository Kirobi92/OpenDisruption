#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="${OPEN_DISRUPTION_DATA_ROOT:-/Datenspeicher/OpenDisruption_Datenstruktur}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
USER_BOOTSTRAP="$REPO_ROOT/infra/scripts/bootstrap-user-folder-structure.sh"

declare -a GLOBAL_STRUCTURE=(
  "Benutzer-Ordner"
  "Geteilte-Wissensbasis"
  "Geteilte-Wissensbasis/01-Canon-und-Richtlinien"
  "Geteilte-Wissensbasis/02-Gemeinsame-Erfahrungen"
  "Geteilte-Wissensbasis/03-Familie-und-Beziehungen"
  "Geteilte-Wissensbasis/04-Business-und-Kunden"
  "Geteilte-Wissensbasis/05-Forschung-und-Quellen"
  "Integrationen-und-Importe"
  "Integrationen-und-Importe/01-Chat-Importe"
  "Integrationen-und-Importe/02-Dokumenten-Importe"
  "Integrationen-und-Importe/03-Medien-Importe"
  "Integrationen-und-Importe/04-Datenbank-und-Systemimporte"
  "Integrationen-und-Importe/05-Web-und-Research-Importe"
  "Integrationen-und-Importe/06-Messenger-und-Social-Importe"
  "Integrationen-und-Importe/07-OCR-und-Transkripte"
  "Orchestrierung-und-Agenten"
  "Orchestrierung-und-Agenten/01-Hermes"
  "Orchestrierung-und-Agenten/02-KeyCodi-und-KIDI"
  "Orchestrierung-und-Agenten/03-Agent-Profile-und-Policies"
  "Orchestrierung-und-Agenten/04-Workflows-und-Automationen"
  "Orchestrierung-und-Agenten/05-Audit-und-Beobachtung"
  "Systemkonfiguration"
  "Systemkonfiguration/01-Umgebungen-und-Secrets-Hinweise"
  "Systemkonfiguration/02-Compose-Caddy-und-Routing"
  "Systemkonfiguration/03-Modelle-und-Provider"
  "Systemkonfiguration/04-Zonen-und-Sicherheitsregeln"
  "Systemkonfiguration/05-Schemas-und-Mappings"
  "Systembetrieb-und-Indizes"
  "Systembetrieb-und-Indizes/01-Ingest-Protokolle"
  "Systembetrieb-und-Indizes/02-Retrieval-und-Suchindizes"
  "Systembetrieb-und-Indizes/03-Analytics-und-Metriken"
  "Systembetrieb-und-Indizes/04-Healthchecks-und-Status"
  "Systembetrieb-und-Indizes/05-Fehler-und-Wartung"
  "Backups-und-Exporte"
  "Backups-und-Exporte/01-Benutzer-Exporte"
  "Backups-und-Exporte/02-System-Backups"
  "Backups-und-Exporte/03-Berichte-und-Audits"
  "Backups-und-Exporte/04-Migrationen-und-Snapshots"
  "_Vorlagen"
  "_Vorlagen/01-Benutzerstruktur"
  "_Vorlagen/02-Dokumentvorlagen"
  "_Vorlagen/03-Import-Mappings"
  "_Vorlagen/04-Ordnerinfo-Vorlagen"
)

ensure_dir() {
  mkdir -p "$1"
}

zone_for_path() {
  local path="$1"
  case "$path" in
    *"/Dokumente/99-Vertraulich-SACRED"* )
      printf 'SACRED'
      ;;
    "$ROOT_DIR/Benutzer-Ordner/"* )
      if [[ "$path" == "$ROOT_DIR/Benutzer-Ordner/_Muster-Benutzerstruktur"* ]]; then
        printf 'WORKSPACE'
      else
        printf 'FAMILY_PRIVATE'
      fi
      ;;
    * )
      printf 'WORKSPACE'
      ;;
  esac
}

rel_path() {
  local path="$1"
  if [[ "$path" == "$ROOT_DIR" ]]; then
    printf ''
  else
    printf '%s' "${path#"$ROOT_DIR"/}"
  fi
}

folder_role() {
  local rel="$1"
  case "$rel" in
    "" )
      printf '%s' "Hauptwurzel des OpenDisruption-Datenspeichers. Hier werden Benutzerdaten, geteiltes Wissen, Systemkonfiguration, Agentenbetrieb, Importe und Backups getrennt organisiert."
      ;;
    *"/Dokumente/99-Vertraulich-SACRED"* )
      printf '%s' "Hochvertrauliche Dokumentenablage fuer besonders sensible Nachweise, Urkunden, Beziehungs- und Sicherheitsdaten mit maximaler Zurueckhaltung bei Verarbeitung und Zugriff."
      ;;
    *"/13-Digitaler-Zwilling"* )
      printf '%s' "Spezialbereich fuer verdichtete Persona-Modelle, Lebensmuster, Verhaltenssignale und abgeleitete Digital-Twin-Artefakte eines Benutzers."
      ;;
    *"/12-Stammbaum"* )
      printf '%s' "Strukturierter Bereich fuer Familienbeziehungen, genealogische Informationen, Personenstandsdaten und den spaeteren Stammbaum-Aufbau."
      ;;
    *"/02-Chat-Exporte"* )
      printf '%s' "Quellsammlung fuer importierte KI- und Chatverlaeufe, die spaeter extrahiert, semantisch zerlegt und in Wissen oder Memory ueberfuehrt werden."
      ;;
    *"/03-Dokumente-Roh"* )
      printf '%s' "Rohablage fuer noch nicht ausgewertete Dokumente aller Formate, die spaeter per OCR, Parser oder manuell klassifiziert werden."
      ;;
    *"/04-Medien-Roh"* )
      printf '%s' "Rohablage fuer multimodale Medien wie Fotos, Videos, Audio und Musik, bevor sie kuratiert oder analysiert werden."
      ;;
    "Benutzer-Ordner"* )
      printf '%s' "Kanonische Benutzerbereiche fuer personenspezifische Daten, Dokumente, Medien, Wissen, Agentenmemory und Digital-Twin-Aufbau."
      ;;
    "Geteilte-Wissensbasis"* )
      printf '%s' "Gemeinsam nutzbares Wissen ueber Familie, Business, Regeln, Quellen und geteilte Kontexte ausserhalb einzelner Benutzerordner."
      ;;
    "Integrationen-und-Importe"* )
      printf '%s' "Eingangs- und Austauschbereich fuer externe Datenquellen, Exporte, Rohimporte, OCR und Import-Pipelines."
      ;;
    "Orchestrierung-und-Agenten"* )
      printf '%s' "Betriebs- und Konzeptbereich fuer Hermes, KeyCodi, Agentenprofile, Automationen, Audit und Beobachtung."
      ;;
    "Systemkonfiguration"* )
      printf '%s' "Dateibasierte Meta- und Betriebsstruktur fuer Umgebungen, Routing, Modelle, Sicherheitsregeln und Mapping-Konventionen."
      ;;
    "Systembetrieb-und-Indizes"* )
      printf '%s' "Ablage fuer laufende Systemdaten wie Ingest-Protokolle, Suchindizes, Metriken, Healthchecks und Wartungshinweise."
      ;;
    "Backups-und-Exporte"* )
      printf '%s' "Historische Sicherungen, Snapshots, Exporte, Berichte und Migrationsartefakte fuer Wiederherstellung und Nachvollziehbarkeit."
      ;;
    "_Vorlagen"* )
      printf '%s' "Wiederverwendbare Struktur- und Dokumentvorlagen fuer neue Benutzer, Importschemata und Ordnermetadaten."
      ;;
    "eNVenta-Agent"* )
      printf '%s' "Spezialbereich fuer eNVenta-bezogene Hilfe, Exporte, Wissensaufbau und Integrationsmaterial."
      ;;
    *"/00-Inbox"*|*"/01-Schnellerfassung"*|*"/02-Chat-Exporte"*|*"/03-Dokumente-Roh"*|*"/04-Medien-Roh"*|*"/05-Web-und-Research-Importe"*|*"/06-Messenger-und-Soziale-Kanaele"*|*"/07-Review-Queue"*|*"/08-Import-Protokolle"* )
      printf '%s' "Roh- und Eingangsebene fuer neue Informationen, Exporte, Uploads und Material, das erst spaeter klassifiziert wird."
      ;;
    *"/01-Wissen"*|*"/12-Stammbaum"*|*"/13-Digitaler-Zwilling"* )
      printf '%s' "Verdichteter Wissensbereich fuer verifizierte Fakten, Muster, Lebenskontexte, Beziehungen und digitale Zwillinge."
      ;;
    *"/02-Projekte"* )
      printf '%s' "Aktivbereich fuer Vorhaben, Ziele, To-dos, Entscheidungen und operative Umsetzung nach Lebensbereichen."
      ;;
    *"/03-Erfahrungen"*|*"/Tagebuch"*|*"/Selbstreflexion"*|*"/Emotionen-und-Stimmungen"* )
      printf '%s' "Erfahrungs- und Reflexionsraum fuer Tagebuch, Emotionen, Learnings, Coaching und persoenliche Entwicklung."
      ;;
    *"/04-Referenzen"* )
      printf '%s' "Langfristige Referenzen wie Kontakte, Geraete, Services, Vorlagen und Literatur fuer spaetere Wiederverwendung."
      ;;
    *"/05-Archiv"* )
      printf '%s' "Historische Ablage fuer fruehere Stande, Snapshots, ersetzte Inhalte und Exporte."
      ;;
    *"/Dokumente"* )
      printf '%s' "Strukturierte Dokumentenablage fuer Nachweise, Scans, Vertrage, Personenstandsdaten und andere Originale."
      ;;
    *"/Medien"* )
      printf '%s' "Strukturierte Ablage fuer Fotos, Videos, Audio, Musik und kreative Medienartefakte."
      ;;
    *"/agent"*|*"/hermes-runtime"*|*"/memory"*|*"/ingest"*|*"/digital-twin"*|*"/analytics"* )
      printf '%s' "Technische und semantische Runtime-Ablage fuer persoenliche Agenten, Hermes, Memory, Ingest-Pipelines und Digital-Twin-Bausteine."
      ;;
    *"/.obsidian" )
      printf '%s' "Lokale Vault-Konfiguration fuer Obsidian-Ansichten, Plugins und Wissensnavigation."
      ;;
    * )
      printf '%s' "Fachordner innerhalb der OpenDisruption-Datenstruktur zur klaren Trennung von Inhalt, Zweck und spaeterer Automatisierung."
      ;;
  esac
}

folder_contents() {
  local rel="$1"
  case "$rel" in
    "" )
      cat <<EOF
- Benutzerordner
- geteilte Wissens- und Systembereiche
- Import-, Index- und Backup-Ablagen
EOF
      ;;
    *"/Dokumente/99-Vertraulich-SACRED"* )
      cat <<EOF
- hochsensible Dokumente und Nachweise
- personenstands- oder beziehungsrelevante Originale
- Inhalte mit maximalem Schutzbedarf
EOF
      ;;
    *"/13-Digitaler-Zwilling"* )
      cat <<EOF
- verdichtete Persona-Modelle und Profile
- Muster, Gewohnheiten, Vorlieben und Verhaltenshypothesen
- Ableitungen fuer personalisierte Agenten und spaetere Simulation
EOF
      ;;
    *"/12-Stammbaum"* )
      cat <<EOF
- Personen, Beziehungen und Verwandtschaftsverknuepfungen
- Geburts-, Heirats- und Familienkontexte
- Quellen fuer genealogische Rekonstruktion
EOF
      ;;
    *"/02-Chat-Exporte"* )
      cat <<EOF
- rohe Chatverlaeufe verschiedener Anbieter
- JSON-, HTML-, ZIP- oder Text-Exporte
- Import-Metadaten und spaetere Extraktionsnotizen
EOF
      ;;
    *"/03-Dokumente-Roh"* )
      cat <<EOF
- noch nicht ausgewertete Originaldokumente
- Office-, PDF-, Tabellen-, EPUB- und Datenbankdateien
- OCR- und Parser-Eingangsdateien
EOF
      ;;
    *"/04-Medien-Roh"* )
      cat <<EOF
- Foto-, Video-, Audio- und Musikrohmaterial
- Uploads aus Kamera, Apps oder Exporten
- Eingangsdaten vor Verschlagwortung und Kuratierung
EOF
      ;;
    "Benutzer-Ordner"* )
      cat <<EOF
- individuelle Lebensdaten pro Person
- Dokumente, Medien, Projekte, Erfahrungen
- Agentenprofile, Memory und Hermes-Konfiguration
EOF
      ;;
    "Integrationen-und-Importe/01-Chat-Importe"*|*"02-Chat-Exporte"* )
      cat <<EOF
- Chat-Exporte als JSON, HTML, ZIP oder Markdown
- Verlaufssammlungen verschiedener KI-Anbieter
- Mapping- und Extraktionsnotizen
EOF
      ;;
    "Integrationen-und-Importe/02-Dokumenten-Importe"*|*"03-Dokumente-Roh"* )
      cat <<EOF
- PDF, Office, Tabellen, Datenbankdateien, EPUB, Archive
- Rohdokumente vor Extraktion
- OCR- und Konvertierungsnebenprodukte
EOF
      ;;
    "Integrationen-und-Importe/03-Medien-Importe"*|*"04-Medien-Roh"*|*"/Medien"* )
      cat <<EOF
- Fotos, Videos, Audio, Musik, Design- und 3D-Dateien
- Rohmaterial und spaetere kuratierte Ableitungen
- Metadaten und Referenzzuordnungen
EOF
      ;;
    *"/Dokumente"* )
      cat <<EOF
- Originaldokumente und Scans
- Nachweise, Urkunden, Vertraege, Zertifikate
- OCR-Texte, Metadaten und geordnete Ablage
EOF
      ;;
    *"/01-Wissen"* )
      cat <<EOF
- verifizierte Fakten und Notizen
- Muster, Prinzipien, Beziehungen, Timeline
- Verdichtungen fuer semantische Suche und Agenten
EOF
      ;;
    *"/03-Erfahrungen"* )
      cat <<EOF
- Tagebucheintraege und Reflexionen
- Learnings, Retros, emotionale Entwicklung
- Gespraechs- und Coachingnotizen
EOF
      ;;
    *"/agent"* )
      cat <<EOF
- profil.yaml, knowledge_graph.json und Agentenartefakte
- Hermes-Runtime-Konfigurationen und Sitzungen
- Ingest-Queues, Mappingdateien, Analytics und Digital-Twin-Modelle
EOF
      ;;
    * )
      cat <<EOF
- strukturierte Inhalte passend zum Ordnerzweck
- Metadaten, Arbeitsdateien oder spaetere Ableitungen
- Material fuer Menschen und KI-Agenten
EOF
      ;;
  esac
}

folder_human_usage() {
  local rel="$1"
  case "$rel" in
    "" )
      printf '%s' "Menschen nutzen diese Wurzel als Navigationspunkt fuer alle Datenbereiche von OpenDisruption."
      ;;
    *"/00-Inbox"*|*"Integrationen-und-Importe"* )
      printf '%s' "Menschen legen hier neue Dateien zuerst roh ab, bevor sie spaeter sortiert, extrahiert oder bewertet werden."
      ;;
    *"/01-Wissen"* )
      printf '%s' "Menschen dokumentieren hier stabile Erkenntnisse, Biografie, Werte und Zusammenhaenge."
      ;;
    *"/03-Erfahrungen"* )
      printf '%s' "Menschen schreiben hier Tagebuch, Reflexionen, Emotionen und Learnings nieder."
      ;;
    *"/Dokumente"* )
      printf '%s' "Menschen finden und pflegen hier ihre vertraglichen, persoenlichen und vertraulichen Unterlagen."
      ;;
    *"/Medien"* )
      printf '%s' "Menschen verwalten hier Fotos, Videos, Audio und kreative Inhalte in nachvollziehbarer Form."
      ;;
    *"/agent"* )
      printf '%s' "Menschen greifen hier nur gezielt ein, wenn Profil, Memory oder Ingest-Prozesse manuell nachgeschaut werden muessen."
      ;;
    * )
      printf '%s' "Menschen nutzen diesen Ordner fuer den beschriebenen Fachbereich und als stabile semantische Ablage."
      ;;
  esac
}

folder_agent_usage() {
  local rel="$1"
  case "$rel" in
    "" )
      printf '%s' "KI-Agenten lesen diese Wurzel zur Orientierung ueber die gesamte Datenlandschaft und deren Sicherheitsgrenzen."
      ;;
    *"/00-Inbox"*|*"Integrationen-und-Importe"* )
      printf '%s' "KI-Agenten behandeln Inhalte hier als Rohmaterial, fuehren keine vorschnellen Annahmen ein und verschieben erst nach Analyse in Zielbereiche."
      ;;
    *"/01-Wissen"* )
      printf '%s' "KI-Agenten duerfen hier Wissen verdichten, aber nur auf Basis verifizierter Quellen oder bestaetigter Aussagen."
      ;;
    *"/03-Erfahrungen"* )
      printf '%s' "KI-Agenten koennen Muster, Learnings und Reflexionen ableiten, muessen aber persoenliche Aussagen sauber trennen und nicht halluzinieren."
      ;;
    *"/Dokumente"* )
      printf '%s' "KI-Agenten nutzen diesen Bereich fuer Dokumentanalyse, OCR-Nachbereitung, Metadatenpflege und spaetere semantische Einordnung."
      ;;
    *"/Medien"* )
      printf '%s' "KI-Agenten koennen Medien verschlagworten, beschreiben, verknuepfen oder fuer spaetere Suchindizes vorbereiten."
      ;;
    *"/agent"* )
      printf '%s' "KI-Agenten lesen und schreiben hier nur nach klaren Regeln: verifizierte Fakten in Profile/Memory, technische Artefakte in Runtime- und Ingest-Unterordner."
      ;;
    * )
      printf '%s' "KI-Agenten verwenden diesen Ordner als klar abgegrenzten Fachkontext fuer Suche, Strukturierung und spaetere Automatisierung."
      ;;
  esac
}

immediate_children() {
  local path="$1"
  find "$path" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | LC_ALL=C sort
}

should_skip_dir() {
  local path="$1"
  case "$path" in
    */agent/hermes-runtime/.npm*|\
    */agent/hermes-runtime/skills*|\
    */agent/hermes-runtime/workspace*|\
    */agent/hermes-runtime/home*|\
    */agent/hermes-runtime/logs*|\
    */agent/hermes-runtime/hooks*|\
    */agent/hermes-runtime/plans*|\
    */agent/hermes-runtime/platforms*|\
    */agent/hermes-runtime/bin*|\
    */agent/hermes-runtime/skins*|\
    */agent/hermes-runtime/cron* )
      return 0
      ;;
    * )
      return 1
      ;;
  esac
}

related_paths_markdown() {
  local path="$1"
  local rel parent_rel
  rel="$(rel_path "$path")"
  parent_rel="$(dirname "$rel")"
  if [[ "$rel" == "$path" || "$rel" == "." || -z "$rel" ]]; then
    parent_rel=""
  fi

  printf '%s\n' "## Beziehungen und Abhaengigkeiten"
  if [[ -n "$rel" ]]; then
    local parent_display="/"
    if [[ "$parent_rel" != "." && -n "$parent_rel" ]]; then
      parent_display="/${parent_rel#./}"
    fi
    printf '%s\n' "- **Elternbereich:** \`${parent_display}\`"
  else
    printf '%s\n' "- **Elternbereich:** keiner, dies ist die Wurzel"
  fi

  local children=()
  while IFS= read -r child; do
    [[ -n "$child" ]] && children+=("$child")
  done < <(immediate_children "$path")

  if (( ${#children[@]} > 0 )); then
    printf '%s\n' "- **Direkte Unterordner:**"
    local child
    for child in "${children[@]}"; do
      printf '%s\n' "  - \`${child}/\`"
    done
  else
    printf '%s\n' "- **Direkte Unterordner:** keine"
  fi

  case "$rel" in
    "" )
      printf '%s\n' "- **Abhaengig von:** Docker-/Service-Landschaft, Benutzerdaten, Dateisystem als System of Record"
      printf '%s\n' "- **Beeinflusst:** alle Agenten, Ingest, Retrieval, Personalisierung und Backups"
      ;;
    "Benutzer-Ordner"* )
      printf '%s\n' "- **Abhaengig von:** Benutzer-Onboarding, Uploads, persoenlichen Agenten, semantischer Verarbeitung"
      printf '%s\n' "- **Beeinflusst:** Chat-Personalisierung, Dokumentanalyse, Memory, Digital Twin, Familienkontext"
      ;;
    "Integrationen-und-Importe"*|*"00-Inbox"* )
      printf '%s\n' "- **Abhaengig von:** Uploads, Exporte, externe Systeme, OCR/Parser"
      printf '%s\n' "- **Beeinflusst:** spaetere Einordnung in Wissen, Dokumente, Medien, Agent-Memory und Suche"
      ;;
    "Systemkonfiguration"*|*"Orchestrierung-und-Agenten"*|*"Systembetrieb-und-Indizes"* )
      printf '%s\n' "- **Abhaengig von:** Compose, Services, Modelle, Policies und Betriebslogik"
      printf '%s\n' "- **Beeinflusst:** Hermes, KeyCodi, Retrieval, Ingest, Dashboard und Admin"
      ;;
    * )
      printf '%s\n' "- **Abhaengig von:** angrenzenden Fachordnern, manueller Pflege und spaeteren Automationen"
      printf '%s\n' "- **Beeinflusst:** semantische Suche, Wissensverdichtung und nachvollziehbare Ablage"
      ;;
  esac
}

write_folder_info() {
  local path="$1"
  local rel zone
  if should_skip_dir "$path"; then
    return 0
  fi
  if [[ ! -w "$path" ]]; then
    return 0
  fi
  rel="$(rel_path "$path")"
  zone="$(zone_for_path "$path")"

  {
    printf '%s\n' "---"
    printf 'zone: %s\n' "$zone"
    printf 'path: /%s\n' "${rel}"
    printf 'generated_by: bootstrap-global-data-structure.sh\n'
    printf 'version: 1.0\n'
    printf '%s\n\n' "---"
    if [[ -n "$rel" ]]; then
      printf '# ORDNERINFO - /%s\n\n' "$rel"
    else
      printf '# ORDNERINFO - /\n\n'
    fi
    printf '## Zweck\n%s\n\n' "$(folder_role "$rel")"
    printf '## Typische Inhalte\n%s\n\n' "$(folder_contents "$rel")"
    related_paths_markdown "$path"
    printf '\n## Fuer Menschen\n%s\n\n' "$(folder_human_usage "$rel")"
    printf '## Fuer KI-Agenten\n%s\n' "$(folder_agent_usage "$rel")"
  } > "$path/ORDNERINFO.md"
}

main() {
  mkdir -p "$ROOT_DIR"

  local rel
  for rel in "${GLOBAL_STRUCTURE[@]}"; do
    ensure_dir "$ROOT_DIR/$rel"
  done

  if [[ -f "$USER_BOOTSTRAP" ]]; then
    BENUTZER_BASE="$ROOT_DIR/Benutzer-Ordner" bash "$USER_BOOTSTRAP" all-existing >/dev/null
  else
    echo "WARNUNG: user bootstrap script nicht gefunden: $USER_BOOTSTRAP" >&2
  fi

  local dir
  while IFS= read -r dir; do
    write_folder_info "$dir"
  done < <(find "$ROOT_DIR" -type d | LC_ALL=C sort)

  while IFS= read -r dir; do
    rm -f "$dir/ORDNERINFO.md"
  done < <(find "$ROOT_DIR" -type d | LC_ALL=C sort | while IFS= read -r dir; do
    if should_skip_dir "$dir"; then
      printf '%s\n' "$dir"
    fi
  done)

  echo "Globale OpenDisruption-Datenstruktur vorbereitet unter: $ROOT_DIR"
}

main "$@"
