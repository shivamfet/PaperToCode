import time
from unittest.mock import patch

import pytest
from services.job_manager import JobManager, JobStatus


class TestJobManager:
    """Tests for the JobManager."""

    def test_create_job_returns_id(self):
        jm = JobManager()
        job_id = jm.create_job()
        assert isinstance(job_id, str)
        assert len(job_id) > 0

    def test_create_job_unique_ids(self):
        jm = JobManager()
        ids = {jm.create_job() for _ in range(10)}
        assert len(ids) == 10

    def test_get_job_returns_status(self):
        jm = JobManager()
        job_id = jm.create_job()
        job = jm.get_job(job_id)
        assert job is not None
        assert job["status"] == JobStatus.PENDING

    def test_get_job_returns_none_for_unknown(self):
        jm = JobManager()
        assert jm.get_job("nonexistent") is None

    def test_add_message(self):
        jm = JobManager()
        job_id = jm.create_job()
        jm.add_message(job_id, "Extracting text...")
        job = jm.get_job(job_id)
        assert "Extracting text..." in job["messages"]

    def test_set_status(self):
        jm = JobManager()
        job_id = jm.create_job()
        jm.set_status(job_id, JobStatus.PROCESSING)
        assert jm.get_job(job_id)["status"] == JobStatus.PROCESSING

    def test_set_result(self):
        jm = JobManager()
        job_id = jm.create_job()
        jm.set_result(job_id, b"notebook bytes")
        job = jm.get_job(job_id)
        assert job["result"] == b"notebook bytes"

    def test_set_error(self):
        jm = JobManager()
        job_id = jm.create_job()
        jm.set_error(job_id, "Something failed")
        job = jm.get_job(job_id)
        assert job["status"] == JobStatus.FAILED
        assert job["error"] == "Something failed"

    def test_complete_job(self):
        jm = JobManager()
        job_id = jm.create_job()
        jm.set_status(job_id, JobStatus.COMPLETED)
        assert jm.get_job(job_id)["status"] == JobStatus.COMPLETED


class TestJobTTLCleanup:
    """Jobs older than 30 minutes should be automatically purged."""

    def test_expired_jobs_are_purged_on_create(self):
        """Creating a new job triggers cleanup of expired jobs."""
        jm = JobManager(ttl_seconds=1800, max_jobs=100)
        # Create a job, then simulate it being 31 minutes old
        old_id = jm.create_job()
        with jm._lock:
            jm._jobs[old_id]["created_at"] = time.time() - 1801
        # Creating a new job should purge the old one
        jm.create_job()
        assert jm.get_job(old_id) is None

    def test_non_expired_jobs_are_kept(self):
        """Jobs within TTL should not be purged."""
        jm = JobManager(ttl_seconds=1800, max_jobs=100)
        recent_id = jm.create_job()
        # Create another job — should not purge the recent one
        jm.create_job()
        assert jm.get_job(recent_id) is not None

    def test_expired_job_returns_none_on_get(self):
        """get_job should return None for expired jobs."""
        jm = JobManager(ttl_seconds=1800, max_jobs=100)
        job_id = jm.create_job()
        with jm._lock:
            jm._jobs[job_id]["created_at"] = time.time() - 1801
        assert jm.get_job(job_id) is None


class TestMaxJobLimit:
    """Maximum concurrent jobs should be enforced."""

    def test_rejects_when_max_jobs_reached(self):
        """create_job raises ValueError when max jobs reached."""
        jm = JobManager(ttl_seconds=1800, max_jobs=3)
        jm.create_job()
        jm.create_job()
        jm.create_job()
        with pytest.raises(ValueError, match="limit"):
            jm.create_job()

    def test_allows_new_jobs_after_expired_cleanup(self):
        """Expired jobs are cleaned up before checking the limit."""
        jm = JobManager(ttl_seconds=1800, max_jobs=2)
        old_id = jm.create_job()
        jm.create_job()
        # Expire the first job
        with jm._lock:
            jm._jobs[old_id]["created_at"] = time.time() - 1801
        # Should succeed because cleanup frees a slot
        new_id = jm.create_job()
        assert isinstance(new_id, str)

    def test_completed_jobs_count_toward_limit(self):
        """Completed but non-expired jobs still count."""
        jm = JobManager(ttl_seconds=1800, max_jobs=2)
        job1 = jm.create_job()
        jm.set_status(job1, JobStatus.COMPLETED)
        jm.create_job()
        with pytest.raises(ValueError, match="limit"):
            jm.create_job()
