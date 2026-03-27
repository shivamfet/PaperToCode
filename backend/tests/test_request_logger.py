import json
import logging

import pytest
from httpx import AsyncClient, ASGITransport

from main import app


class TestRequestLogFormat:
    """Request logs should be structured JSON with required fields."""

    @pytest.mark.anyio
    async def test_log_contains_required_fields(self, caplog):
        """Each request should log method, path, status_code, client_ip, duration_ms."""
        with caplog.at_level(logging.INFO, logger="request_logger"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.get("/health")

        # Find the JSON log line
        log_entries = [r for r in caplog.records if r.name == "request_logger"]
        assert len(log_entries) >= 1

        entry = json.loads(log_entries[-1].message)
        assert entry["method"] == "GET"
        assert entry["path"] == "/health"
        assert entry["status_code"] == 200
        assert "client_ip" in entry
        assert "duration_ms" in entry
        assert isinstance(entry["duration_ms"], (int, float))
        assert "timestamp" in entry

    @pytest.mark.anyio
    async def test_log_captures_404_status(self, caplog):
        with caplog.at_level(logging.INFO, logger="request_logger"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.get("/api/status/nonexistent")

        log_entries = [r for r in caplog.records if r.name == "request_logger"]
        assert len(log_entries) >= 1
        entry = json.loads(log_entries[-1].message)
        assert entry["status_code"] == 404


class TestSensitiveDataExclusion:
    """Logs must NOT contain API keys or request bodies."""

    @pytest.mark.anyio
    async def test_api_key_not_logged(self, caplog):
        """X-API-Key header value must not appear in logs."""
        secret_key = "sk-super-secret-key-12345"
        with caplog.at_level(logging.INFO, logger="request_logger"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.post(
                    "/api/convert",
                    headers={"X-API-Key": secret_key},
                )

        log_entries = [r for r in caplog.records if r.name == "request_logger"]
        for entry in log_entries:
            assert secret_key not in entry.message

    @pytest.mark.anyio
    async def test_request_body_not_logged(self, caplog):
        """Request body content must not appear in logs."""
        with caplog.at_level(logging.INFO, logger="request_logger"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.post(
                    "/api/convert",
                    headers={"X-API-Key": "sk-test"},
                    files={"file": ("paper.pdf", b"%PDF-1.4 test content", "application/pdf")},
                )

        log_entries = [r for r in caplog.records if r.name == "request_logger"]
        for entry in log_entries:
            assert "test content" not in entry.message
