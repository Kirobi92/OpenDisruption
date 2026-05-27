# 05 — LUKI MVP Definition

**Datum:** 2026-05-26 · **MVP-Name:** LUKI Knowledge v0.1 — *Lokaler ERP-Wissensassistent*

## 1. Problem

Mittelständische Unternehmen (Pilot: Nutzeisen) brauchen einen lokalen, datenschutzkonformen Wissensassistenten, der ERP-/eNVenta-/Prozess-Wissen aus existierenden Dokumenten beantworten kann — mit nachvollziehbarer Quellenangabe, ohne ERP-Schreibrechte, ohne Cloud-LLM, ohne dass Fragen das Haus verlassen.

## 2. Zielnutzer (MVP)

- Sven (Owner, Demo-Vorführung, Eval)
- 2–3 Pilot-Anwender bei Nutzeisen (interne Power-User, Lager/Einkauf/IT)
- Niemand außerhalb des Pilot-Kontexts.

## 3. Scope (drin)

1. **Dokumenten-Ingest** für PDF, DOCX, MD, TXT, HTML aus `products/luki/source-docs/`.
2. **Bereinigung** (Whitespace, Header/Footer-Stripping, Tabellen-Erhalt minimal).
3. **Chunking** mit Quellmetadaten (Datei, Seite, Abschnitt, sha256).
4. **Indexierung** in eigene Qdrant-Collection `luki_knowledge_v1` (separat von KIROBI-Collections).
5. **Retrieval** (BM25 + Embedding-Hybrid optional; MVP: nur Embedding) → Top-K + Re-Ranking minimal.
6. **Antwort-Generierung** lokal via Ollama, mit erzwungener Quellen-Ausgabe.
7. **„Ich weiß es nicht"-Verhalten:** Wenn Top-K-Score < Threshold ODER LLM keine belegbare Antwort hat → explizite Ablehnung mit Hinweis auf fehlende Quelle.
8. **Audit-Log** (append-only JSONL): Zeit, User-Hash, Frage-Hash, Top-K-Quellen-IDs, Antwort-Hash, LLM-Modell, Token-Counts.
9. **Zugang:** EIN Kanal im MVP — Empfehlung: minimale HTTP-API + simples Web-UI (kein Telegram im MVP, weil Schutz/Authentifizierung schwerer). Wenn Telegram bereits stabil als Hermes-Gateway läuft, kann ein dedizierter `LUKI`-Bot mit User-Whitelist genutzt werden.
10. **Eval-Set:** 50 Testfragen aus Nutzeisen-Material mit Goldset (erwartete Quelle).
11. **Evaluationsbericht** als Markdown: Treffer-Rate Top-1, Top-3, Halluzinations-Quote, Verweigerungs-Quote.
12. **Doku:** Installation, Start/Stop, Backup/Restore, Security-Hinweise, Quellpflicht-Policy.

## 4. Non-Scope (explizit nicht)

- ❌ Schreibender ERP-Zugriff (kein Anlegen/Ändern/Löschen in eNVenta)
- ❌ Multi-Tenant (keine Kunden-Trennung in einer Instanz)
- ❌ Billing/Lizenzierung
- ❌ Komplexes Dashboard
- ❌ Voice/Avatar
- ❌ Agentenschwarm/autonome Ketten
- ❌ Webshop-/3D-Druck-Integration
- ❌ Marketing-Automation
- ❌ WhatsApp/Teams/eNVenta-Middleware (eigene Roadmap-Phase)
- ❌ Cloud-LLM-Aufrufe
- ❌ Indexierung privater KIROBI-Daten

## 5. Datenfluss

```
[Quelldokument] ── manuell/scriptweise nach products/luki/source-docs/
   │
   ▼
[ingest CLI] ── extract (pypdfium/textract) ── normalize ── chunk(size=800, overlap=150)
   │                                                              │
   │                                                              ▼
   │                                                   [metadata: file, page, sha, section]
   ▼
[embed]  ── Ollama Embedding-Modell (z.B. nomic-embed-text)
   │
   ▼
[qdrant upsert into luki_knowledge_v1]
   │
========= Indexierung Ende =========

[Anfrage] ── HTTP API / Web-UI ── policy_gate (LUKI-Zone)
   │
   ▼
[retrieve top-K] (k=8, score>=θ)
   │
   ▼
[answer]  Ollama LLM mit System-Prompt:
   "Antworte nur basierend auf den Quellen.
    Wenn keine Quelle ausreicht: 'Ich weiß es nicht.'
    Jede Aussage mit [Quelle-ID]"
   │
   ▼
[audit-log JSONL] ── Antwort an User mit Quellenliste
```

