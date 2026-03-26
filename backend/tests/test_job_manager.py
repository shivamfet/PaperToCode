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
