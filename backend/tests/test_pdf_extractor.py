import pytest
from services.pdf_extractor import extract_text_from_pdf


def make_pdf_bytes(pages: list[str]) -> bytes:
    """Create a minimal valid PDF with the given page texts using reportlab."""
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for text in pages:
        c.drawString(72, 700, text)
        c.showPage()
    c.save()
    return buf.getvalue()


class TestExtractTextFromPdf:
    def test_extracts_text_from_single_page(self):
        pdf_bytes = make_pdf_bytes(["Hello World"])
        result = extract_text_from_pdf(pdf_bytes)
        assert "Hello World" in result

    def test_extracts_text_from_multiple_pages(self):
        pdf_bytes = make_pdf_bytes(["Page one content", "Page two content", "Page three content"])
        result = extract_text_from_pdf(pdf_bytes)
        assert "Page one content" in result
        assert "Page two content" in result
        assert "Page three content" in result

    def test_includes_page_markers(self):
        pdf_bytes = make_pdf_bytes(["First", "Second"])
        result = extract_text_from_pdf(pdf_bytes)
        assert "--- Page 1 ---" in result
        assert "--- Page 2 ---" in result

    def test_raises_for_empty_pdf(self):
        # A PDF with blank pages (no extractable text)
        pdf_bytes = make_pdf_bytes([""])
        with pytest.raises(ValueError, match="no extractable text"):
            extract_text_from_pdf(pdf_bytes)

    def test_raises_for_invalid_bytes(self):
        with pytest.raises(ValueError):
            extract_text_from_pdf(b"not a pdf")

    def test_handles_many_pages(self):
        pages = [f"Content on page {i}" for i in range(1, 52)]
        pdf_bytes = make_pdf_bytes(pages)
        result = extract_text_from_pdf(pdf_bytes)
        assert "--- Page 1 ---" in result
        assert "--- Page 51 ---" in result
        assert "Content on page 51" in result

    def test_returns_string(self):
        pdf_bytes = make_pdf_bytes(["Test"])
        result = extract_text_from_pdf(pdf_bytes)
        assert isinstance(result, str)

    def test_strips_excessive_whitespace(self):
        pdf_bytes = make_pdf_bytes(["Some text here"])
        result = extract_text_from_pdf(pdf_bytes)
        # Should not have excessive blank lines
        assert "\n\n\n" not in result
