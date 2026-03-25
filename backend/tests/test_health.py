import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.anyio
async def test_health_returns_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_cors_allows_nextjs_origin():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert "http://localhost:3000" in response.headers.get(
        "access-control-allow-origin", ""
    )


@pytest.mark.anyio
async def test_cors_blocks_unknown_origin():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
    allow_origin = response.headers.get("access-control-allow-origin", "")
    assert "http://evil.com" not in allow_origin


@pytest.mark.anyio
async def test_health_returns_json_content_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert "application/json" in response.headers.get("content-type", "")
