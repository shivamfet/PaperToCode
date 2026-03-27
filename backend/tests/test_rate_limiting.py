import io

import pytest
from httpx import AsyncClient, ASGITransport
from reportlab.pdfgen import canvas
from unittest.mock import patch

from main import app


def _make_pdf_bytes(text: str = "Hello world research paper content") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.save()
    return buf.getvalue()


MOCK_TUTORIAL = {
    "title": "Test",
    "authors": ["A"],
    "summary": "S",
    "math_foundations": [],
    "algorithms": [],
    "visualizations": [],
    "ablation_study": {"description": "d", "code": "c"},
    "exercises": [],
    "references": [],
}


class TestConvertRateLimit:
    """POST /api/convert should be limited to 5 requests/minute."""

    @pytest.mark.anyio
    @patch("main.generate_tutorial", return_value=MOCK_TUTORIAL)
    @patch("main.extract_text_from_pdf", return_value="--- Page 1 ---\ntext")
    async def test_convert_rate_limit_triggers_429(self, mock_ext, mock_gen):
        """6th request within a minute should return 429."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for i in range(5):
                resp = await client.post(
                    "/api/convert",
                    files={"file": ("paper.pdf", _make_pdf_bytes(), "application/pdf")},
                    headers={"X-API-Key": "sk-test"},
                )
                assert resp.status_code == 200, f"Request {i+1} should succeed"

            # 6th request should be rate limited
            resp = await client.post(
                "/api/convert",
                files={"file": ("paper.pdf", _make_pdf_bytes(), "application/pdf")},
                headers={"X-API-Key": "sk-test"},
            )
            assert resp.status_code == 429


class TestHealthNotRateLimited:
    """GET /health should not be rate limited."""

    @pytest.mark.anyio
    async def test_health_not_rate_limited(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(50):
                resp = await client.get("/health")
                assert resp.status_code == 200


class TestStatusRateLimit:
    """GET /api/status should be limited to 30 requests/minute."""

    @pytest.mark.anyio
    async def test_status_rate_limit_triggers_429(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for i in range(30):
                resp = await client.get("/api/status/fake-id")
                # 404 is fine — we just care it's not 429 yet
                assert resp.status_code in (200, 404), f"Request {i+1} should not be rate limited"

            # 31st should be rate limited
            resp = await client.get("/api/status/fake-id")
            assert resp.status_code == 429


class TestDownloadRateLimit:
    """GET /api/download should be limited to 10 requests/minute."""

    @pytest.mark.anyio
    async def test_download_rate_limit_triggers_429(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for i in range(10):
                resp = await client.get("/api/download/fake-id")
                assert resp.status_code in (200, 400, 404), f"Request {i+1} should not be rate limited"

            # 11th should be rate limited
            resp = await client.get("/api/download/fake-id")
            assert resp.status_code == 429
