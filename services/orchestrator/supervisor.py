"""
Kirobi Core Supervisor
Autonomous 24/7 orchestration and self-development system

This supervisor runs continuously, manages agents, prioritizes tasks,
and evolves the system based on family interactions and system needs.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

import asyncpg
import httpx
from pydantic import BaseModel

# Optional integration with the local-first kirobi_core package. We
# import lazily so the supervisor still runs on environments where the
# package is not installed (e.g. the original container build context).
try:  # pragma: no cover - exercised in integration runs
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from kirobi_core.backlog import generate_backlog, prioritize  # type: ignore
    from kirobi_core.bridge import backlog_for_supervisor  # type: ignore
    from kirobi_core.scanner import scan_repository  # type: ignore
    KIROBI_CORE_AVAILABLE = True
except Exception:  # noqa: BLE001 - any failure means feature off
    KIROBI_CORE_AVAILABLE = False


def _resolve_log_path() -> str:
    """Return a writable path for the supervisor log file.

    In the container the path is ``/data/supervisor.log`` (mounted
    volume); outside the container we fall back to a writable location
    inside the repository so the supervisor stays importable for
    tooling and tests.
    """
    container_path = Path("/data")
    if container_path.is_dir() and os.access(container_path, os.W_OK):
        return str(container_path / "supervisor.log")
    fallback = Path(os.getenv("KIROBI_DATA_DIR", "")) if os.getenv("KIROBI_DATA_DIR") else None
    if fallback is None:
        fallback = Path(__file__).resolve().parents[2] / ".kirobi" / "supervisor"
    fallback.mkdir(parents=True, exist_ok=True)
    return str(fallback / "supervisor.log")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_resolve_log_path()),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class TaskStatus(str, Enum):
    """Task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    DEAD_LETTER = "dead_letter"


# Retry configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 1  # seconds; attempt n → sleep 2^(n-1) seconds


class Task(BaseModel):
    """Task model"""
    id: str
    name: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    assigned_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
    dependencies: List[str] = []
    retry_count: int = 0
    last_error: Optional[str] = None


