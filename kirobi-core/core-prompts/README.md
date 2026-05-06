# Core Prompts: Kirobi Agenten-System-Prompts

**Zone:** WORKSPACE | **Sensitivität:** Hoch

---

## Zweck
Alle System-Prompts für Kirobi-Agenten. Diese Prompts definieren das Verhalten, die Persönlichkeit und die Grenzen jedes Agenten.

## Prompts

| Datei | Agent | Modell |
|-------|-------|--------|
| `supervisor-system-prompt.md` | kirobi-core | llama3.1:70b |
| `architect-prompt.md` | kirobi-architect | deepseek-r1:32b |
| `coder-prompt.md` | kirobi-coder | qwen2.5-coder:32b |
| `observer-prompt.md` | kirobi-observer | mistral:7b |
| `ops-prompt.md` | kirobi-ops | llama3.1:8b |
| `hermes-prompt.md` | hermes-extractor | mistral:7b |
| `heart-agent-prompt.md` | samira-heart-agent | llama3.1:8b |
| `creator-coach-prompt.md` | sineo-creator-coach | llama3.1:8b |

## Verwendungs-Hinweise

- Prompts werden als System-Message in Flowise/Open WebUI geladen
- Änderungen erfordern Review durch kirobi-core und Sven
- Prompt-Versionen werden in Git-History getrackt
- Test jeder Änderung mit dem Agent-Test-Framework
