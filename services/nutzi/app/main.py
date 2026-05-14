"""
Nutzi — eNVenta ERP Hilfe-Agent
Persönlicher Assistent für alle eNVenta 4.5 Funktionen.
Port: 8015
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DATA_DIR = Path(__file__).parent.parent / "data"
CHAPTERS_DIR = DATA_DIR / "chapters"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# eNVenta module categories for intro/overview
ENVENTA_MODULES = [
    {
        "name": "Stammdaten",
        "icon": "🗂️",
        "description": "Artikel-, Kunden-, Lieferanten- und Lagerstamm",
        "key_functions": [
            "Artikelstamm anlegen & pflegen (inkl. Stahlprofile, Werkstoff, Norm, kg/m)",
            "Kundenstamm mit Preisgruppen, Rabattgruppen, Zahlungsbedingungen",
            "Lieferantenstamm mit EK-Preisen, Lieferzeiten und Artikel-Verknüpfung",
            "Lagerstamm: Lagerorte, Mindest-/Melde-/Höchstbestand",
            "ABC-Analyse der Artikel",
        ],
        "menu_path": "Stammdaten",
    },
    {
        "name": "Einkauf",
        "icon": "🛒",
        "description": "Bestellungen, Wareneingänge, Lieferantenmanagement",
        "key_functions": [
            "Bestellungen anlegen, genehmigen, versenden (inkl. EDI)",
            "Bestellautomatik aus Meldebeständen",
            "Anfragen an mehrere Lieferanten senden",
            "Wareneingang mit Chargenzuordnung & Zertifikat-Erfassung",
            "Rechnungsprüfung & Eingangsrechnungen buchen",
            "Streckengeschäft (Direktlieferung Lieferant → Kunde)",
        ],
        "menu_path": "Einkauf",
    },
    {
        "name": "Verkauf",
        "icon": "💼",
        "description": "Angebote, Aufträge, Lieferscheine, Rechnungen, CRM",
        "key_functions": [
            "Angebote erstellen mit Staffelpreisen & Zuschlägen",
            "Auftragserfassung mit automatischer Preisfindung",
            "Lieferscheine & Versandpapiere drucken",
            "Ausgangsrechnungen erstellen und archivieren",
            "Retouren und Reklamationsbearbeitung",
            "Kundenindividuelle Preise, Rahmenaufträge, Kontraktpreise",
            "Zuschläge: Kleinstmengen, Expresslieferung, Zuschnitt",
        ],
        "menu_path": "Verkauf",
    },
    {
        "name": "Lagerverwaltung",
        "icon": "🏭",
        "description": "Lager, Inventur, Umlagerungen, Chargen, Kommissionierung",
        "key_functions": [
            "Wareneingang & Auslagerung buchen",
            "Umlagerungen zwischen Lagerorten",
            "Inventur (Liste, Zählung, Abschluss)",
            "Chargenverfolgung von Eingang bis Ausgang",
            "Tourenplanung: Fahrzeuge, Fahrer, Liefertouren",
            "Kommissionierung für Kundenaufträge",
        ],
        "menu_path": "Lager",
    },
    {
        "name": "Finanzbuchhaltung",
        "icon": "📊",
        "description": "Debitoren, Kreditoren, Sachkonten, Zahlungsverkehr",
        "key_functions": [
            "Debitorenbuchhaltung: Zahlungseingänge, Mahnwesen, OP-Verwaltung",
            "Kreditorenbuchhaltung: Zahlungsausgänge, SEPA-Überweisung",
            "Sachkontenbuchhaltung: Kostenstellen, Buchungen",
            "Bankimport (MT940, CAMT.053) & automatischer Kontoabgleich",
            "UStVA, ZM-Meldung, Jahresabschluss",
            "Anlagenbuchhaltung: Abschreibungen, Anlagegüter",
        ],
        "menu_path": "Finanzbuchhaltung",
    },
    {
        "name": "Produktion / Zuschnitt",
        "icon": "⚙️",
        "description": "Fertigungsaufträge, Stücklisten, BDE (für Zuschnittbetriebe relevant)",
        "key_functions": [
            "Betriebsaufträge anlegen & steuern",
            "Stücklisten (BOM) für konfektionierte Produkte",
            "BDE (Betriebsdatenerfassung) für Fertigungszeiten",
            "Sägeschein / Zuschnittauftrag",
        ],
        "menu_path": "Produktion",
    },
    {
        "name": "Archiv & Dokumente",
        "icon": "📁",
        "description": "Automatische Belegarchivierung, DMS-Anbindung (Proxess)",
        "key_functions": [
            "Automatisches Archivieren von Rechnungen, Lieferscheinen, Bestellungen",
            "Proxess DMS-Anbindung",
            "Dokumente an Artikel, Kunde, Lieferant hinterlegen",
            "Suche und Abruf archivierter Belege",
        ],
        "menu_path": "Archiv",
    },
    {
        "name": "EDI / Schnittstellen",
        "icon": "🔗",
        "description": "Elektronischer Datenaustausch, Imports/Exports",
        "key_functions": [
            "ORDERS/ORDRSP (elektronische Bestellungen/Bestätigungen)",
            "DESADV (Lieferavis)",
            "INVOIC (elektronische Rechnung)",
            "CSV-Import für Artikel, Preise, Bestände",
            "eGate Beratungsassistent",
        ],
        "menu_path": "EDI",
    },
    {
        "name": "Reporting & Auswertungen",
        "icon": "📈",
        "description": "Berichte, Crystal Reports, Dashboards",
        "key_functions": [
            "Standard-Reports: Umsatz, Lagerbestand, Offene Posten",
            "Crystal Reports für individuelle Layouts",
            "Statistiken: Kunden-, Artikel-, Lieferantenstatistik",
            "ABC-Analyse, Bewegungsauswertungen",
            "Export nach Excel / CSV",
        ],
        "menu_path": "Auswertungen",
    },
    {
        "name": "Administration",
        "icon": "🔧",
        "description": "Benutzer, Berechtigungen, System, Nummernkreise",
        "key_functions": [
            "Benutzerverwaltung & Berechtigungsgruppen",
            "Nummernkreise konfigurieren (Belege, Artikel, Kunden)",
            "E-Mail-Versand einrichten (SMTP)",
            "Druckereinstellungen & Formularlayouts",
            "Systemparameter & Grundeinstellungen",
            "2-Faktor-Authentifizierung",
        ],
        "menu_path": "Administration",
    },
]

INTRO_TEXT = """Hallo! Ich bin **Nutzi** 👋 — dein persönlicher eNVenta ERP-Experte bei Sülzle Nutzeisen.