class SupervisorState(str, Enum):
    """Supervisor operational states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    INTERVIEW_MODE = "interview_mode"
    AUTONOMOUS = "autonomous"
    MAINTENANCE = "maintenance"
    PAUSED = "paused"
    SHUTDOWN = "shutdown"


class SupervisorConfig:
    """Configuration for supervisor"""

    # Database
    DB_HOST = os.getenv('POSTGRES_HOST', 'postgres')
    DB_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    DB_NAME = os.getenv('POSTGRES_DB', 'kirobi')
    DB_USER = os.getenv('POSTGRES_USER', 'kirobi')
    DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'changeme')

    # Ollama
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
    SUPERVISOR_MODEL = os.getenv('SUPERVISOR_MODEL', 'llama3.1:70b')

    # Voice service
    VOICE_SERVICE_URL = os.getenv('VOICE_SERVICE_URL', 'http://voice-processing:8001')

    # Qdrant
    QDRANT_HOST = os.getenv('QDRANT_HOST', 'qdrant')
    QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))

    # Agent-Service-Endpunkte (konfigurierbar via Umgebungsvariablen)
    EMBEDDINGS_SERVICE_URL = os.getenv('EMBEDDINGS_SERVICE_URL', 'http://embeddings:8004')
    INGEST_SERVICE_URL = os.getenv('INGEST_SERVICE_URL', 'http://ingest:8005')
    RETRIEVAL_SERVICE_URL = os.getenv('RETRIEVAL_SERVICE_URL', 'http://retrieval:8006')
    API_SERVICE_URL = os.getenv('API_SERVICE_URL', 'http://api:8000')

    # Operation
    MAIN_LOOP_INTERVAL = int(os.getenv('SUPERVISOR_LOOP_INTERVAL', 30))  # seconds
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', 60))
    TASK_EXECUTION_TIMEOUT = int(os.getenv('TASK_TIMEOUT', 300))

    # Paths
    KIROBI_CORE_PATH = Path('/kirobi-core')
    EXPERIENCES_PATH = Path('/experiences')
    CANON_PATH = Path('/canon')
    DATA_PATH = Path('/data')


class KirobiSupervisor:
    """Main supervisor orchestrator"""

    def __init__(self, config: Optional[SupervisorConfig] = None):
        self.config = config or SupervisorConfig()
        self.state = SupervisorState.INITIALIZING
        self.db_pool: Optional[asyncpg.Pool] = None
        self.task_queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.shutdown_flag = False

        # Statistics
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'uptime_start': datetime.now(),
            'last_health_check': None
        }

        # Cached API token for Kirobi API calls
        self._api_token: Optional[str] = None

        logger.info("Kirobi Supervisor initializing...")

    async def initialize(self):
        """Initialize supervisor components"""
        try:
            logger.info("Connecting to database...")
            self.db_pool = await asyncpg.create_pool(
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                database=self.config.DB_NAME,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                min_size=2,
                max_size=10
            )

            logger.info("Initializing database schema...")
            await self.init_database_schema()

            logger.info("Loading pending tasks...")
            await self.load_pending_tasks()

            logger.info("Checking system health...")
            await self.health_check()

            self.state = SupervisorState.ACTIVE
            logger.info("Supervisor initialization complete!")

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

    async def init_database_schema(self):
        """Initialize database tables"""
        async with self.db_pool.acquire() as conn:
            # Tasks table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS supervisor_tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    assigned_agent TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    metadata JSONB,
                    dependencies TEXT[],
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT
                )
            ''')

            # Add columns if they don't exist yet (idempotent migration)
            for col_def in (
                "retry_count INTEGER NOT NULL DEFAULT 0",
                "last_error TEXT",
            ):
                col_name = col_def.split()[0]
                try:
                    await conn.execute(
                        f"ALTER TABLE supervisor_tasks ADD COLUMN IF NOT EXISTS {col_def}"
                    )
                except Exception:
                    pass  # column already exists on older Postgres versions

            # Events table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS supervisor_events (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    metadata JSONB
                )
            ''')

            logger.info("Database schema initialized")

    async def load_pending_tasks(self):
        """Load pending tasks from database, ordered by priority then age."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM supervisor_tasks
                WHERE status IN ('pending', 'in_progress', 'blocked')
                ORDER BY
                    CASE priority
                        WHEN 'critical'   THEN 0
                        WHEN 'high'       THEN 1
                        WHEN 'medium'     THEN 2
                        WHEN 'low'        THEN 3
                        WHEN 'background' THEN 4
                        ELSE 5
                    END ASC,
                    created_at ASC
            ''')

            for row in rows:
                task = Task(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    priority=TaskPriority(row['priority']),
                    status=TaskStatus(row['status']),
                    assigned_agent=row['assigned_agent'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    completed_at=row['completed_at'],
                    metadata=row['metadata'] or {},
                    dependencies=row['dependencies'] or [],
                    retry_count=row['retry_count'] if 'retry_count' in row.keys() else 0,
                    last_error=row['last_error'] if 'last_error' in row.keys() else None,
                )
                self.task_queue.append(task)

            logger.info(f"Loaded {len(self.task_queue)} pending tasks")

    async def health_check(self):
        """Check system health"""
        try:
            health_status = {
                'supervisor': 'healthy',
                'database': 'unknown',
                'ollama': 'unknown',
                'voice': 'unknown',
                'qdrant': 'unknown'
            }

            # Check database
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.fetchval('SELECT 1')
                health_status['database'] = 'healthy'
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                health_status['database'] = 'unhealthy'

            # Check Ollama
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.config.OLLAMA_HOST}/api/tags") as resp:
                        if resp.status == 200:
                            health_status['ollama'] = 'healthy'
            except Exception as e:
                logger.warning(f"Ollama health check failed: {e}")
                health_status['ollama'] = 'unhealthy'

            # Check voice service
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.config.VOICE_SERVICE_URL}/health") as resp:
                        if resp.status == 200:
                            health_status['voice'] = 'healthy'
            except Exception as e:
                logger.warning(f"Voice service health check failed: {e}")
                health_status['voice'] = 'unhealthy'

            self.stats['last_health_check'] = datetime.now()

            await self.log_event(
                'health_check',
                'info',
                f"Health check completed: {health_status}"
            )

            return health_status

        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {'supervisor': 'error'}

    async def log_event(self, event_type: str, severity: str, message: str, metadata: Optional[Dict] = None):
        """Log supervisor event"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO supervisor_events (timestamp, event_type, severity, message, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                ''', datetime.now(), event_type, severity, message, json.dumps(metadata or {}))

            # Also log to file
            log_file = self.config.KIROBI_CORE_PATH / 'core-events.log'
            with open(log_file, 'a') as f:
                f.write(f"[{datetime.now()}] [{event_type}] {message}\n")

        except Exception as e:
            logger.error(f"Failed to log event: {e}")

    async def create_task(self, name: str, description: str, priority: TaskPriority,
                          agent: Optional[str] = None, metadata: Optional[Dict] = None) -> Task:
        """Create a new task"""
        task_id = f"task_{datetime.now().timestamp()}"

        task = Task(
            id=task_id,
            name=name,
            description=description,
            priority=priority,
            status=TaskStatus.PENDING,
            assigned_agent=agent,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata or {}
        )

        # Save to database
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO supervisor_tasks
                (id, name, description, priority, status, assigned_agent, created_at, updated_at,
                 metadata, retry_count, last_error)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ''', task.id, task.name, task.description, task.priority.value, task.status.value,
                task.assigned_agent, task.created_at, task.updated_at, json.dumps(task.metadata),
                task.retry_count, task.last_error)

        self.task_queue.append(task)
        logger.info(f"Created task: {task.name} (priority: {task.priority})")

        return task

    async def process_task_queue(self):
        """Process tasks from queue, highest priority first."""
        if not self.task_queue:
            return

        # Sort in-memory queue: priority ASC (critical=0), then created_at ASC
        _PRIO = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'background': 4}
        self.task_queue.sort(
            key=lambda t: (_PRIO.get(t.priority.value, 9), t.created_at)
        )

        # Get next available task
        for task in self.task_queue:
            if task.status == TaskStatus.PENDING and task.id not in self.active_tasks:
                await self.execute_task(task)
                break

    async def execute_task(self, task: Task):
        """Execute a single task with retry logic and dead-letter handling."""
        logger.info(f"Executing task: {task.name} (attempt {task.retry_count + 1}/{MAX_RETRY_ATTEMPTS})")
        self.active_tasks[task.id] = task

        # Update status to in_progress
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now()
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                'UPDATE supervisor_tasks SET status = $1, updated_at = $2 WHERE id = $3',
                task.status.value, task.updated_at, task.id,
            )

        try:
            result = await self.route_to_agent(task)

            # Mark complete
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.updated_at = datetime.now()
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    'UPDATE supervisor_tasks SET status = $1, completed_at = $2, updated_at = $3 WHERE id = $4',
                    task.status.value, task.completed_at, task.updated_at, task.id,
                )

            del self.active_tasks[task.id]
            self.task_queue.remove(task)
            self.stats['tasks_completed'] += 1
            logger.info(f"Task completed: {task.name}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Task execution failed: {task.name} — {error_msg}")

            task.retry_count += 1
            task.last_error = error_msg

            if task.retry_count >= MAX_RETRY_ATTEMPTS:
                # Move to dead-letter
                task.status = TaskStatus.DEAD_LETTER
                task.updated_at = datetime.now()
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        '''UPDATE supervisor_tasks
                           SET status = $1, updated_at = $2, retry_count = $3, last_error = $4
                           WHERE id = $5''',
                        task.status.value, task.updated_at, task.retry_count, task.last_error, task.id,
                    )
                del self.active_tasks[task.id]
                self.task_queue.remove(task)
                self.stats['tasks_failed'] += 1
                logger.warning(f"Task moved to dead-letter after {MAX_RETRY_ATTEMPTS} attempts: {task.name}")
                await self.log_event(
                    'task_dead_letter', 'warning',
                    f"Task '{task.name}' dead-lettered after {MAX_RETRY_ATTEMPTS} attempts: {error_msg}",
                    {'task_id': task.id},
                )
            else:
                # Schedule retry with exponential backoff
                backoff = RETRY_BACKOFF_BASE * (2 ** (task.retry_count - 1))
                task.status = TaskStatus.PENDING
                task.updated_at = datetime.now()
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        '''UPDATE supervisor_tasks
                           SET status = $1, updated_at = $2, retry_count = $3, last_error = $4
                           WHERE id = $5''',
                        task.status.value, task.updated_at, task.retry_count, task.last_error, task.id,
                    )
                del self.active_tasks[task.id]
                logger.info(f"Task '{task.name}' will retry in {backoff}s (attempt {task.retry_count}/{MAX_RETRY_ATTEMPTS})")
                await asyncio.sleep(backoff)

    async def route_to_agent(self, task: Task) -> Any:
        """Route task to the appropriate agent handler.

        Dispatches based on ``task.assigned_agent``:

        - Known kirobi agents → Kirobi API conversation endpoint
        - ``"voice-agent"``   → Voice TTS service
        - ``None`` / unknown  → LLM-based auto-routing via Ollama

        Never raises — errors are caught, logged, and returned as a
        structured dict so the supervisor loop stays stable.
        """
        logger.info(f"Routing task '{task.name}' to agent: {task.assigned_agent or 'auto'}")

        _KIROBI_AGENTS = {
            "kirobi-coder",
            "kirobi-architect",
            "kirobi-ops",
            "kirobi-reviewer",
            "kirobi-frontend",
            "kirobi-docs",
        }

        agent = task.assigned_agent
        if agent in _KIROBI_AGENTS:
            return await self._route_to_kirobi_api(task)
        elif agent == "voice-agent":
            return await self._route_to_voice(task)
        else:
            return await self._route_auto(task)

    async def _get_api_token(self) -> Optional[str]:
        """Return a Bearer token for the Kirobi API.

        Checks ``KIROBI_API_TOKEN`` env first; otherwise performs a
        password-grant login against the auth service and caches the
        result in ``self._api_token``.
        """
        env_token = os.getenv("KIROBI_API_TOKEN")
        if env_token:
            return env_token

        if self._api_token:
            return self._api_token

        auth_url = os.getenv("KIROBI_AUTH_URL", "http://auth:8000")
        username = os.getenv("KIROBI_DEFAULT_USER", "admin")
        password = os.getenv("KIROBI_DEFAULT_PASSWORD", "changeme")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{auth_url}/token",
                    data={"username": username, "password": password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                resp.raise_for_status()
                data = resp.json()
                self._api_token = data.get("access_token")
                return self._api_token
        except Exception as exc:
            logger.warning(f"Could not obtain API token: {exc}")
            return None

    async def _route_to_kirobi_api(self, task: Task) -> Any:
        """Send task to a Kirobi agent via the API conversation endpoint.

        1. POST /conversations  → conversation_id
        2. POST /conversations/{id}/messages with task.description
        Returns a structured result dict; never raises.
        """
        api_url = os.getenv("KIROBI_API_URL", "http://api:8000")
        try:
            token = await self._get_api_token()
            headers: Dict[str, str] = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            async with httpx.AsyncClient(timeout=60.0) as client:
                # 1. Create conversation
                conv_resp = await client.post(
                    f"{api_url}/conversations",
                    json={"title": task.name, "agent": task.assigned_agent},
                    headers=headers,
                )
                conv_resp.raise_for_status()
                conversation_id = conv_resp.json()["id"]

                # 2. Send message and retrieve AI response
                msg_resp = await client.post(
                    f"{api_url}/conversations/{conversation_id}/messages",
                    json={"content": task.description, "role": "user"},
                    headers=headers,
                )
                msg_resp.raise_for_status()
                ai_response = msg_resp.json().get("content", "")

            return {
                "status": "success",
                "response": ai_response,
                "agent": task.assigned_agent,
            }
        except Exception as exc:
            logger.error(f"Kirobi API routing failed for task '{task.name}': {exc}")
            return {"status": "error", "error": str(exc)}

    async def _route_auto(self, task: Task) -> Any:
        """Use Ollama to determine the best agent, then delegate to Kirobi API.

        Sends a short prompt to Ollama asking which agent fits the task.
        Parses the response for a known agent name, sets
        ``task.assigned_agent``, and calls ``_route_to_kirobi_api``.
        Falls back to ``{"status": "skipped"}`` on any error.
        """
        ollama_host = SupervisorConfig.OLLAMA_HOST
        model = SupervisorConfig.SUPERVISOR_MODEL
        prompt = (
            f"Task: {task.name}\n"
            f"Description: {task.description}\n"
            "Which agent? (kirobi-coder/kirobi-architect/kirobi-ops/"
            "kirobi-reviewer/kirobi-frontend/kirobi-docs/none)\n"
            "Answer with just the agent name:"
        )
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{ollama_host}/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                )
                resp.raise_for_status()
                raw = resp.json().get("response", "").strip().lower()

            _VALID = {
                "kirobi-coder", "kirobi-architect", "kirobi-ops",
                "kirobi-reviewer", "kirobi-frontend", "kirobi-docs",
            }
            detected: Optional[str] = None
            for token in raw.split():
                candidate = token.strip(".,;:")
                if candidate in _VALID:
                    detected = candidate
                    break

            if detected:
                task.assigned_agent = detected
                logger.info(f"Auto-routing task '{task.name}' → {detected}")
                return await self._route_to_kirobi_api(task)

            logger.info(
                f"Auto-routing found no suitable agent for '{task.name}' (raw: {raw!r})"
            )
            return {"status": "skipped", "reason": "no suitable agent determined"}

        except Exception as exc:
            logger.warning(f"Auto-routing unavailable for task '{task.name}': {exc}")
            return {"status": "skipped", "reason": "auto-routing unavailable"}

    async def _route_to_voice(self, task: Task) -> Any:
        """Send task description to the voice TTS service.

        POST {VOICE_SERVICE_URL}/tts with ``{"text": task.description}``.
        Returns a structured result dict; never raises.
        """
        voice_url = SupervisorConfig.VOICE_SERVICE_URL
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{voice_url}/tts",
                    json={"text": task.description},
                )
                resp.raise_for_status()
            return {"status": "success", "agent": "voice-agent"}
        except Exception as exc:
            logger.warning(f"Voice service unavailable for task '{task.name}': {exc}")
            return {"status": "skipped", "reason": "voice service unavailable"}

    def _infer_agent(self, task: Task) -> str:
        """Leitet den passenden Agenten aus Task-Name und -Beschreibung ab."""
        text = f"{task.name} {task.description}".lower()
        if any(kw in text for kw in ("code", "implement", "bug", "test", "refactor")):
            return "kirobi-coder"
        if any(kw in text for kw in ("architecture", "design", "schema", "adr")):
            return "kirobi-architect"
        if any(kw in text for kw in ("docker", "deploy", "infra", "compose", "script")):
            return "kirobi-ops"
        if any(kw in text for kw in ("frontend", "ui", "pwa", "react", "next")):
            return "kirobi-frontend"
        if any(kw in text for kw in ("interview", "family", "onboarding")):
            return "family-interviewer"
        if any(kw in text for kw in ("voice", "speech", "audio")):
            return "voice-agent"
        return "kirobi-core"

    # Agent-Handler-Registry
    @property
    def _AGENT_HANDLERS(self) -> dict:
        return {
            "kirobi-coder": self._handle_coding_task,
            "kirobi-architect": self._handle_architecture_task,
            "kirobi-ops": self._handle_ops_task,
            "kirobi-core": self._handle_generic,
            "family-interviewer": self._handle_interview_task,
            "voice-agent": self._handle_voice_task,
        }

    async def _handle_coding_task(self, task: Task) -> dict:
        """Coding-Tasks: Ollama mit qwen2.5-coder oder llama3.1."""
        return await self._call_ollama(
            model=os.getenv("MODEL_CODE_PRIMARY", "qwen2.5-coder:7b"),
            prompt=f"Task: {task.name}\n\n{task.description}\n\nAnalysiere und schlage eine Implementierung vor.",
            task=task,
        )

    async def _handle_architecture_task(self, task: Task) -> dict:
        """Architektur-Tasks: Ollama mit deepseek-r1 für Reasoning."""
        return await self._call_ollama(
            model=os.getenv("MODEL_REASONING_PRIMARY", "deepseek-r1:7b"),
            prompt=f"Architektur-Aufgabe: {task.name}\n\n{task.description}\n\nErstelle eine strukturierte Analyse.",
            task=task,
        )

    async def _handle_ops_task(self, task: Task) -> dict:
        """Ops-Tasks: Ollama mit llama3.1:8b."""
        return await self._call_ollama(
            model=os.getenv("MODEL_CHAT_PRIMARY", "llama3.1:8b"),
            prompt=f"DevOps-Aufgabe: {task.name}\n\n{task.description}",
            task=task,
        )

    async def _handle_interview_task(self, task: Task) -> dict:
        """Interview-Tasks: Voice-Service aufrufen."""
        logger.info(f"Interview-Task: {task.name} — Voice-Service wird benachrichtigt")
        # Voice-Service benachrichtigen (best-effort)
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.VOICE_SERVICE_URL}/interview/start",
                    json={"participant": task.metadata.get("participant", "Sven"), "task_id": task.id},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        return {"status": "interview_started", "agent": "family-interviewer"}
        except Exception as e:
            logger.warning(f"Voice-Service nicht erreichbar: {e}")
        return {"status": "queued", "agent": "family-interviewer", "note": "Voice-Service offline"}

    async def _handle_voice_task(self, task: Task) -> dict:
        """Voice-Tasks: Voice-Processing-Service."""
        return {"status": "voice_task_queued", "agent": "voice-agent"}

    async def _handle_generic(self, task: Task) -> dict:
        """Generischer Handler: Ollama mit Standard-Modell."""
        return await self._call_ollama(
            model=self.config.SUPERVISOR_MODEL,
            prompt=f"Aufgabe: {task.name}\n\n{task.description}",
            task=task,
        )

    async def _call_ollama(self, model: str, prompt: str, task: Task) -> dict:
        """Ruft Ollama auf und gibt strukturiertes Ergebnis zurück."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.OLLAMA_HOST}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.3, "num_predict": 512},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.config.TASK_EXECUTION_TIMEOUT),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "status": "success",
                            "model": model,
                            "response": data.get("response", ""),
                            "task_id": task.id,
                        }
                    else:
                        logger.warning(f"Ollama {resp.status} für Task {task.id}")
                        return {"status": "ollama_error", "code": resp.status, "task_id": task.id}
        except Exception as e:
            logger.error(f"Ollama-Aufruf fehlgeschlagen: {e}")
            return {"status": "error", "error": str(e), "task_id": task.id}

    async def start_family_interview(self, participant: str):
        """Initiate family interview"""
        logger.info(f"Starting family interview for: {participant}")

        self.state = SupervisorState.INTERVIEW_MODE

        # Create interview task
        await self.create_task(
            name=f"Family Interview: {participant}",
            description=f"Conduct natural voice interview with {participant}",
            priority=TaskPriority.CRITICAL,
            agent="family-interviewer",
            metadata={
                'participant': participant,
                'interview_type': 'initial',
                'voice_enabled': True
            }
        )

        await self.log_event(
            'interview_started',
            'info',
            f"Family interview started for {participant}"
        )

    async def seed_from_kirobi_core(self, repo_root: Optional[str] = None,
                                     limit: int = 10) -> int:
        """Seed the task queue from the local kirobi_core backlog.

        Returns the number of tasks created. Silently returns 0 when
        the optional ``kirobi_core`` package is not importable, which
        keeps the supervisor backwards compatible with the original
        container build.
        """
        if not KIROBI_CORE_AVAILABLE:
            logger.info("kirobi_core not available; skipping backlog seed")
            return 0
        try:
            root = repo_root or os.getenv(
                "KIROBI_REPO_ROOT",
                str(Path(__file__).resolve().parents[2]),
            )
            scan = scan_repository(root)
            tasks = prioritize(generate_backlog(scan), limit=limit)
            created = 0
            for payload in backlog_for_supervisor(tasks):
                # Map string priority back to TaskPriority enum.
                try:
                    prio = TaskPriority(payload["priority"])
                except ValueError:
                    prio = TaskPriority.MEDIUM
                await self.create_task(
                    name=payload["name"],
                    description=payload["description"],
                    priority=prio,
                    agent=payload.get("agent"),
                    metadata=payload.get("metadata") or {},
                )
                created += 1
            logger.info(f"Seeded {created} task(s) from kirobi_core backlog")
            return created
        except Exception as exc:  # noqa: BLE001 - feature must not break the loop
            logger.warning(f"kirobi_core backlog seed failed: {exc}")
            return 0

    async def welcome_greeting(self):
        """Initial welcome greeting after system start"""
        greeting = """
        Hallo! Ich bin Kirobi – dein persönliches, intelligentes Familien-System.

        Ich bin gerade zum ersten Mal gestartet und freue mich sehr, dich und deine Familie kennenzulernen.

        Ich kann mit dir sprechen, zuhören, und lernen, wie ich euch am besten unterstützen kann.

        Bist du bereit für ein erstes Gespräch? Ich würde gerne mehr über deine Vision,
        deine Werte, deinen Alltag und deine Wünsche erfahren.

        Sag einfach "Ja, lass uns starten" wenn du bereit bist!
        """

        logger.info("Playing welcome greeting")

        # TODO: Send to voice service for TTS
        # For now, just log
        logger.info(greeting)

        await self.log_event(
            'welcome_greeting',
            'info',
            "Welcome greeting displayed"
        )

    async def _write_heartbeat(self):
        """Write a heartbeat line to kirobi-core/core-events.log."""
        queue_depth = len(self.task_queue)
        msg = (
            f"[{datetime.now().isoformat(timespec='seconds')}] [supervisor] "
            f"HEARTBEAT: processed={self.stats['tasks_completed']}, "
            f"failed={self.stats['tasks_failed']}, "
            f"queue_depth={queue_depth}"
        )
        logger.info(msg)
        try:
            log_file = self.config.KIROBI_CORE_PATH / 'core-events.log'
            with open(log_file, 'a') as f:
                f.write(msg + "\n")
        except Exception as exc:
            logger.warning(f"Heartbeat write failed: {exc}")

    async def main_loop(self):
        """Main supervisor control loop"""
        logger.info("Starting main supervisor loop...")

        # Initial greeting on first start
        await self.welcome_greeting()

        # Create initial family interview task
        await self.create_task(
            name="Initial Family Onboarding",
            description="Start family interview process with Sven",
            priority=TaskPriority.CRITICAL,
            agent="family-interviewer",
            metadata={'phase': 'onboarding'}
        )

        # Optionally seed additional repository-housekeeping tasks from
        # the local kirobi_core backlog. This is gated by an env var so
        # operators can opt-in once they trust the workflow.
        if os.getenv("KIROBI_SEED_BACKLOG", "").lower() in ("1", "true", "yes"):
            await self.seed_from_kirobi_core(
                limit=int(os.getenv("KIROBI_SEED_LIMIT", "5"))
            )

        loop_count = 0
        last_heartbeat = datetime.now()
        HEARTBEAT_INTERVAL = 60  # seconds

        while not self.shutdown_flag:
            try:
                loop_count += 1

                # Process task queue
                await self.process_task_queue()

                # Periodic health check
                if loop_count % (self.config.HEALTH_CHECK_INTERVAL // self.config.MAIN_LOOP_INTERVAL) == 0:
                    await self.health_check()

                # Heartbeat every 60 seconds
                now = datetime.now()
                if (now - last_heartbeat).total_seconds() >= HEARTBEAT_INTERVAL:
                    await self._write_heartbeat()
                    last_heartbeat = now

                # Periodic stats logging
                if loop_count % 20 == 0:
                    uptime = datetime.now() - self.stats['uptime_start']
                    logger.info(f"Supervisor stats - Uptime: {uptime}, "
                               f"Completed: {self.stats['tasks_completed']}, "
                               f"Failed: {self.stats['tasks_failed']}, "
                               f"Queue size: {len(self.task_queue)}")

                # Sleep — use short slices so SIGTERM is noticed quickly
                for _ in range(self.config.MAIN_LOOP_INTERVAL):
                    if self.shutdown_flag:
                        break
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(self.config.MAIN_LOOP_INTERVAL)

        # Finish any in-progress tasks before exiting
        if self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} active task(s) to finish...")
            for _ in range(30):  # max 30s grace period
                if not self.active_tasks:
                    break
                await asyncio.sleep(1)

        logger.info("Main loop shutting down...")

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Initiating supervisor shutdown...")
        self.state = SupervisorState.SHUTDOWN
        self.shutdown_flag = True

        # Close database pool
        if self.db_pool:
            await self.db_pool.close()

        logger.info("Supervisor shutdown complete")

    async def run(self):
        """Run the supervisor"""
        try:
            # Initialize
            await self.initialize()

            # Setup async-safe signal handlers
            loop = asyncio.get_running_loop()

            def _signal_handler(signum: int) -> None:
                logger.info(f"Received signal {signum} — initiating graceful shutdown")
                self.shutdown_flag = True

            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, _signal_handler, sig)
                except (NotImplementedError, RuntimeError):
                    # Fallback for environments that don't support add_signal_handler
                    signal.signal(sig, lambda s, f: _signal_handler(s))

            # Run main loop
            await self.main_loop()

        except Exception as e:
            logger.error(f"Supervisor error: {e}")
            raise
        finally:
            await self.shutdown()


async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Kirobi Supervisor Starting")
    logger.info("=" * 60)

    supervisor = KirobiSupervisor()
    await supervisor.run()


if __name__ == '__main__':
    asyncio.run(main())
