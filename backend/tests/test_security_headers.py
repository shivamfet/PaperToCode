import pytest
from httpx import AsyncClient, ASGITransport

from main import app

EXPECTED_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "x-xss-protection": "1; mode=block",
    "referrer-policy": "strict-origin-when-cross-origin",
    "content-security-policy": "default-src 'self'",
}


class TestSecurityHeadersOnHealth:
    """Security headers must be present on GET /health."""

    @pytest.mark.anyio
    async def test_health_has_all_security_headers(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        for header, value in EXPECTED_HEADERS.items():
            assert resp.headers.get(header) == value, f"Missing or wrong: {header}"


class TestSecurityHeadersOnStatus:
    """Security headers must be present on GET /api/status."""

    @pytest.mark.anyio
    async def test_status_404_has_security_headers(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/status/nonexistent")
        assert resp.status_code == 404
        for header, value in EXPECTED_HEADERS.items():
            assert resp.headers.get(header) == value, f"Missing or wrong: {header}"


class TestSecurityHeadersOnDownload:
    """Security headers must be present on GET /api/download."""

    @pytest.mark.anyio
    async def test_download_404_has_security_headers(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/download/nonexistent")
        assert resp.status_code == 404
        for header, value in EXPECTED_HEADERS.items():
            assert resp.headers.get(header) == value, f"Missing or wrong: {header}"
