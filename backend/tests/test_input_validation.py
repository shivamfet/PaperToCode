import io

import pytest
from httpx import AsyncClient, ASGITransport
from reportlab.pdfgen import canvas

from main import app


def _make_pdf_bytes(text: str = "Hello world research paper content") -> bytes:
    """Create a minimal valid PDF with the given text."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.save()
    return buf.getvalue()


class TestFileSizeValidation:
    """Backend must reject files larger than 50 MB."""

    @pytest.mark.anyio
    async def test_rejects_file_over_50mb(self):
        """Files > 50 MB should return 413."""
        # Create a file just over 50 MB (50 * 1024 * 1024 + 1 bytes)
        oversized = b"%PDF-1.4 " + b"\x00" * (50 * 1024 * 1024 + 1)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                files={"file": ("big.pdf", oversized, "application/pdf")},
                data={"openai_api_key": "sk-test"},
            )
        assert response.status_code == 413
        assert "50 MB" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_accepts_file_under_50mb(self):
        """Valid PDF under 50 MB should not be rejected for size."""
        pdf_bytes = _make_pdf_bytes()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                files={"file": ("paper.pdf", pdf_bytes, "application/pdf")},
                data={"openai_api_key": "sk-test"},
            )
        # Should not be 413 (may be 200 with job_id since the file is valid)
        assert response.status_code != 413


class TestMagicBytesValidation:
    """Backend must validate PDF magic bytes, not just file extension."""

    @pytest.mark.anyio
    async def test_rejects_non_pdf_with_pdf_extension(self):
        """A .pdf file that isn't actually a PDF should be rejected."""
        fake_pdf = b"This is not a PDF file at all"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                files={"file": ("sneaky.pdf", fake_pdf, "application/pdf")},
                data={"openai_api_key": "sk-test"},
            )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_rejects_non_pdf_extension(self):
        """A .txt file should be rejected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                files={"file": ("notes.txt", b"just text", "text/plain")},
                data={"openai_api_key": "sk-test"},
            )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_accepts_valid_pdf(self):
        """A real PDF with correct magic bytes should pass validation."""
        pdf_bytes = _make_pdf_bytes()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                files={"file": ("paper.pdf", pdf_bytes, "application/pdf")},
                data={"openai_api_key": "sk-test"},
            )
        # Should pass validation (200 with job_id)
        assert response.status_code == 200
        assert "job_id" in response.json()

    @pytest.mark.anyio
    async def test_rejects_zip_disguised_as_pdf(self):
        """A ZIP file renamed to .pdf should be rejected via magic bytes."""
        # ZIP magic bytes: PK\x03\x04
        zip_bytes = b"PK\x03\x04" + b"\x00" * 100
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                files={"file": ("archive.pdf", zip_bytes, "application/pdf")},
                data={"openai_api_key": "sk-test"},
            )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_rejects_empty_file(self):
        """An empty file should be rejected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/convert",
                files={"file": ("empty.pdf", b"", "application/pdf")},
                data={"openai_api_key": "sk-test"},
            )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]