Ich kenne das **eNVenta 4.5 ERP-System** vollständig und habe **4.559 Hilfekapitel** aus der offiziellen Online-Hilfe indexiert.

**Was ich für dich tun kann:**
🔍 Präzise Antworten auf deine eNVenta-Fragen mit konkreten Menüpfaden
📚 Kapitel und Anleitungen aus der offiziellen Hilfe abrufen
🗂️ Den kompletten Artikelstamm von Nutzeisen anlegen (Stahl, Profile, Werkstoff, Normen)
⚡ Schnelle Keyword-Suche in 3.563 Themen-Kategorien
🤖 KI-gestützte Antworten via Ollama (Deutsch, praxisnah)

**Einfach fragen — ich antworte auf Deutsch, präzise und mit konkreten Schritten!**"""

app = FastAPI(
    title="Nutzi — eNVenta ERP Assistent",
    description="Vollumfängliche Hilfe für das eNVenta 4.5 ERP-System von Sülzle Nutzeisen",
    version="1.1.0",
)
def _cors_kwargs() -> dict:
    raw = os.getenv("KIROBI_PUBLIC_ORIGINS", "").strip()
    if raw:
        origins = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
        return {"allow_origins": origins}
    pattern = (
        r"^https?://("
        r"localhost(:\d+)?|127\.0\.0\.1(:\d+)?|"
        r"[a-zA-Z0-9-]+\.local(:\d+)?|"
        r"10\.\d+\.\d+\.\d+(:\d+)?|"
        r"192\.168\.\d+\.\d+(:\d+)?|"
        r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+(:\d+)?|"
        r"100\.(6[4-9]|[7-9]\d|1[0-1]\d|12[0-7])\.\d+\.\d+(:\d+)?"
        r")$"
    )
    return {"allow_origin_regex": pattern}


app.add_middleware(
    CORSMiddleware,
    **_cors_kwargs(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@lru_cache(maxsize=1)
def load_master_index() -> dict:
    path = DATA_DIR / "master_index.json"
    if not path.exists():
        return {"chapters": [], "total_chapters": 0}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_topic_lookup() -> dict:
    path = DATA_DIR / "topic_lookup.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_chapter(chapter_id: str) -> str:
    path = CHAPTERS_DIR / f"{chapter_id}.md"
    if not path.exists():
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def is_generic_chapter(chap: dict) -> bool:
    """Returns True if chapter has a generic auto-generated title with no topics."""
    title = chap.get("title", "")
    return title.startswith("Kapitel ") and not chap.get("topics")


def search_chapters(query: str, max_results: int = 10, skip_generic: bool = True) -> list[dict]:
    """Keyword search across chapter titles and topics. Prefers real titles over generic ones."""
    query_lower = query.lower()
    terms = [t for t in query_lower.split() if len(t) > 2]
    if not terms:
        terms = query_lower.split()
    results = []
    index = load_master_index()

    for chap in index.get("chapters", []):
        if skip_generic and is_generic_chapter(chap):
            continue
        title = chap.get("title", "").lower()
        topics_str = " ".join(chap.get("topics", [])).lower()
        combined = title + " " + topics_str
        # Score: title match counts double
        title_score = sum(2 for t in terms if t in title)
        topic_score = sum(1 for t in terms if t in topics_str)
        score = title_score + topic_score
        if score > 0:
            results.append({**chap, "_score": score})

    results.sort(key=lambda x: -x["_score"])
    # If no real results, retry including generic chapters
    if not results and skip_generic:
        return search_chapters(query, max_results, skip_generic=False)
    return results[:max_results]


def search_full_text(query: str, max_results: int = 5, skip_generic: bool = True) -> list[dict]:
    """Search inside chapter content (slower but more thorough)."""
    query_lower = query.lower()
    terms = [t for t in query_lower.split() if len(t) > 2]
    if not terms:
        terms = query_lower.split()
    results = []
    index = load_master_index()

    for chap in index.get("chapters", []):
        if skip_generic and is_generic_chapter(chap):
            continue
        chap_id = chap.get("chapter_id")
        if not chap_id:
            continue
        content = read_chapter(chap_id).lower()
        score = sum(content.count(t) for t in terms)
        if score > 0:
            first_term = terms[0]
            pos = content.find(first_term)
            snippet = content[max(0, pos - 80): pos + 200].strip() if pos >= 0 else ""
            snippet = re.sub(r"\s+", " ", snippet)
            results.append({**chap, "_score": score, "snippet": f"...{snippet}..."})

    results.sort(key=lambda x: -x["_score"])
    return results[:max_results]


# ─── Models ──────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str
    chapter_ids: Optional[list[str]] = None
    max_context_chapters: int = 3
    use_llm: bool = True


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]
    model: str


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Nutzi API — eNVenta ERP Assistent."""
    index = load_master_index()
    return {
        "agent": "Nutzi",
        "description": "eNVenta 4.5 ERP Hilfe-Agent für Sülzle Nutzeisen",
        "version": "1.1.0",
        "total_chapters": index.get("total_chapters", 0),
        "endpoints": ["/health", "/intro", "/search", "/ask", "/topics", "/chapter/{id}", "/modules", "/artikelstamm/guide", "/stats"],
    }


