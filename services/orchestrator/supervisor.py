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
                    dependencies TEXT[]
                )
            ''')

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
        """Load pending tasks from database"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM supervisor_tasks
                WHERE status IN ('pending', 'in_progress', 'blocked')
                ORDER BY priority DESC, created_at ASC
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
                    dependencies=row['dependencies'] or []
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
                (id, name, description, priority, status, assigned_agent, created_at, updated_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ''', task.id, task.name, task.description, task.priority.value, task.status.value,
                task.assigned_agent, task.created_at, task.updated_at, json.dumps(task.metadata))

        self.task_queue.append(task)
        logger.info(f"Created task: {task.name} (priority: {task.priority})")

        return task

    async def process_task_queue(self):
        """Process tasks from queue"""
        if not self.task_queue:
            return

        # Sort by priority
        self.task_queue.sort(
            key=lambda t: (
                {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'background': 4}[t.priority.value],
                t.created_at
            )
        )

        # Get next available task
        for task in self.task_queue:
            if task.status == TaskStatus.PENDING and task.id not in self.active_tasks:
                await self.execute_task(task)
                break

    async def execute_task(self, task: Task):
        """Execute a single task"""
        try:
            logger.info(f"Executing task: {task.name}")
            self.active_tasks[task.id] = task

            # Update status
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = datetime.now()

            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    UPDATE supervisor_tasks
                    SET status = $1, updated_at = $2
                    WHERE id = $3
                ''', task.status.value, task.updated_at, task.id)

            # Route to appropriate agent
            result = await self.route_to_agent(task)

            # Mark complete
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.updated_at = datetime.now()

            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    UPDATE supervisor_tasks
                    SET status = $1, completed_at = $2, updated_at = $3
                    WHERE id = $4
                ''', task.status.value, task.completed_at, task.updated_at, task.id)

            # Remove from active
            del self.active_tasks[task.id]
            self.task_queue.remove(task)
            self.stats['tasks_completed'] += 1

            logger.info(f"Task completed: {task.name}")

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.status = TaskStatus.FAILED
            self.stats['tasks_failed'] += 1

            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    UPDATE supervisor_tasks
                    SET status = $1, updated_at = $2
                    WHERE id = $3
                ''', task.status.value, datetime.now(), task.id)

    async def route_to_agent(self, task: Task) -> Any:
        """Route task to appropriate agent"""
        # This is a placeholder for actual agent routing
        # In real implementation, this would invoke specific agents via Flowise or direct API

        logger.info(f"Routing task {task.name} to agent: {task.assigned_agent or 'auto'}")

        # Simulate work
        await asyncio.sleep(1)

        return {"status": "success"}

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

        while not self.shutdown_flag:
            try:
                loop_count += 1

                # Process task queue
                await self.process_task_queue()

                # Periodic health check
                if loop_count % (self.config.HEALTH_CHECK_INTERVAL // self.config.MAIN_LOOP_INTERVAL) == 0:
                    await self.health_check()

                # Periodic stats logging
                if loop_count % 20 == 0:
                    uptime = datetime.now() - self.stats['uptime_start']
                    logger.info(f"Supervisor stats - Uptime: {uptime}, "
                               f"Completed: {self.stats['tasks_completed']}, "
                               f"Failed: {self.stats['tasks_failed']}, "
                               f"Queue size: {len(self.task_queue)}")

                # Sleep
                await asyncio.sleep(self.config.MAIN_LOOP_INTERVAL)

            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(self.config.MAIN_LOOP_INTERVAL)

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

            # Setup signal handlers
            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}")
                self.shutdown_flag = True

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

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
