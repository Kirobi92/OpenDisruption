# Modell-Registry: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

---

## Lokale Modelle (via Ollama)

### Sprach-Modelle (LLMs)

| Modell | Größe | VRAM | Kontext | Stärken | Use Case |
|--------|-------|------|---------|---------|----------|
| `llama3.1:70b` | 42 GB | 40+ GB | 128k | Bestes allgemeines Reasoning | Kirobi-Core Supervisor |
| `llama3.1:8b` | 4.7 GB | 6 GB | 128k | Schnell, gut für Dialoge | Meiste Agenten |
| `deepseek-r1:32b` | 19 GB | 20 GB | 65k | Chain-of-Thought Reasoning | Architect, komplexe Planung |
| `qwen2.5-coder:32b` | 19 GB | 20 GB | 32k | Code-Generierung, alle Sprachen | Kirobi-Coder |
| `qwen2.5-coder:7b` | 4.7 GB | 6 GB | 32k | Schnelle Code-Hilfe | Quick-Code-Tasks |
| `mistral:7b` | 4.1 GB | 6 GB | 32k | Effizienz, Extraktion | Hermes, Observer |
| `phi3.5:3.8b` | 2.2 GB | 4 GB | 128k | Sehr schnell, guter Kontext | Quick-Tasks, Routing |
| `gemma2:27b` | 16 GB | 18 GB | 8k | Mehrsprachig, Qualität | Kreativität, DE-Texte |

### Vision-Modelle (Multimodal)

| Modell | Größe | VRAM | Fähigkeiten | Use Case |
|--------|-------|------|------------|----------|
| `llava:13b` | 8.2 GB | 10 GB | Bild-Verständnis, OCR | Bild-Analyse, Dokument-Scan |
| `moondream:1.8b` | 1.1 GB | 2 GB | Schnelle Bildanalyse | Thumbnail-Check, Quick-Vision |
| `bakllava:7b` | 4.5 GB | 6 GB | LLaVA-basiert | Allgemeine Vision-Tasks |

### Embedding-Modelle

| Modell | Dimensionen | Sprachen | Stärken | Use Case |
|--------|------------|----------|---------|----------|
| `nomic-embed-text` | 768 | EN (gut), DE (OK) | Schnell, effizient | Standard-Embeddings |
| `mxbai-embed-large` | 1024 | EN, Multilingual | Hohe Qualität | Wichtige Dokumente |
| `bge-m3` | 1024 | 100+ Sprachen | Bestes DE | Deutsche Inhalte |

### Sprach-Modelle (STT/TTS)

| Modell | Art | Sprachen | Qualität | Use Case |
|--------|-----|----------|---------|----------|
| `whisper:base` | STT | 99 Sprachen | Gut | Schnelle Transkription |
| `whisper:large-v3` | STT | 99 Sprachen | Sehr gut | Hochqualitative Transkription |
| `piper` | TTS | DE, EN, etc. | Gut | Lokale Sprachausgabe |
| `coqui-xtts` | TTS | Multilingual | Sehr gut | Hochwertige TTS |

---

## Cloud-Modelle (Optional, für nicht-sensible Aufgaben)

### OpenAI

| Modell | Kontext | Kosten (input/1M) | Use Case |
|--------|---------|-------------------|----------|
| `gpt-4o` | 128k | $2.50 | Komplexe Aufgaben |
| `gpt-4o-mini` | 128k | $0.15 | Kostengünstige Allgemein-Tasks |
| `text-embedding-3-small` | 8k | $0.02 | Embeddings (PUBLIC only) |
| `dall-e-3` | – | $0.04/Bild | Bildgenerierung (PUBLIC) |
| `whisper-1` | – | $0.006/min | Cloud-STT (PUBLIC only) |

### Anthropic

| Modell | Kontext | Kosten (input/1M) | Use Case |
|--------|---------|-------------------|----------|
| `claude-3-5-sonnet` | 200k | $3.00 | Langen Kontext, Analyse |
| `claude-3-haiku` | 200k | $0.25 | Schnelle Aufgaben |

### Google AI

| Modell | Kontext | Kosten | Use Case |
|--------|---------|--------|----------|
| `gemini-1.5-pro` | 1M | $3.50/1M | Sehr langer Kontext |
| `gemini-1.5-flash` | 1M | $0.075/1M | Schnell und günstig |

### Groq (Schnelle Inferenz)

| Modell | Kontext | Kosten | Use Case |
|--------|---------|--------|----------|
| `llama-3.1-70b-versatile` | 128k | $0.59/1M | Schnelles 70B |
| `mixtral-8x7b-32768` | 32k | $0.27/1M | Sehr schnell |

---

## Modell-Routing-Regeln

```yaml
routing_rules:
  - task: "supervisor_decision"
    model: "llama3.1:70b"
    fallback: "llama3.1:8b"
    
  - task: "architecture_planning"
    model: "deepseek-r1:32b"
    fallback: "llama3.1:70b"
    
  - task: "code_generation"
    model: "qwen2.5-coder:32b"
    fallback: "qwen2.5-coder:7b"
    
  - task: "quick_response"
    model: "phi3.5:3.8b"
    fallback: "llama3.1:8b"
    
  - task: "data_extraction"
    model: "mistral:7b"
    fallback: "llama3.1:8b"
    
  - task: "embedding"
    model: "bge-m3"
    fallback: "nomic-embed-text"
    
  - task: "image_analysis"
    model: "llava:13b"
    fallback: "moondream:1.8b"
    
  - task: "speech_to_text"
    model: "whisper:large-v3"
    fallback: "whisper:base"
    
  - task: "family_mediation"
    model: "llama3.1:8b"
    cloud_allowed: false
    
  - task: "sacred_zone"
    model: "llama3.1:8b"
    cloud_allowed: false
    local_only: true
```

---

## Modell-Prioritätsliste für Download

```bash
# Priorität 1: Essentiell für MVP
ollama pull llama3.1:8b
ollama pull nomic-embed-text
ollama pull mistral:7b

# Priorität 2: Wichtig für volle Funktionalität
ollama pull llama3.1:70b
ollama pull qwen2.5-coder:7b
ollama pull phi3.5:3.8b

# Priorität 3: Erweiterungen
ollama pull deepseek-r1:32b
ollama pull qwen2.5-coder:32b
ollama pull llava:13b
ollama pull bge-m3

# Priorität 4: Optional / Experimentell
ollama pull gemma2:27b
ollama pull moondream:1.8b
```
