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

app = FastAPI(
    title="Nutzi — eNVenta ERP Assistent",
    description="Vollumfängliche Hilfe für das eNVenta 4.5 ERP-System von Sülzle Nutzeisen",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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


def search_chapters(query: str, max_results: int = 10) -> list[dict]:
    """Simple keyword search across chapter titles and topics."""
    query_lower = query.lower()
    terms = query_lower.split()
    results = []
    index = load_master_index()

    for chap in index.get("chapters", []):
        title = chap.get("title", "").lower()
        topics_str = " ".join(chap.get("topics", [])).lower()
        combined = title + " " + topics_str

        # Score: count how many terms match
        score = sum(1 for t in terms if t in combined)
        if score > 0:
            results.append({**chap, "_score": score})

    results.sort(key=lambda x: -x["_score"])
    return results[:max_results]


def search_full_text(query: str, max_results: int = 5) -> list[dict]:
    """Search inside chapter content (slower but more thorough)."""
    query_lower = query.lower()
    terms = query_lower.split()
    results = []
    index = load_master_index()
    chapters = index.get("chapters", [])

    for chap in chapters:
        chap_id = chap.get("chapter_id")
        if not chap_id:
            continue
        content = read_chapter(chap_id).lower()
        score = sum(content.count(t) for t in terms)
        if score > 0:
            # Get a snippet
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


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]
    model: str


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    index = load_master_index()
    return {
        "status": "ok",
        "agent": "Nutzi",
        "total_chapters": index.get("total_chapters", 0),
        "data_dir": str(DATA_DIR),
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


@app.get("/search")
def search(q: str = Query(..., description="Suchbegriff"), full_text: bool = False, limit: int = 10):
    """Suche nach eNVenta Themen oder Inhalten."""
    if not q.strip():
        raise HTTPException(400, "Suchbegriff darf nicht leer sein")

    results = search_chapters(q, limit)
    if not results and full_text:
        results = search_full_text(q, limit)

    return {
        "query": q,
        "results_count": len(results),
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
- Den Artikelstamm von Nutzeisen anzulegen und zu pflegen
- Alle Module vollumfänglich zu nutzen (Einkauf, Verkauf, Lager, Fibu, CRM etc.)
- Sülzle Nutzeisen auf den neuesten Stand der Technik zu bringen
- Prozesse zu optimieren und zu digitalisieren

Antworte immer auf Deutsch, präzise und praxisorientiert.
Beziehe dich auf konkrete Menüpfade und Felder in eNVenta wenn möglich.
"""

    user_prompt = f"""Frage: {req.question}

Relevante eNVenta Hilfe-Inhalte:
{context}

Bitte beantworte die Frage präzise und praxisorientiert für den Einsatz bei Sülzle Nutzeisen."""

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
    except Exception as e:
        answer = f"Fehler bei LLM-Anfrage: {e}\n\nKontext aus Hilfe:\n{context[:1000]}"
        model_used = "fallback"

    return AskResponse(answer=answer, sources=sources_meta, model=model_used)


@app.get("/modules")
def list_modules():
    """Gibt alle Hauptmodule von eNVenta zurück."""
    # Derived from the help structure
    modules = [
        {"name": "Stammdaten", "description": "Artikel, Kunden, Lieferanten, Lager"},
        {"name": "Einkauf", "description": "Bestellungen, Anfragen, Lieferantenmanagement"},
        {"name": "Verkauf", "description": "Angebote, Aufträge, Rechnungen, CRM"},
        {"name": "Lagerverwaltung", "description": "Lagerorte, Inventur, Umlagerungen, Chargen"},
        {"name": "Finanzbuchhaltung", "description": "Debitoren, Kreditoren, Sachkonten, Zahlungsverkehr"},
        {"name": "Anlagenbuchhaltung", "description": "Anlagevermögen, Abschreibungen"},
        {"name": "Produktion", "description": "Stücklisten, Fertigungsaufträge, BDE"},
        {"name": "Tourenplanung", "description": "Liefertouren, Fahrzeuge, Fahrer"},
        {"name": "Archiv", "description": "Dokumentenmanagement, Proxess-Anbindung"},
        {"name": "EDI", "description": "Elektronischer Datenaustausch, Schnittstellen"},
        {"name": "Kasse", "description": "Kassensystem, Abschlüsse"},
        {"name": "Beratungsassistent", "description": "eGate, Beratung und Konfiguration"},
        {"name": "Administration", "description": "Benutzer, Berechtigungen, System-Einstellungen"},
        {"name": "Reporting", "description": "Berichte, Auswertungen, Crystal Reports"},
    ]
    return {"modules": modules, "total": len(modules)}


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
                "name": "Stahlspezifische Attribute",
                "steps": [
                    "Werkstoffbezeichnung (z.B. S235JR, S355J2)",
                    "DIN/EN-Norm hinterlegen",
                    "Profilart (Flachstahl, Rundstahl, Winkel, U-Profil, IPE, HEA etc.)",
                    "Chargen-/Zertifikatspflicht aktivieren wenn nötig",
                    "Oberfläche (blank, verzinkt, lackiert, geschliffen)",
                    "Länge/Gewicht Beziehungen (kg/m)",
                ],
            },
            {
                "phase": 4,
                "name": "Preisfindung konfigurieren",
                "steps": [
                    "Preisgruppen anlegen (A, B, C Kunden oder Branche)",
                    "Staffelpreise hinterlegen",
                    "Rabattgruppen + Rabattstaffeln",
                    "Zuschläge (Kleinstmengen, Expresslieferung, Schnitt)",
                    "Währungen falls Export",
                ],
            },
            {
                "phase": 5,
                "name": "Validierung & Go-Live",
                "steps": [
                    "Test-Bestellung mit neuem Artikel anlegen",
                    "Lagerbuchung prüfen",
                    "Rechnungsdruck testen",
                    "Bestandsmengen importieren (Anfangsbestand)",
                    "ABC-Analyse nach erstem Monat durchführen",
                ],
            },
        ],
        "important_fields": {
            "Pflichtfelder": ["Artikelnummer", "Bezeichnung", "Artikelgruppe", "Hauptlieferant", "Einheit"],
            "Empfohlen": ["Gewicht", "Mindestbestand", "Lieferzeit", "EAN", "Warengruppe"],
            "Nutzeisen-spezifisch": ["Werkstoff", "Norm", "Profilart", "kg/m", "Länge"],
        },
    }
    return guide
