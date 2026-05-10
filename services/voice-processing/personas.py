"""Persona presets and tone modifiers for voice conversations.

These are layered on top of the existing 15-agent system prompts in
services/api/main.py: the agent provides the core identity (Hermes,
KeyCodi, kirobi-coder etc.), the tone modifier shapes HOW the answer
sounds (short/long, serious/playful, mentor/peer).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TonePreset:
    tone_id: str
    label: str
    emoji: str
    description: str
    modifier: str  # appended to the agent system prompt

    def to_dict(self) -> dict:
        return {
            "tone_id": self.tone_id,
            "label": self.label,
            "emoji": self.emoji,
            "description": self.description,
        }


TONE_PRESETS: dict[str, TonePreset] = {
    "neutral": TonePreset(
        tone_id="neutral",
        label="Neutral",
        emoji="🎯",
        description="Sachlich, klar, ohne Schnoerkel.",
        modifier=(
            "Antworte sachlich und klar. Keine Floskeln. Halte dich an Fakten und"
            " den Konversationskontext."
        ),
    ),
    "ernst": TonePreset(
        tone_id="ernst",
        label="Ernst & fundiert",
        emoji="🧠",
        description="Tief, durchdacht, fundierte Antworten.",
        modifier=(
            "Antworte ernsthaft, durchdacht und fundiert. Argumentiere Schritt fuer"
            " Schritt. Verzichte auf Witze und uebertriebene Lockerheit. Wenn etwas"
            " unsicher ist, sage das offen."
        ),
    ),
    "lustig": TonePreset(
        tone_id="lustig",
        label="Lustig & locker",
        emoji="😄",
        description="Mit Humor, Wortwitz, locker.",
        modifier=(
            "Antworte mit Humor und Wortwitz. Bleib aber inhaltlich praezise und"
            " hilfreich. Kurze Pointen sind erwuenscht. Kein Cringe, kein Slapstick."
        ),
    ),
    "kurz": TonePreset(
        tone_id="kurz",
        label="Kurz & knapp",
        emoji="⚡",
        description="Maximal 2 Saetze pro Antwort.",
        modifier=(
            "Antworte maximal in zwei kurzen Saetzen. Keine Aufzaehlungen, keine"
            " Erlaeuterungen. Zur Not nur ein Stichwort."
        ),
    ),
    "ausfuehrlich": TonePreset(
        tone_id="ausfuehrlich",
        label="Ausfuehrlich",
        emoji="📖",
        description="Detailreich mit Beispielen.",
        modifier=(
            "Erklaere ausfuehrlich. Strukturiere nach: 1. Was, 2. Warum, 3. Wie,"
            " 4. Beispiel. Nutze konkrete Beispiele."
        ),
    ),
    "mentor": TonePreset(
        tone_id="mentor",
        label="Mentor",
        emoji="🧙",
        description="Sokratischer Coach, stellt Rueckfragen.",
        modifier=(
            "Antworte wie ein erfahrener Mentor. Stelle vor allem die richtigen"
            " Rueckfragen, damit der Nutzer selbst zur Loesung kommt. Erst am Ende"
            " gibst du eine kompakte Empfehlung."
        ),
    ),
    "kumpel": TonePreset(
        tone_id="kumpel",
        label="Kumpel",
        emoji="🤙",
        description="Locker auf Augenhoehe, du-Form, kein Jargon.",
        modifier=(
            "Sprich auf Augenhoehe wie ein guter Kumpel. Locker, du-Form, ohne"
            " Fachjargon-Wand. Kurze Saetze, klare Sprache."
        ),
    ),
    "philosoph": TonePreset(
        tone_id="philosoph",
        label="Philosoph",
        emoji="📜",
        description="Reflektierend, zitiert, denkt mehrschichtig.",
        modifier=(
            "Antworte reflektierend und mehrschichtig. Beziehe philosophische"
            " Perspektiven ein, wenn passend. Zitate sparsam und nur sinnvoll."
        ),
    ),
}


def get_tone(tone_id: Optional[str]) -> TonePreset:
    if tone_id and tone_id in TONE_PRESETS:
        return TONE_PRESETS[tone_id]
    return TONE_PRESETS["neutral"]


def list_tones() -> list[TonePreset]:
    return list(TONE_PRESETS.values())


def apply_tone_to_text(reply_text: str, tone: TonePreset, max_tts_chars: int = 800) -> str:
    """Trim text for TTS — long-form answers should be truncated for synthesis."""
    if tone.tone_id == "kurz":
        # Kurz-mode: take only the first sentence or 200 chars
        first = reply_text.split(". ")[0]
        return first[:200].strip() + ("." if not first.endswith(".") else "")
    if len(reply_text) > max_tts_chars:
        truncated = reply_text[:max_tts_chars].rsplit(". ", 1)[0]
        return truncated + " ..."
    return reply_text
