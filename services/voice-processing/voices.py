"""Voice catalog and Piper voice management."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

VOICES_DIR = Path(os.getenv("PIPER_VOICES_DIR", "/models/piper"))


@dataclass
class Voice:
    voice_id: str
    label: str
    language: str
    gender: str
    quality: str
    onnx_path: str
    config_path: str
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "voice_id": self.voice_id,
            "label": self.label,
            "language": self.language,
            "gender": self.gender,
            "quality": self.quality,
            "description": self.description,
        }


# Curated voice metadata — labels & descriptions for the UI
VOICE_METADATA: dict[str, dict[str, str]] = {
    "de_DE-thorsten-high": {
        "label": "Thorsten (warm, high-quality)",
        "gender": "male",
        "description": "Warmer maennlicher Sprecher, hoechste Qualitaet — Standard fuer ernste Themen.",
    },
    "de_DE-eva_k-x_low": {
        "label": "Eva (klar, schnell)",
        "gender": "female",
        "description": "Schnelle weibliche Stimme — gut fuer kurze Antworten.",
    },
    "de_DE-karlsson-low": {
        "label": "Karlsson (neutral, maennlich)",
        "gender": "male",
        "description": "Neutraler maennlicher Sprecher — Allzweck.",
    },
    "de_DE-kerstin-low": {
        "label": "Kerstin (freundlich, weiblich)",
        "gender": "female",
        "description": "Freundliche weibliche Stimme — Allzweck und Familie.",
    },
    "de_DE-ramona-low": {
        "label": "Ramona (dynamisch, weiblich)",
        "gender": "female",
        "description": "Dynamische weibliche Stimme — gut fuer lebhafte Konversation.",
    },
    "en_US-amy-medium": {
        "label": "Amy (English, female)",
        "gender": "female",
        "description": "American English female voice.",
    },
    "en_US-ryan-medium": {
        "label": "Ryan (English, male)",
        "gender": "male",
        "description": "American English male voice.",
    },
}


def list_voices() -> list[Voice]:
    """Scan the voices directory and return a list of available voices."""
    voices: list[Voice] = []
    if not VOICES_DIR.exists():
        logger.warning("Voices directory missing: %s", VOICES_DIR)
        return voices
    for onnx in sorted(VOICES_DIR.glob("*.onnx")):
        voice_id = onnx.stem
        config = onnx.with_suffix(".onnx.json")
        if not config.exists():
            continue
        meta = VOICE_METADATA.get(voice_id, {})
        # Extract language from the voice_id prefix (e.g. de_DE)
        lang = voice_id.split("-")[0] if "-" in voice_id else "unknown"
        # Quality is the last segment (high/medium/low/x_low)
        parts = voice_id.split("-")
        quality = parts[-1] if len(parts) >= 3 else "medium"
        voices.append(Voice(
            voice_id=voice_id,
            label=meta.get("label", voice_id),
            language=lang,
            gender=meta.get("gender", "neutral"),
            quality=quality,
            onnx_path=str(onnx),
            config_path=str(config),
            description=meta.get("description", ""),
        ))
    return voices


def find_voice(voice_id: Optional[str]) -> Optional[Voice]:
    """Return a Voice by id, or fall back to the first available voice."""
    voices = list_voices()
    if not voices:
        return None
    if voice_id:
        for v in voices:
            if v.voice_id == voice_id:
                return v
    return voices[0]


def default_voice() -> Optional[Voice]:
    return find_voice(os.getenv("PIPER_DEFAULT_VOICE", "de_DE-thorsten-high"))
