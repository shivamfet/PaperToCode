import uuid
from enum import Enum
from threading import Lock


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobManager:
    """In-memory job tracker for conversion tasks."""

    def __init__(self):
        self._jobs: dict[str, dict] = {}
        self._lock = Lock()

    def create_job(self) -> str:
        job_id = uuid.uuid4().hex
        with self._lock:
            self._jobs[job_id] = {
                "status": JobStatus.PENDING,
                "messages": [],
                "result": None,
                "error": None,
            }
        return job_id

    def get_job(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
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
