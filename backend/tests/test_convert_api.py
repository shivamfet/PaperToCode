import asyncio
import io
import json

import pytest
from httpx import AsyncClient, ASGITransport
from reportlab.pdfgen import canvas
from unittest.mock import patch

from main import app, job_manager


def _make_pdf_bytes(text: str = "Hello world research paper content") -> bytes:
    """Create a minimal valid PDF with the given text."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.save()
    return buf.getvalue()


MOCK_TUTORIAL = {
    "title": "Test Paper",
    "authors": ["Test Author"],
    "summary": "A test summary.",
    "math_foundations": [{"name": "Eq1", "latex": "x=1", "explanation": "Simple."}],
    "algorithms": [
        {
            "name": "Algo1",
            "pseudocode": "step 1",
            "implementation": "x = 1",
            "synthetic_data": "data = [1,2,3]",
        }
    ],
    "visualizations": [{"title": "Plot1", "code": "print('plot')"}],
    "ablation_study": {"description": "Test ablation", "code": "print('ablation')"},
    "exercises": [{"question": "Q1?", "hint": "H1"}],
    "references": ["Ref 1"],
}


class TestPostConvert:
    """Tests for POST /api/convert."""

    @pytest.mark.anyio
    @patch("main.generate_tutorial", return_value=MOCK_TUTORIAL)
    @patch("main.extract_text_from_pdf", return_value="--- Page 1 ---\nExtracted text")
    async def test_returns_job_id(self, mock_extract, mock_generate):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                files={"file": ("paper.pdf", _make_pdf_bytes(), "application/pdf")},
                headers={"X-API-Key": "sk-test-key"},
            )
        assert response.status_code == 200
        assert "job_id" in response.json()

    @pytest.mark.anyio
    async def test_rejects_missing_file(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                headers={"X-API-Key": "sk-test-key"},
            )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_rejects_missing_api_key_header(self):
        """Missing X-API-Key header should return 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                files={"file": ("paper.pdf", _make_pdf_bytes(), "application/pdf")},
            )
        assert response.status_code == 401
        assert "API key" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_rejects_empty_api_key_header(self):
        """Empty X-API-Key header should return 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                files={"file": ("paper.pdf", _make_pdf_bytes(), "application/pdf")},
                headers={"X-API-Key": ""},
            )
        assert response.status_code == 401
        assert "API key" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_rejects_non_pdf_file(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                files={"file": ("doc.txt", b"not a pdf", "text/plain")},
                headers={"X-API-Key": "sk-test-key"},
            )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]


class TestJobLifecycle:
    """Tests for the full job lifecycle: convert -> status -> download."""

    @pytest.mark.anyio
    @patch("main.generate_tutorial", return_value=MOCK_TUTORIAL)
    @patch("main.extract_text_from_pdf", return_value="--- Page 1 ---\nExtracted text")
    async def test_successful_conversion(self, mock_extract, mock_generate):
        """Full pipeline: submit -> poll status -> download notebook."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Submit
            resp = await client.post(
                "/api/convert",
                files={"file": ("paper.pdf", _make_pdf_bytes(), "application/pdf")},
                headers={"X-API-Key": "sk-test"},
            )
            job_id = resp.json()["job_id"]

            # Wait for background processing
            await asyncio.sleep(1.0)

            # Check status
            status_resp = await client.get(f"/api/status/{job_id}")
            assert status_resp.status_code == 200
            status_data = status_resp.json()
            assert status_data["status"] == "completed"
            assert len(status_data["messages"]) > 0
            assert status_data["error"] is None

            # Download
            dl_resp = await client.get(f"/api/download/{job_id}")
            assert dl_resp.status_code == 200
            assert "application/octet-stream" in dl_resp.headers.get("content-type", "")
            nb_data = json.loads(dl_resp.content)
            assert "cells" in nb_data
            assert "nbformat" in nb_data

    @pytest.mark.anyio
    @patch("main.generate_tutorial", side_effect=ValueError("Invalid OpenAI API key"))
    @patch("main.extract_text_from_pdf", return_value="text")
    async def test_bad_api_key_sets_auth_error(self, mock_extract, mock_generate):
        """Auth errors are stored in job status with AUTH: prefix."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/convert",
                files={"file": ("paper.pdf", _make_pdf_bytes(), "application/pdf")},
                headers={"X-API-Key": "sk-bad"},
            )
            job_id = resp.json()["job_id"]
            await asyncio.sleep(0.5)

            status_resp = await client.get(f"/api/status/{job_id}")
            data = status_resp.json()
            assert data["status"] == "failed"
            assert "AUTH:" in data["error"]

    @pytest.mark.anyio
    @patch("main.generate_tutorial", side_effect=ValueError("rate limit exceeded"))
    @patch("main.extract_text_from_pdf", return_value="text")
    async def test_generation_error_sets_failed(self, mock_extract, mock_generate):
        """Non-auth errors are stored as regular failures."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/convert",
                files={"file": ("paper.pdf", _make_pdf_bytes(), "application/pdf")},
                headers={"X-API-Key": "sk-test"},
            )
            job_id = resp.json()["job_id"]
            await asyncio.sleep(0.5)

            status_resp = await client.get(f"/api/status/{job_id}")
            data = status_resp.json()
            assert data["status"] == "failed"
            assert "rate limit" in data["error"]

    @pytest.mark.anyio
    @patch("main.extract_text_from_pdf", side_effect=ValueError("no extractable text"))
    async def test_pdf_extraction_error(self, mock_extract):
        """PDF extraction errors are stored in job status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/convert",
                files={"file": ("paper.pdf", _make_pdf_bytes(), "application/pdf")},
                headers={"X-API-Key": "sk-test"},
            )
            job_id = resp.json()["job_id"]
            await asyncio.sleep(0.5)

            status_resp = await client.get(f"/api/status/{job_id}")
            data = status_resp.json()
            assert data["status"] == "failed"
            assert "extractable text" in data["error"]

    @pytest.mark.anyio
    @patch("main.generate_tutorial", return_value=MOCK_TUTORIAL)
    @patch("main.extract_text_from_pdf", return_value="--- Page 1 ---\ntext")
    async def test_status_messages_are_descriptive(self, mock_extract, mock_generate):
        """Status messages include specific information."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/convert",
                files={"file": ("paper.pdf", _make_pdf_bytes(), "application/pdf")},
                headers={"X-API-Key": "sk-test"},
            )
            job_id = resp.json()["job_id"]
            await asyncio.sleep(1.0)

            status_resp = await client.get(f"/api/status/{job_id}")
            messages = status_resp.json()["messages"]
            assert any("Extracting" in m for m in messages)
            assert any("page" in m.lower() for m in messages)
            assert any("notebook" in m.lower() or "Notebook" in m for m in messages)


class TestStatusEndpoint:
    """Tests for GET /api/status/{job_id}."""

    @pytest.mark.anyio
    async def test_returns_404_for_unknown_job(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/status/nonexistent-job-id")
        assert response.status_code == 404


class TestDownloadEndpoint:
    """Tests for GET /api/download/{job_id}."""

    @pytest.mark.anyio
    async def test_returns_404_for_unknown_job(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/download/nonexistent")
        assert response.status_code == 404