@app.get("/health")
def health():
    index = load_master_index()
    return {
        "status": "ok",
        "agent": "Nutzi",
        "version": "1.1.0",
        "total_chapters": index.get("total_chapters", 0),
        "data_dir": str(DATA_DIR),
    }


@app.get("/intro")
def intro():
    """Nutzi stellt sich vor — alle Bereiche und Fähigkeiten."""
    index = load_master_index()
    chaps = index.get("chapters", [])
    real_chaps = [c for c in chaps if not is_generic_chapter(c)]
    lookup = load_topic_lookup()

    return {
        "agent": "Nutzi",
        "version": "1.1.0",
        "intro_text": INTRO_TEXT,
        "knowledge_base": {
            "total_chapters": len(chaps),
            "searchable_chapters": len(real_chaps),
            "total_topics": len(lookup),
            "source": "eNVenta 4.5 Online-Hilfe (Nissen & Velten Software GmbH)",
        },
        "modules": [
            {
                "name": m["name"],
                "icon": m["icon"],
                "description": m["description"],
                "key_functions_count": len(m["key_functions"]),
                "menu_path": m["menu_path"],
            }
            for m in ENVENTA_MODULES
        ],
        "quick_start": [
            "Stelle mir eine Frage: POST /ask {\"question\": \"Wie lege ich einen Artikel an?\"}",
            "Suche nach Themen: GET /search?q=Artikelstamm",
            "Volltext-Suche: GET /search?q=Chargenverwaltung&full_text=true",
            "Modul-Übersicht: GET /modules",
            "Artikelstamm-Leitfaden: GET /artikelstamm/guide",
        ],
        "special_expertise": [
            "Artikelstamm-Anlage für Stahl (Werkstoff, Norm, Profil, kg/m)",
            "Chargen- und Zertifikatsverwaltung",
            "Preisfindung mit Staffeln, Zuschlägen und Rabattgruppen",
            "Zuschnitt- und Tourenplanung",
            "Import/Export und EDI-Schnittstellen",
            "Berechtigungen und Administration",
        ],
        "how_to_ask_via_telegram": [
            "\"Nutzi, wie lege ich einen neuen Artikel an?\"",
            "\"Nutzi, erkläre mir die Chargenverwaltung\"",
            "\"Nutzi, zeig mir den Artikelstamm-Leitfaden\"",
            "\"Nutzi, suche nach Tourenplanung\"",
            "\"Nutzi, was kann eNVenta im Bereich Einkauf?\"",
        ],
    }


