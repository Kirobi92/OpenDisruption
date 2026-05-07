# Architecture Documentation: Kirobi / Disruptive OS

**Version:** 1.0
**Date:** 2026-05-05
**Classification:** WORKSPACE
**Authors:** Principal Systems Architect

---

## Table of Contents

> **Phase-0 Hinweis (KIDI-Rollout):** Die Architektur des Multi-Agent-/KIDI-/KEYBRODI-Layers ist als Design-Dokumente unter `docs/agent/` separat erfasst (siehe `docs/agent/MULTI-AGENT-ARCHITECTURE.md`, `AGENT-DECISION-MATRIX.md`). Runtime-Code folgt phasenweise.

1. [System Overview](#system-overview)
2. [Architectural Principles](#architectural-principles)
3. [High-Level Architecture](#high-level-architecture)
4. [Component Architecture](#component-architecture)
5. [Data Architecture](#data-architecture)
6. [Security Architecture](#security-architecture)
7. [Agent Architecture](#agent-architecture)
8. [Integration Architecture](#integration-architecture)
9. [Deployment Architecture](#deployment-architecture)
10. [Technology Stack](#technology-stack)
11. [Design Decisions](#design-decisions)

---

## System Overview

Kirobi / Disruptive OS is a **local-first, agent-orchestrated, privacy-focused personal AI operating system** designed to serve as a comprehensive digital ecosystem for Sven Darusi and family.

### Vision

Create a living, learning digital ecosystem that augments human capability while preserving privacy, autonomy, and family values.

### Core Purpose

- **Knowledge Management:** Structure and retrieve personal, family, and business knowledge
- **Agent Orchestration:** Coordinate 14+ specialized AI agents for different life domains
- **Privacy Protection:** Keep sensitive data local, never expose family information to cloud
- **Workflow Automation:** Automate repetitive tasks while keeping human in control
- **Second Brain:** Build a digital twin that learns and evolves with the user

### Key Characteristics

- **Local-First:** All sensitive processing on-premise
- **Agent-Driven:** Multi-agent system with supervisor pattern
- **Zone-Based Security:** Five-tier data classification model
- **Modular:** Clean separation of concerns
- **Extensible:** Plugin architecture for future capabilities
- **Observable:** Comprehensive logging and monitoring
- **Human-Centric:** Human always has final decision authority

---

## Architectural Principles

### 1. Local-First, Cloud-Optional

**Principle:** All critical functionality works offline. Cloud services are optional enhancements, never requirements.

**Rationale:** Privacy, control, independence from vendors

**Implications:**
- Local LLMs (Ollama) as default
- Local vector database (Qdrant)
- Local relational database (PostgreSQL)
- Cloud APIs only for PUBLIC/WORKSPACE data with explicit approval

### 2. Privacy by Design

**Principle:** Data never flows from higher sensitivity zones to lower ones or to external services without explicit approval.

**Rationale:** Family privacy is non-negotiable

**Implications:**
- Five-zone security model (PUBLIC → WORKSPACE → FAMILY_PRIVATE → QUARANTINE → SACRED)
- Agent permissions strictly limited by zone
- All external API calls logged and gated
- SACRED data encrypted at rest

### 3. Human-in-the-Loop

**Principle:** Agents augment, never replace, human judgment. Critical actions require human approval.

**Rationale:** Maintain human autonomy and prevent catastrophic automation

**Implications:**
- Approval gates for deletions, external communications, financial transactions
- Transparent agent reasoning
- Easy override and rollback mechanisms
- Clear escalation paths

### 4. Fail-Safe Defaults

**Principle:** When uncertain, choose the safest option. Default to least privilege.

**Rationale:** Prevent accidental harm

**Implications:**
- Unknown data classified as SACRED until proven otherwise
- Untrusted input never executed
- Explicit permissions required, no implicit grants
- Soft-delete instead of hard-delete

### 5. Observable & Auditable

**Principle:** All significant actions are logged. System behavior is explainable.

**Rationale:** Trust through transparency, forensics, debugging

**Implications:**
- Comprehensive event logging
- Agent decision explanations
- Zone access auditing
- Queryable logs

### 6. Separation of Concerns

**Principle:** Each component has a single, well-defined responsibility.

**Rationale:** Maintainability, testability, security

**Implications:**
- Clear boundaries between ingestion, storage, retrieval, agents, presentation
- No mixed responsibilities
- Interfaces over implementations

### 7. Defense in Depth

**Principle:** Multiple overlapping security controls. No single point of failure.

**Rationale:** Robust security even if one layer fails

**Implications:**
- Prompt engineering + input validation + output filtering + human oversight
- Zone policies + file permissions + encryption + audit logs
- Multiple agents can detect issues (observer, supervisor)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│                                                                   │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │  Open WebUI   │  │   Flowise    │  │  Voice Interface    │ │
│  │  (Primary UI) │  │  (Workflows) │  │  (Future)           │ │
│  └───────────────┘  └──────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                         │
│                                                                   │
│                    ┌──────────────────────┐                      │
│                    │   KIROBI-CORE        │                      │
│                    │  (Supervisor Agent)  │                      │
│                    └──────────────────────┘                      │
│                              ↓                                    │
│  ┌────────────┬──────────────┼──────────────┬──────────────┐   │
│  ↓            ↓               ↓               ↓              ↓   │
│ Architect   Coder       Observer         Hermes         Ops     │
│            Creator     Heart-Agent     Research-Crew    [+8]    │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE MANAGEMENT LAYER                    │
│                                                                   │
│  sources/  →  extracts/  →  clusters/  →  canon/  →  experiences/│
│  (Raw)        (Processed)   (Grouped)    (Truth)     (Learnings) │
│     ↓            ↓             ↓            ↓            ↓        │
│  Untrusted   Classified    Semantic    Authoritative  Wisdom     │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER                            │
│                                                                   │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │    Qdrant     │  │  PostgreSQL  │  │   File System       │ │
│  │  (Vectors)    │  │ (Relational) │  │  (Documents)        │ │
│  └───────────────┘  └──────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                         MODEL LAYER                              │
│                                                                   │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │    Ollama     │  │  Embeddings  │  │   Cloud APIs        │ │
│  │ (Local LLMs)  │  │   (BGE-M3)   │  │  (Optional)         │ │
│  └───────────────┘  └──────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                        │
│                                                                   │
│         Docker Compose  │  Networking  │  Monitoring            │
│         GPU (CUDA)      │  Backups     │  Logging               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Presentation Layer

#### Open WebUI
- **Purpose:** Primary user interface for chat and knowledge retrieval
- **Tech:** Web-based, connects to Ollama
- **Port:** 3000
- **Data Flow:** User ↔ Open WebUI ↔ kirobi-core ↔ Ollama/Qdrant
- **Zone Access:** All zones (user is Sven, has full access)

#### Flowise
- **Purpose:** Visual workflow builder for agent orchestration
- **Tech:** Node.js based low-code platform
- **Port:** 3001
- **Data Flow:** Workflows ↔ Flowise ↔ Agents ↔ Data stores
- **Zone Access:** WORKSPACE primarily

#### Voice Interface (Future)
- **Purpose:** Hands-free interaction
- **Tech:** Whisper (STT) + Piper (TTS)
- **Data Flow:** Voice → Whisper → kirobi-core → Piper → Audio

### Orchestration Layer

#### kirobi-core (Supervisor Agent)
- **Purpose:** Route requests to appropriate agents, synthesize responses
- **Model:** llama3.1:70b (high capability for supervision)
- **Responsibilities:**
  - Request routing based on intent
  - Multi-agent coordination
  - Response synthesis
  - Policy enforcement
  - Event logging
- **Zone Access:** Read all (with logging for FAMILY_PRIVATE), Write all except SACRED
- **Location:** `/kirobi-core/`

#### Specialized Agents (14 total)

**Technical Agents:**
- **kirobi-architect:** System design, planning (deepseek-r1:32b)
- **kirobi-coder:** Code development (qwen2.5-coder:32b)
- **kirobi-ops:** DevOps, infrastructure (llama3.1:8b)
- **kirobi-observer:** Monitoring, analysis (mistral:7b)

**Knowledge Agents:**
- **hermes-extractor:** Data ingestion, classification (mistral:7b)
- **research-crew:** Web research (perplexica)

**Family Agents:**
- **samira-heart-agent:** Family mediation, emotional support (llama3.1:8b)
- **sineo-creator-coach:** YouTube/creator coaching (llama3.1:8b)

**Business Agents:**
- **enterprise-agent:** Business workflows (llama3.1:70b)

**Creative Agents:**
- **creative-agent:** Brainstorming, content creation (llama3.1:70b)

**Utility Agents:**
- **voice-agent:** Voice I/O (whisper + TTS)
- **installer-agent:** Setup, onboarding (llama3.1:8b)
- **mediation-crew:** Conflict resolution (llama3.1:8b)

**Agent Communication:**
- Agents communicate via kirobi-core (star topology)
- No direct agent-to-agent communication (prevents complexity)
- Supervisor pattern ensures coordination

### Knowledge Management Layer

#### Five-Stage Knowledge Pipeline

```
1. SOURCES (Untrusted Input)
   ├── /sources/inbox/          # User uploads
   ├── /sources/imports/         # External data
   ├── /sources/web-research/    # Scraped content
   ├── /sources/apis/            # API responses
   └── /sources/[type]/          # Categorized by type

2. EXTRACTS (Processed & Classified)
   ├── /extracts/public/         # PUBLIC zone
   ├── /extracts/workspace/      # WORKSPACE zone
   ├── /extracts/technical/      # WORKSPACE (tech-specific)
   ├── /extracts/business/       # WORKSPACE (business)
   ├── /extracts/family-private/ # FAMILY_PRIVATE zone
   ├── /extracts/structured/     # Structured data
   └── /extracts/[category]/     # Further categorization

3. CLUSTERS (Semantically Grouped)
   ├── /clusters/[topic]/        # Auto-clustered by similarity
   └── [Enables topic-based retrieval]

4. CANON (Authoritative Truth)
   ├── /canon/public/            # Authoritative public docs
   ├── /canon/workspace/         # Authoritative work docs
   ├── /canon/family/            # Authoritative family docs
   └── [Versioned, conflict-resolved master documents]

5. EXPERIENCES (Learnings & Reflections)
   ├── /experiences/projects/    # Project retrospectives
   ├── /experiences/learnings/   # Lessons learned
   ├── /experiences/knowledge/   # Captured insights
   └── /experiences/experiments/ # Experimental findings
```

**Data Flows:**

```
User Upload → hermes-extractor → Classify Zone → Extract Content
                                                      ↓
                                              Embed with BGE-M3
                                                      ↓
                                          Store in Qdrant (zone-specific collection)
                                                      ↓
                                          Save to /extracts/[zone]/
                                                      ↓
[Clustering Algorithm] → Group by similarity → /clusters/[topic]/
                                                      ↓
[Canon Update Logic] → Resolve conflicts → Update /canon/[zone]/
                                                      ↓
[Experience Capture] → Extract learnings → /experiences/learnings/
```

### Storage Layer

#### Qdrant (Vector Database)
- **Purpose:** Semantic search, RAG, embedding storage
- **Port:** 6333 (HTTP), 6334 (gRPC)
- **Collections:**
  - `kirobi_public` - PUBLIC zone embeddings
  - `kirobi_workspace` - WORKSPACE embeddings
  - `kirobi_family` - FAMILY_PRIVATE embeddings
  - `kirobi_sacred` - SACRED embeddings (encrypted)
- **Embedding Model:** BGE-M3 (1024 dims) or nomic-embed-text (768 dims)
- **Data Volume:** Grows indefinitely (disk space dependent)

#### PostgreSQL (Relational Database)
- **Purpose:** Structured metadata, relationships, agent state
- **Port:** 5432
- **Schema:**
  - `documents` - File metadata (path, zone, created, modified, author)
  - `agents` - Agent registry and state
  - `events` - System events (audit log)
  - `workflows` - Flowise workflow definitions
  - `integrations` - External integration configs
- **Data Volume:** Moderate (metadata only, not content)

#### File System (Document Storage)
- **Purpose:** Raw document storage, versioned via git
- **Structure:** See Knowledge Management Layer
- **Backup:** Automated daily backups to `/mnt/backup/kirobi`
- **Versioning:** Git for `/canon/`, `/metadata/`, `/kirobi-core/`

### Model Layer

#### Ollama (Local LLM Server)
- **Purpose:** Run local LLMs for all sensitive data
- **Port:** 11434
- **Models:**
  - `llama3.1:70b` - High capability (supervisor, creative, enterprise)
  - `llama3.1:8b` - Fast, efficient (ops, family, installer)
  - `deepseek-r1:32b` - Reasoning (architect)
  - `qwen2.5-coder:32b` - Code (coder)
  - `mistral:7b` - Versatile (observer, hermes)
  - `nomic-embed-text` - Embeddings (768 dims)
- **GPU:** NVIDIA CUDA required for acceptable performance
- **Scaling:** Parallel requests configured via `OLLAMA_NUM_PARALLEL`

#### Cloud APIs (Optional)
- **OpenAI:** gpt-4o-mini (PUBLIC/WORKSPACE with approval)
- **Anthropic:** claude-3-haiku (PUBLIC/WORKSPACE with approval)
- **Google:** gemini-1.5-flash (PUBLIC/WORKSPACE with approval)
- **Groq:** llama-3.1-8b-instant (fast inference, PUBLIC only)
- **Policy:** Only used for non-sensitive data, always logged

---

## Security Architecture

### Zone-Based Access Control

**Five Security Zones:**

```
┌─────────────────────────────────────────────────────────┐
│  ZONE 5: SACRED (🔐)                                    │
│  - Highest confidentiality                              │
│  - Encrypted at rest                                    │
│  - Human-only access (explicit agent approval)          │
│  - Air-gap capable                                      │
│  - Full audit logging                                   │
└─────────────────────────────────────────────────────────┘
                         ↑ (upgrade only)
┌─────────────────────────────────────────────────────────┐
│  ZONE 4: QUARANTINE (⚠️)                                │
│  - Untrusted/unverified                                 │
│  - No embedding until reviewed                          │
│  - Limited agent access                                 │
│  - Regular review cycles (30 days)                      │
└─────────────────────────────────────────────────────────┘
                         ↑ (data flow restricted)
┌─────────────────────────────────────────────────────────┐
│  ZONE 3: FAMILY_PRIVATE (👨‍👩‍👦)                          │
│  - Family-only content                                  │
│  - Never sent to cloud APIs                             │
│  - Family agent access only                             │
│  - Full access logging                                  │
└─────────────────────────────────────────────────────────┘
                         ↑ (careful upgrades)
┌─────────────────────────────────────────────────────────┐
│  ZONE 2: WORKSPACE (💼)                                 │
│  - Work/technical content                               │
│  - Cloud APIs with approval                             │
│  - Most agents have access                              │
│  - Summary logging                                      │
└─────────────────────────────────────────────────────────┘
                         ↑ (easy upgrades)
┌─────────────────────────────────────────────────────────┐
│  ZONE 1: PUBLIC (🌍)                                    │
│  - Publicly shareable                                   │
│  - Cloud APIs allowed                                   │
│  - All agents have access                               │
│  - Minimal logging                                      │
└─────────────────────────────────────────────────────────┘
```

**Zone Enforcement Layers:**

1. **Documentation Layer:** Policies in `/CLAUDE.md`, `/metadata/`
2. **Agent Training Layer:** System prompts enforce zones
3. **Application Layer:** Pre-flight checks before operations
4. **File System Layer:** Unix permissions (planned)
5. **Encryption Layer:** SACRED data encrypted (planned)
6. **Audit Layer:** All zone access logged

### Defense in Depth

**7-Layer Security Model:**

1. **Human Oversight** - Final authority, approval gates
2. **Application Logic** - Zone enforcement, permission checks
3. **Prompt Engineering** - Safety prefixes, injection resistance
4. **Data Classification** - Automatic zone detection
5. **Application Security** - Input validation, output filtering
6. **Container Security** - Network isolation, resource limits
7. **Host Security** - OS hardening, disk encryption (user responsibility)

### Threat Mitigation

See `/THREAT-MODEL.md` for detailed threat analysis.

**Key Mitigations:**
- **Prompt Injection:** Input sanitization, content isolation, output filtering
- **Data Exfiltration:** Zone-based API restrictions, pre-flight checks, logging
- **Unauthorized Access:** Permission matrix, audit logging, file ACLs (planned)
- **Privilege Escalation:** Immutable security configs, FIM (planned)
- **Supply Chain:** Image pinning, vulnerability scanning (planned)

---

## Agent Architecture

### Supervisor Pattern

```
                    ┌─────────────────┐
                    │  User Request   │
                    └────────┬────────┘
                             ↓
                    ┌────────────────────┐
                    │   kirobi-core      │
                    │   (Supervisor)     │
                    └────────┬───────────┘
                             ↓
                    [Intent Analysis]
                             ↓
                    [Routing Decision]
                             ↓
          ┌──────────┬──────┼──────┬──────────┐
          ↓          ↓      ↓      ↓          ↓
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │Agent 1 │ │Agent 2 │ │Agent 3 │ │Agent N │
    └────┬───┘ └───┬────┘ └───┬────┘ └───┬────┘
         │         │          │          │
         └─────────┴──────────┴──────────┘
                     ↓
            [Response Synthesis]
                     ↓
              ┌──────────────┐
              │ User Response│
              └──────────────┘
```

**Routing Logic:**

```python
def route_request(request: str, context: Context) -> List[Agent]:
    intent = classify_intent(request)

    routing_map = {
        "code": [kirobi_coder],
        "architecture": [kirobi_architect],
        "family_support": [samira_heart_agent],
        "research": [research_crew],
        "monitoring": [kirobi_observer],
        "complex": [kirobi_architect, kirobi_coder, kirobi_observer],
        # ... more mappings
    }

    agents = routing_map.get(intent, [kirobi_core])  # Default to self

    # Filter by zone permissions
    required_zones = detect_zones(request)
    agents = [a for a in agents if a.can_access(required_zones)]

    return agents
```

### Agent State Management

**Stateless Agents (Preferred):**
- Each request is independent
- Context passed explicitly
- No persistent state between requests
- Easier to test, debug, scale

**Stateful Agents (When Needed):**
- Long-running workflows (Flowise)
- Multi-turn conversations (stored in PostgreSQL)
- Learning/adaptation (experiences/ folder)

### Agent Communication Protocol

**Message Format:**

```json
{
  "request_id": "uuid",
  "timestamp": "ISO8601",
  "from": "kirobi-core",
  "to": "kirobi-coder",
  "intent": "code_generation",
  "payload": {
    "task": "Create a Python function...",
    "context": {...},
    "zones": ["PUBLIC", "WORKSPACE"]
  },
  "metadata": {
    "user": "sven",
    "session_id": "uuid"
  }
}
```

**Response Format:**

```json
{
  "request_id": "uuid",
  "timestamp": "ISO8601",
  "from": "kirobi-coder",
  "to": "kirobi-core",
  "status": "success|error|partial",
  "result": {
    "output": "...",
    "reasoning": "...",
    "confidence": 0.95,
    "zones_accessed": ["WORKSPACE"]
  },
  "metadata": {
    "model_used": "qwen2.5-coder:32b",
    "tokens_used": 1234,
    "duration_ms": 5000
  }
}
```

---

## Integration Architecture

### External Integrations

```
┌─────────────────────────────────────────────────────────┐
│                  KIROBI CORE                             │
└──────────────┬───────────────────────────┬──────────────┘
               ↓                           ↓
    ┌──────────────────┐      ┌──────────────────────┐
    │ Local Services   │      │  External Services   │
    └──────────────────┘      └──────────────────────┘
            ↓                          ↓
    ┌──────────────┐          ┌─────────────────────┐
    │  Ollama      │          │  OpenAI API         │
    │  Qdrant      │          │  Anthropic API      │
    │  PostgreSQL  │          │  M365 (Outlook)     │
    │  Flowise     │          │  M365 (Teams)       │
    └──────────────┘          │  M365 (OneDrive)    │
                              │  Perplexica (Web)   │
                              │  Home Assistant     │
                              └─────────────────────┘
```

**Integration Patterns:**

1. **Local Service Integration:**
   - Direct API calls (Ollama, Qdrant, PostgreSQL)
   - Docker network communication
   - No authentication needed (trusted local network)

2. **Cloud Service Integration:**
   - OAuth2 for M365
   - API keys for AI services
   - Rate limiting and retries
   - Zone-aware (PUBLIC/WORKSPACE only)

3. **Webhook Integration:**
   - Incoming webhooks (e.g., from GitHub, GitLab)
   - Outgoing webhooks (notifications, automation)
   - Signature verification

4. **File-Based Integration:**
   - Obsidian (shared folder)
   - Exports/imports via `/sources/imports/`
   - Watch folders for automation

### API Gateway (Future)

**Planned centralized API management:**

```
External Request → API Gateway → [Auth] → [Rate Limit] → [Zone Check] → Agent
                                    ↓
                            [Logging & Monitoring]
```

---

## Deployment Architecture

### Local Deployment (Current)

```
┌─────────────────────────────────────────────────────────────┐
│  Host Machine (Ubuntu 22.04+)                               │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Docker Engine                                         │  │
│  │                                                         │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │  │
│  │  │ ollama   │ │ open-    │ │ qdrant   │ │ postgres │ │  │
│  │  │          │ │ webui    │ │          │ │          │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │  │
│  │                                                         │  │
│  │  ┌──────────┐ [kirobi-net bridge network]            │  │
│  │  │ flowise  │                                         │  │
│  │  └──────────┘                                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  File System                                           │  │
│  │  - /home/sven/kirobi/ (repo clone)                   │  │
│  │  - Docker volumes (ollama_data, qdrant_data, etc.)   │  │
│  │  - /mnt/backup/kirobi/ (backups)                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  [NVIDIA GPU - CUDA 12.0+]                                   │
└─────────────────────────────────────────────────────────────┘
```

**Startup Sequence:**

1. `make init` - Initialize folders, download images
2. `make up` - Start all services via docker-compose
3. `make pull-models` - Download Ollama models
4. `make status` - Verify health

**Service Dependencies:**

```
postgres → flowise
       ↓
     ollama → open-webui
       ↓
     qdrant
```

### Future Deployment Options

**Option 1: Distributed (Family Network)**
- Multiple devices (workstation, NAS, Pi)
- Services distributed across hardware
- Higher availability, better resource utilization

**Option 2: Hybrid (Local + Cloud)**
- Core on-premise
- Non-sensitive compute in cloud
- Bursting for heavy workloads

**Option 3: Air-Gapped (Maximum Privacy)**
- SACRED data on offline device
- Manual transfer for analysis
- Ultimate privacy protection

---

## Technology Stack

### Core Infrastructure

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Container Platform | Docker | 24+ | Service isolation |
| Orchestration | Docker Compose | v2+ | Multi-container management |
| Operating System | Linux (Ubuntu) | 22.04+ | Host OS |
| GPU Support | NVIDIA CUDA | 12.0+ | LLM acceleration |

### Storage & Databases

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Vector DB | Qdrant | latest | Semantic search, embeddings |
| Relational DB | PostgreSQL | 16 | Structured metadata |
| File System | Ext4/Btrfs | - | Document storage |
| Version Control | Git | 2.40+ | Code & doc versioning |

### AI/ML Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Local LLM Server | Ollama | latest | Run local models |
| Large Models | Llama 3.1 | 70b, 8b | General purpose |
| Reasoning Model | DeepSeek R1 | 32b | Complex reasoning |
| Code Model | Qwen 2.5 Coder | 32b | Code generation |
| Embedding Model | BGE-M3 / Nomic | 1024/768d | Text embeddings |

### Application Layer

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Chat UI | Open WebUI | main | Primary interface |
| Workflow Engine | Flowise | latest | Visual orchestration |
| Web Search | Perplexica | latest | Research agent |

### Monitoring (Planned)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM Observability | Langfuse | LLM tracing, metrics |
| System Monitoring | OpenObserve | Logs, metrics, traces |
| Visualization | Grafana | Dashboards |

---

## Design Decisions

### ADR-001: Local-First Architecture

**Status:** ✅ Accepted

**Context:** Need to process sensitive family and business data

**Decision:** All sensitive processing happens locally, cloud optional

**Consequences:**
- ✅ Privacy protection
- ✅ No vendor lock-in
- ✅ Works offline
- ❌ Higher hardware requirements
- ❌ Slower than cloud for some tasks

---

### ADR-002: Five-Zone Security Model

**Status:** ✅ Accepted

**Context:** Different data has different sensitivity levels

**Decision:** Implement five-tier zone model (PUBLIC → SACRED)

**Consequences:**
- ✅ Clear classification
- ✅ Granular access control
- ✅ Audit capability
- ❌ Complexity in enforcement
- ❌ Requires discipline to classify

---

### ADR-003: Supervisor Agent Pattern

**Status:** ✅ Accepted

**Context:** Need to coordinate 14+ specialized agents

**Decision:** Use star topology with kirobi-core as supervisor

**Consequences:**
- ✅ Clear coordination
- ✅ Single point of policy enforcement
- ✅ Easier debugging
- ❌ Supervisor is bottleneck
- ❌ No direct agent-to-agent communication

---

### ADR-004: Docker Compose over Kubernetes

**Status:** ✅ Accepted

**Context:** Need container orchestration for local deployment

**Decision:** Use Docker Compose, not Kubernetes

**Consequences:**
- ✅ Simpler for single-node
- ✅ Lower resource overhead
- ✅ Easier to understand/debug
- ❌ No auto-scaling
- ❌ No high availability

**Rationale:** Kubernetes is overkill for local single-node deployment

---

### ADR-005: Soft-Delete by Default

**Status:** 🔄 Proposed

**Context:** Need to prevent accidental data loss

**Decision:** Move files to /archive/ instead of hard delete

**Consequences:**
- ✅ Recoverable deletions
- ✅ Audit trail
- ❌ More disk usage
- ❌ Requires cleanup policy

---

## Future Architecture Evolution

### Phase 2 Enhancements (Q2-Q4 2025)

1. **Multimodal Processing**
   - Image analysis (LLaVA)
   - Audio processing (Whisper)
   - Video understanding

2. **Agent Teams**
   - Multi-agent collaboration
   - Parallel task execution
   - Conflict resolution

3. **Advanced Observability**
   - Real-time dashboards
   - Anomaly detection
   - Performance optimization

### Phase 3 Enhancements (2026+)

1. **Digital Twin**
   - Personal AI model
   - Proactive recommendations
   - Long-term memory

2. **Enterprise Features**
   - Multi-user support
   - RBAC
   - SSO integration

3. **Edge Deployment**
   - Mobile clients
   - Distributed agents
   - Sync strategies

---

## Glossary

- **Agent:** AI entity with specific role and capabilities
- **Canon:** Authoritative, versioned master documents
- **Extract:** Processed, classified content from sources
- **RAG:** Retrieval Augmented Generation
- **Supervisor:** Coordinator agent (kirobi-core)
- **Zone:** Security classification level

---

**Document Version:** 1.0
**Last Updated:** 2026-05-05
**Next Review:** 2026-08-05
