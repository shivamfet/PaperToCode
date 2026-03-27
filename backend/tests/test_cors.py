import pytest
from httpx import AsyncClient, ASGITransport

from main import app

ORIGIN = "http://localhost:3000"


class TestCorsAllowedMethods:
    """CORS should only allow GET and POST methods."""

    @pytest.mark.anyio
    async def test_preflight_allows_get(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.options(
                "/health",
                headers={
                    "Origin": ORIGIN,
                    "Access-Control-Request-Method": "GET",
                },
            )
        assert resp.headers.get("access-control-allow-methods") is not None
        allowed = resp.headers["access-control-allow-methods"]
        assert "GET" in allowed

    @pytest.mark.anyio
    async def test_preflight_allows_post(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.options(
                "/api/convert",
                headers={
                    "Origin": ORIGIN,
                    "Access-Control-Request-Method": "POST",
                },
            )
        allowed = resp.headers.get("access-control-allow-methods", "")
        assert "POST" in allowed

    @pytest.mark.anyio
    async def test_preflight_rejects_put(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.options(
                "/api/convert",
                headers={
                    "Origin": ORIGIN,
                    "Access-Control-Request-Method": "PUT",
                },
            )
        allowed = resp.headers.get("access-control-allow-methods", "")
        assert "PUT" not in allowed

    @pytest.mark.anyio
    async def test_preflight_rejects_delete(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.options(
                "/api/convert",
                headers={
                    "Origin": ORIGIN,
                    "Access-Control-Request-Method": "DELETE",
                },
            )
        allowed = resp.headers.get("access-control-allow-methods", "")
        assert "DELETE" not in allowed


class TestCorsAllowedHeaders:
    """CORS should only allow Content-Type, X-API-Key, and standard headers."""

    @pytest.mark.anyio
    async def test_preflight_allows_x_api_key(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.options(
                "/api/convert",
                headers={
                    "Origin": ORIGIN,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "X-API-Key",
                },
            )
        allowed = resp.headers.get("access-control-allow-headers", "")
        assert "x-api-key" in allowed.lower()

    @pytest.mark.anyio
    async def test_preflight_allows_content_type(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.options(
                "/api/convert",
                headers={
                    "Origin": ORIGIN,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type",
                },
            )
        allowed = resp.headers.get("access-control-allow-headers", "")
        assert "content-type" in allowed.lower()


class TestCorsCredentials:
    """allow_credentials should be False."""

    @pytest.mark.anyio
    async def test_no_credentials_header(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.options(
                "/health",
                headers={
                    "Origin": ORIGIN,
                    "Access-Control-Request-Method": "GET",
                },
            )
        # Should not have access-control-allow-credentials: true
        cred = resp.headers.get("access-control-allow-credentials")
        assert cred is None or cred != "true"