@app.get("/topics")
def list_topics(limit: int = Query(100, le=500)):
    """Liste aller eNVenta Hilfe-Themen."""
    lookup = load_topic_lookup()
    topics = [
        {"label": k, "chapters": v.get("chapters", []), "children": v.get("children", [])}
        for k, v in lookup.items()
    ]
    return {"total": len(topics), "topics": topics[:limit]}


@app.get("/stats")
def stats():
    """Statistiken über die Nutzi-Wissensdatenbank."""
    index = load_master_index()
    chaps = index.get("chapters", [])
    lookup = load_topic_lookup()
    real = [c for c in chaps if not is_generic_chapter(c)]
    generic = [c for c in chaps if is_generic_chapter(c)]
    sizes = [c.get("char_count", 0) for c in chaps if c.get("char_count")]
    avg_size = int(sum(sizes) / len(sizes)) if sizes else 0
    return {
        "total_chapters": len(chaps),
        "searchable_chapters": len(real),
        "generic_chapters": len(generic),
        "total_topics": len(lookup),
        "avg_chapter_chars": avg_size,
        "modules": len(ENVENTA_MODULES),
        "ollama_model": OLLAMA_MODEL,
        "ollama_url": OLLAMA_URL,
    }


@app.get("/search")
def search(
    q: str = Query(..., description="Suchbegriff"),
    full_text: bool = False,
    limit: int = 10,
    include_generic: bool = False,
):
    """Suche nach eNVenta Themen oder Inhalten."""
    if not q.strip():
        raise HTTPException(400, "Suchbegriff darf nicht leer sein")

    skip_generic = not include_generic
    results = search_chapters(q, limit, skip_generic=skip_generic)
    if not results and full_text:
        results = search_full_text(q, limit, skip_generic=skip_generic)
    elif full_text and len(results) < 3:
        ft_results = search_full_text(q, limit - len(results), skip_generic=skip_generic)
        seen = {r.get("chapter_id") for r in results}
        results += [r for r in ft_results if r.get("chapter_id") not in seen]

    return {
        "query": q,
        "results_count": len(results),
        "full_text_used": full_text,
        "results": [
            {
                "chapter_id": r.get("chapter_id"),
                "title": r.get("title"),
                "topics": r.get("topics", []),
                "relevance": r.get("_score", 0),
                "snippet": r.get("snippet", ""),
            }
            for r in results
        ],
    }


@app.get("/chapter/{chapter_id}")
def get_chapter(chapter_id: str):
    """Vollständigen Inhalt eines Kapitels abrufen."""
    content = read_chapter(chapter_id)
    if not content:
        raise HTTPException(404, f"Kapitel {chapter_id} nicht gefunden")

    index = load_master_index()
    chap_meta = next((c for c in index.get("chapters", []) if c.get("chapter_id") == chapter_id), {})

    return {
        "chapter_id": chapter_id,
        "title": chap_meta.get("title", f"Kapitel {chapter_id}"),
        "topics": chap_meta.get("topics", []),
        "content": content,
        "char_count": len(content),
    }


