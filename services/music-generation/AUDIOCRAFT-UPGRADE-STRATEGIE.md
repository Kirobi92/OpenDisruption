---
zone: WORKSPACE
created_by: Kirobi CEO Runner
created_at: 2026-05-21
issue: OPE-163
reviewed_by: pending
---

# audiocraft==1.3.0 Upgrade-Strategie: Langzeitanalyse

## Problem-Zusammenfassung

Der `music-generation`-Service ist an **torch==2.1.0** gebunden (strict pin durch audiocraft==1.3.0).
Die aktuelle PyTorch-Version ist **2.12.0** — das ist eine Lücke von 11 Minor-Versionen (ca. 18 Monate).

**Security-Risiko:** torch 2.1.0 enthält bekannte CVEs die in 2.2.x+ gepatcht wurden
(u.a. Pickle-Deserialisierungs-Schwachstellen, Tensor-Memory-Korruption).

---

## Dependency-Map

```
audiocraft==1.3.0
  ├── torch==2.1.0  (STRICT PIN — PyPI requirement)
  ├── torchaudio>=2.0.0,<2.1.2
  ├── xformers<0.0.23  (auch strikt → aktuell 0.0.30+)
  ├── torchvision==0.16.0
  ├── torchtext==0.16.0
  └── transformers (wir pinnen 4.57.0)

huggingface_hub: >=0.36.2,<1.0  (wegen transformers 4.x)
```

**Kern-Blocker:** `audiocraft==1.3.0` ist das **letzte offizielle PyPI-Release** von Facebook Research.
Kein neueres PyPI-Release existiert. Das Repo wird seit 2024 kaum mehr aktiv maintained.

---

## Optionen und Bewertung

### Option A: Status quo halten (torch 2.1.0, audiocraft 1.3.0)
- **Pro:** Funktioniert nachgewiesen, E2E-Smoke-Test bestanden (OPE-165)
- **Con:** torch 2.1.0 CVEs nicht gepatcht, kein xformers-Upgrade möglich
- **Security-Risiko:** MEDIUM — Service ist intern (127.0.0.1), kein direkter Internet-Zugang
- **Empfehlung:** Akzeptabler Interim-Status solange Service nicht extern exponiert

### Option B: audiocraft GitHub-Fork mit torch>=2.4 Patch
- **Fork-Kandidaten:** Eigener Fork mit entferntem torch-Pin aus audiocraft requirements
- **Aufwand:** Hoch — torch 2.4+ breaking changes in nn.Module-API, xformers-Kompatibilität prüfen
- **Risiko:** Reproduzierbarkeit sinkt, Fork wird zu Eigenverantwortung
- **Empfehlung:** Nur wenn CVE-Scan CRITICAL ergibt auf intern-exponiertem Port

### Option C: Migration zu native HuggingFace MusicGen (BEVORZUGT)
- **transformers >=4.31** enthält `MusicgenForConditionalGeneration` direkt — kein audiocraft nötig
- torch kann auf 2.6+ angehoben werden, huggingface_hub >=1.0 wird möglich
- **Aufwand:** MITTEL — `main.py` MusicGen-Loading anpassen, E2E-Smoke-Test als Gate
- **Gleiche Modelle:** `facebook/musicgen-small/medium/large` weiterhin verfügbar
- **Empfehlung:** Langzeitstrategie für Q3/Q4 2026

### Option D: Cloud-Alternative (Stable Audio API etc.)
- Nicht sinnvoll — widerspricht local-first Prinzip

---

## Langzeitstrategie

**Phase 1 — Sofort (Status quo absichern):**
- torch 2.1.0 Status und Risiko dokumentiert (diese Datei)
- Docker Image via Compose Network-Isolation schützen (music-generation nur internes Netzwerk)
- Trivy/Docker Scout CVE-Scan in CI ergänzen (CRITICAL = Build-Block)

**Phase 2 — Migration Q3/Q4 2026:**
- `main.py` auf native transformers MusicGen API migrieren
- `torch==2.6.0+cu124` + `transformers>=4.40.0` + `huggingface_hub>=0.26.0` (ohne audiocraft)
- E2E-Smoke-Test (3-Sek-WAV von OPE-165) als Regressions-Gate

**Phase 3 — Cleanup:**
- audiocraft aus requirements.txt entfernen
- xformers Strict-Pin auflösen (>=0.0.27 kompatibel mit torch 2.4+)
- Docker Image Größe: ~8 GB → ~4 GB erwartet

---

## Migration-Snippet (transformers-native MusicGen)

```python
# VORHER (audiocraft):
from audiocraft.models import MusicGen
model = MusicGen.get_pretrained('small')

# NACHHER (transformers native, torch 2.6+):
from transformers import MusicgenForConditionalGeneration, AutoProcessor
import scipy.io.wavfile

processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")

inputs = processor(text=["ambient meditation music"], padding=True, return_tensors="pt")
audio_values = model.generate(**inputs, max_new_tokens=256)
scipy.io.wavfile.write(
    "output.wav",
    rate=model.config.audio_encoder.sampling_rate,
    data=audio_values[0, 0].numpy()
)
```

---

## Status-Tabelle

| Schritt | Owner | Status |
|---------|-------|--------|
| Risiko analysiert + dokumentiert | Kirobi | ✅ Erledigt (OPE-163) |
| CVE-Trivy in CI | KeyCodi | Backlog Q3 2026 |
| Network-Isolation Compose | Sven-Review | Backlog |
| transformers-native Migration | KeyCodi | Backlog Q3/Q4 2026 |

---

## Referenzen

- audiocraft PyPI (letztes Release 1.3.0): https://pypi.org/project/audiocraft/
- transformers MusicGen Doku: https://huggingface.co/docs/transformers/model_doc/musicgen
- Verwandte Issues: OPE-164 (Warnung-Doku), OPE-165 (E2E-Test), OPE-166/167/168 (Dependabot)