## 6. Service-Liste (LUKI-MVP-Stack)

| Service | Image/Stack | Port | Speicherort |
|---|---|---|---|
| `luki-api` | eigenes FastAPI-Image (Python 3.12) | 127.0.0.1:8410 | `infra/hermes-runtime`-unabhängig |
| `luki-worker` | gleicher Image, andere Entry-Cmd: Ingest-Watcher | – | – |
| `luki-ui` | minimaler SvelteKit oder reines HTML/HTMX | 127.0.0.1:8411 | – |
| (geteilt) `qdrant` | aus `infra/qdrant` | 127.0.0.1:6333 | shared/qdrant/collections/luki_knowledge_v1 |
| (geteilt) `ollama` | aus `infra/ollama` | 11434 | shared/ollama/models |
| `caddy` Route | `/luki` → 8410/8411 mit Basic-Auth | – | – |

## 7. Datenhaltung

- **Quelldokumente (read-only Master):** `products/luki/source-docs/` im Repo (binär versioniert mit Git-LFS oder ausgelagert in `/Datenspeicher/OpenDisruption-Data/luki/source-docs/` mit Hash-Manifest im Repo). MVP: Hash-Manifest im Repo, Dateien außerhalb.
- **Ingest-Staging:** `/Datenspeicher/OpenDisruption-Data/luki/ingest-staging/<batch-id>/` (extract+chunks).
- **Vektor-Daten:** `…/shared/qdrant/collections/luki_knowledge_v1`.
- **Audit-Log:** `…/luki/audit/YYYY-MM/luki-audit-YYYY-MM-DD.jsonl` (append-only, daily rotate, restic-backupd).
- **Evals:** `…/luki/evals/<run-id>/{questions.json, predictions.json, report.md}`.

## 8. Config

- `products/luki/config/luki.yaml`:
  - `embedding_model`, `llm_model`, `top_k`, `score_threshold`, `chunk_size`, `chunk_overlap`
  - `policy: { zone: LUKI_BUSINESS, allow_cloud: false }`
  - `audit: { enabled: true, hash_user: true, hash_question: true }`
- `/Datenspeicher/OpenDisruption-Data/secrets/luki.env`:
  - `LUKI_API_BASIC_AUTH_USER`, `LUKI_API_BASIC_AUTH_PASSWORD_HASH`, `OLLAMA_URL`, `QDRANT_URL`

## 9. Security

- Kein Zugriff auf KIROBI-Collections (Qdrant-Auth oder Collection-Allowlist erzwingen).
- Caddy-Route `/luki` mit Basic-Auth + Tailscale-Bindung (kein offenes LAN).
- Audit-Log ohne Klartext-Frage/Antwort (nur Hashes); Mapping-Tabelle Hash→Klartext nur lokal in `/Datenspeicher/OpenDisruption-Data/luki/audit/_unhashed/` (chmod 600, **nicht** ins Repo, **nicht** in Backups die das Haus verlassen).
- Quellen-IDs sind Dateipfade + Seitenzahl; keine PII-Exfiltration über LLM-Prompt.
- Pre-Ingest-Filter: PII-Erkennung (z.B. simple Regex für IBAN/E-Mail/Telefon) → Warnung im Eval-Report, kein automatisches Maskieren im MVP.

## 10. Logging

- API-Logs: nur Request-ID, Zeit, Latenz, Status. Keine Frage/Antwort im Plain-Log.
- Worker-Logs: Datei + Chunk-Anzahl, keine Inhalts-Snippets.
- Ollama-Logs: Standard-Level (kein Prompt-Dump in Produktion).

## 11. Evaluation