@app.post("/ask", response_model=AskResponse)
async def ask_nutzi(req: AskRequest):
    """
    Stelle Nutzi eine Frage zu eNVenta. Nutzt Kontext aus der Onlinehilfe
    und beantwortet auf Deutsch mit Ollama.
    """
    # Find relevant chapters
    if req.chapter_ids:
        sources_meta = []
        context_parts = []
        for cid in req.chapter_ids[:req.max_context_chapters]:
            content = read_chapter(cid)
            if content:
                index = load_master_index()
                meta = next((c for c in index.get("chapters", []) if c.get("chapter_id") == cid), {})
                sources_meta.append({"chapter_id": cid, "title": meta.get("title", cid)})
                context_parts.append(f"### {meta.get('title', cid)}\n{content[:2000]}")
    else:
        results = search_chapters(req.question, req.max_context_chapters)
        if not results:
            results = search_full_text(req.question, req.max_context_chapters)
        sources_meta = [{"chapter_id": r.get("chapter_id"), "title": r.get("title")} for r in results]
        context_parts = []
        for r in results:
            cid = r.get("chapter_id")
            if cid:
                content = read_chapter(cid)
                if content:
                    context_parts.append(f"### {r.get('title')}\n{content[:2000]}")

    context = "\n\n".join(context_parts) if context_parts else "Kein passender Kontext gefunden."

    system_prompt = """Du bist Nutzi, der persönliche eNVenta ERP-Experte von Sven Darusi bei Sülzle Nutzeisen.
Du kennst das eNVenta 4.5 ERP-System vollständig und hilfst dabei:
- Den Artikelstamm von Nutzeisen anzulegen und zu pflegen (Stahl, Profile, Werkstoff S235/S355, Normen, kg/m)
- Alle Module vollumfänglich zu nutzen (Einkauf, Verkauf, Lager, Fibu, CRM etc.)
- Sülzle Nutzeisen auf den neuesten Stand der Technik zu bringen
- Prozesse zu optimieren und zu digitalisieren

Antworte IMMER auf Deutsch, präzise, praxisorientiert und mit konkreten Menüpfaden.
Beziehe dich auf konkrete Menüpfade und Felder in eNVenta wenn möglich.
Wenn du eine Schritt-für-Schritt-Anleitung geben kannst, tue es.
Halte Antworten kompakt — maximal 5-8 Schritte oder 3 Absätze."""

    user_prompt = f"""Frage: {req.question}

Relevante eNVenta Hilfe-Inhalte:
{context}

Bitte beantworte die Frage präzise und praxisorientiert für den Einsatz bei Sülzle Nutzeisen."""

    # Return context-only if LLM disabled
    if not req.use_llm:
        return AskResponse(
            answer=context[:2000] if context_parts else "Kein Kontext gefunden.",
            sources=sources_meta,
            model="context-only",
        )

    # Call Ollama
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("message", {}).get("content", "Keine Antwort vom Modell erhalten.")
            model_used = data.get("model", OLLAMA_MODEL)
    except httpx.TimeoutException:
        answer = f"⏱️ Ollama-Timeout. Kontext aus Hilfe:\n\n{context[:1500]}"
        model_used = "timeout-fallback"
    except Exception as e:
        answer = f"⚠️ LLM nicht verfügbar ({type(e).__name__}).\n\nKontext aus Hilfe:\n\n{context[:1500]}"
        model_used = "error-fallback"

    return AskResponse(answer=answer, sources=sources_meta, model=model_used)


@app.get("/modules")
def list_modules(detail: bool = False):
    """Gibt alle Hauptmodule von eNVenta zurück."""
    if detail:
        return {"modules": ENVENTA_MODULES, "total": len(ENVENTA_MODULES)}
    return {
        "modules": [
            {
                "name": m["name"],
                "icon": m["icon"],
                "description": m["description"],
                "menu_path": m["menu_path"],
            }
            for m in ENVENTA_MODULES
        ],
        "total": len(ENVENTA_MODULES),
    }


