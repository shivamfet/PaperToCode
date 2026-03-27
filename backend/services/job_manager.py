import time
import uuid
from enum import Enum
from threading import Lock

DEFAULT_TTL_SECONDS = 1800  # 30 minutes
DEFAULT_MAX_JOBS = 100


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobManager:
    """In-memory job tracker for conversion tasks."""

    def __init__(
        self,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        max_jobs: int = DEFAULT_MAX_JOBS,
    ):
        self._jobs: dict[str, dict] = {}
        self._lock = Lock()
        self._ttl_seconds = ttl_seconds
        self._max_jobs = max_jobs

    def _cleanup_expired(self) -> None:
        """Remove jobs older than TTL. Must be called with lock held."""
        now = time.time()
        expired = [
            jid
            for jid, job in self._jobs.items()
            if now - job["created_at"] > self._ttl_seconds
        ]
        for jid in expired:
            del self._jobs[jid]

    def create_job(self) -> str:
        job_id = uuid.uuid4().hex
        with self._lock:
            self._cleanup_expired()
            if len(self._jobs) >= self._max_jobs:
                raise ValueError(
                    f"Server busy. Maximum job limit ({self._max_jobs}) reached."
                )
            self._jobs[job_id] = {
                "status": JobStatus.PENDING,
                "messages": [],
                "result": None,
                "error": None,
                "created_at": time.time(),
            }
        return job_id

    def get_job(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            if time.time() - job["created_at"] > self._ttl_seconds:
                del self._jobs[job_id]
                return None
            return dict(job)

    def add_message(self, job_id: str, message: str) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["messages"].append(message)

    def set_status(self, job_id: str, status: JobStatus) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = status

    def set_result(self, job_id: str, result: bytes) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["result"] = result

    def set_error(self, job_id: str, error: str) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.FAILED
                self._jobs[job_id]["error"] = error