- **Goldset:** 50 Fragen aus Nutzeisen-Material (Owner: Sven + Pilot-User), Format:
  ```json
  {"id":"q01","question":"…","expected_source":"datei.pdf#page=42","expected_concepts":["…"]}
  ```
- **Metriken:**
  - Source-Top1-Hit (Quelle stimmt überein)
  - Source-Top3-Hit
  - Refusal-Rate (`Ich weiß es nicht`-Anteil bei Fragen ohne Quelle — sollte hoch sein)
  - Halluzinations-Rate (Antworten mit Quellenangabe, deren Quelle die Aussage nicht stützt — manuelles Spot-Check)
- **Akzeptanzschwellen:** Top1≥0.50, Top3≥0.75, Halluzinations-Rate≤0.10, Refusal-Rate bei „bekannten Lücken"≥0.80.

## 12. Demo-Szenario (Nutzeisen)

1. 10 Beispiel-Fragen aus IST-Prozessanalyse (Lager, Wareneingang, Artikelstamm, Bestand, KG/STK).
2. Live-Demo: Frage stellen → Antwort mit klickbarer Quelle (Dateiname + Seite).
3. Negative-Demo: Frage außerhalb des Materials → System sagt „Ich weiß es nicht".
4. Audit-Log-Auszug zeigen (ohne Klartext-Frage).
5. Restic-Restore-Probelauf für Kunden-Comfort.

## 13. Akzeptanzkriterien (messbar)

- [ ] 50 Eval-Fragen mit Goldset existieren in `products/luki/evals/v1/questions.json`
- [ ] Eval-Run produziert `report.md` mit allen Metriken
- [ ] Top1≥0.50 erreicht
- [ ] Jede Antwort enthält mindestens eine Quelle ODER explizite Verweigerung
- [ ] Kein Eval-Run führt zu Zugriff auf KIROBI-Collections (Test: Whitelist-Check)
- [ ] Audit-Log pro Anfrage existiert und ist parseable (`jq` over JSONL)
- [ ] Start/Stop dokumentiert (`docs/runbooks/luki-start-stop.md`)
- [ ] Backup-Restore-Test dokumentiert + einmal erfolgreich durchgeführt
- [ ] Demo-Skript für Nutzeisen existiert (`products/luki/runbooks/demo-nutzeisen.md`)
- [ ] Secrets ausschließlich in `/Datenspeicher/OpenDisruption-Data/secrets/luki.env`, niemals im Repo
- [ ] LAN-Exposition nur via Tailscale-+-Caddy-+-BasicAuth verifiziert (Port-Scan-Test)

## 14. Risiken (MVP)

| Risiko | Wahrscheinlichkeit | Auswirkung | Mitigation |
|---|---|---|---|
| Halluzinationen trotz Quellenpflicht | MITTEL | Vertrauensverlust beim Pilot | strenger System-Prompt, Eval-Cycle, Refusal-Default |
| Embedding-Modell zu schwach für DE-Fachbegriffe | MITTEL | schlechte Recall | mehrere Modelle vergleichen (nomic-embed-text vs. bge-m3) |
| Qdrant-Cross-Collection-Lese-Bug | NIEDRIG | KIROBI-Leak | Whitelist-Test im CI |
| PDF-Extraction-Qualität (Tabellen, Scan-PDFs) | HOCH | Lücken im Wissen | OCR-Fallback dokumentieren, im Audit kennzeichnen |
| Pilot-Nutzer setzen falsche Erwartungen (autonomes ERP) | MITTEL | Erwartungsmanagement-Problem | Demo-Skript klar mit Non-Scope-Liste |

## 15. Spätere Operatoren (nach MVP)

- **LUKI Process Operator** — Schritt-für-Schritt-Anleitungen zu eNVenta-Prozessen (read-only, mit Screenshots).
- **LUKI Document Operator** — Klassifikation + Verschlagwortung neuer Dokumente, Routing nach Proxess/DMS.
- **LUKI Artikel Operator** — Stammdaten-Vorschläge (KG/STK-Einheiten, Synonymliste).
- **LUKI Wareneingang Operator** — Scanner-/Waage-Workflow-Begleiter.
- **LUKI Middleware** — WhatsApp/Teams/eNVenta-Brücke (eigener Go/No-Go nach MVP).