@app.get("/artikelstamm/guide")
def artikelstamm_guide():
    """Vollständiger Leitfaden zum Anlegen des Artikelstamms für Nutzeisen."""
    guide = {
        "title": "Artikelstamm anlegen — Leitfaden für Sülzle Nutzeisen",
        "phases": [
            {
                "phase": 1,
                "name": "Grundstruktur vorbereiten",
                "steps": [
                    "Artikelgruppen definieren (Roh-, Hilfs-, Betriebsstoffe, Handelswaren)",
                    "Lagergruppen anlegen (Haupt-, Außen-, Kommissionslager)",
                    "Maßeinheiten konfigurieren (kg, m, Stk, Bund, Coil)",
                    "Warengruppen / Produkthierarchien einrichten",
                    "Mehrwertsteuerschlüssel prüfen (Standard 19%, ermäßigt 7%)",
                ],
            },
            {
                "phase": 2,
                "name": "Artikelstamm-Felder befüllen",
                "steps": [
                    "Artikelnummer (intern + Lieferantennummer)",
                    "Bezeichnung 1 + 2 (Werkstoff, Abmessung, Norm)",
                    "Artikelgruppe + Warengruppe zuweisen",
                    "Einheit (VKE = Verkaufseinheit, LEH = Lagereinheit)",
                    "Gewicht (brutto/netto) + Maße",
                    "EAN/GTIN-Code falls vorhanden",
                    "Mindestbestand + Meldebestand + Höchstbestand",
                    "Lieferzeit + Bestellmenge",
                    "VK-Preise + EK-Listenpreise",
                    "Lieferanten-Artikel verknüpfen",
                ],
            },
            {
                "phase": 3,
                "name": "Stahlspezifische Attribute (Nutzeisen)",
                "steps": [
                    "Werkstoffbezeichnung (z.B. S235JR, S355J2, 1.0038)",
                    "DIN/EN-Norm hinterlegen (z.B. EN 10025, DIN 1025)",
                    "Profilart (Flachstahl, Rundstahl, Winkel, U-Profil, IPE, HEA, T-Stahl)",
                    "Chargen-/Zertifikatspflicht aktivieren",
                    "Oberfläche (blank, verzinkt, lackiert, geschliffen)",
                    "Länge/Gewicht Beziehungen (kg/m) für Längenware",
                ],
            },
            {
                "phase": 4,
                "name": "Preisfindung konfigurieren",
                "steps": [
                    "Preisgruppen anlegen (A, B, C Kunden oder Branche)",
                    "Staffelpreise nach Menge hinterlegen",
                    "Rabattgruppen + Rabattstaffeln definieren",
                    "Zuschläge einrichten (Kleinstmengen, Expresslieferung, Zuschnitt)",
                    "Währungen falls Export vorhanden",
                ],
            },
            {
                "phase": 5,
                "name": "Validierung & Go-Live",
                "steps": [
                    "Test-Bestellung mit neuem Artikel anlegen",
                    "Lagerbuchung prüfen",
                    "Rechnungsdruck testen",
                    "Bestandsmengen importieren (Anfangsbestand via CSV)",
                    "ABC-Analyse nach erstem Monat durchführen",
                ],
            },
        ],
        "steel_categories": {
            "Flacherzeugnisse": ["Blech", "Band", "Coil", "Tränenblech"],
            "Langprodukte": ["Flachstahl", "Rundstahl", "Vierkantstahl", "Sechskantstahl"],
            "Profile": ["Winkelstahl", "U-Stahl", "T-Stahl", "IPE", "HEA", "HEB", "HEM"],
            "Rohre": ["Rundrohre", "Rechteckrohre", "Quadratrohre"],
            "Sonstiges": ["Schrauben", "Nägel", "Verbindungsmittel", "Dienstleistungen"],
        },
        "units": {
            "KG": "Kilogramm (Basiseinheit Stahl)",
            "TO": "Tonne (= 1000 kg)",
            "STK": "Stück",
            "M": "Meter (Längenware)",
            "M2": "Quadratmeter (Blech)",
            "BND": "Bund",
            "CL": "Coil",
        },
        "important_fields": {
            "Pflichtfelder": ["Artikelnummer", "Bezeichnung", "Artikelgruppe", "Hauptlieferant", "Einheit"],
            "Empfohlen": ["Gewicht", "Mindestbestand", "Lieferzeit", "EAN", "Warengruppe"],
            "Nutzeisen-spezifisch": ["Werkstoff", "Norm", "Profilart", "kg/m", "Länge"],
        },
    }
    return guide



