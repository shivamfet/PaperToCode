import io
import pdfplumber


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file, returning text with page markers.

    Args:
        file_bytes: Raw bytes of a PDF file.

    Returns:
        Extracted text with '--- Page N ---' markers between pages.

    Raises:
        ValueError: If the input is not a valid PDF or contains no extractable text.
    """
    try:
        pdf = pdfplumber.open(io.BytesIO(file_bytes))
    except Exception:
        raise ValueError("Invalid PDF: could not parse the file.")

    pages = []
    for i, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append(f"--- Page {i} ---\n{text}")
        else:
            pages.append(f"--- Page {i} ---")

    pdf.close()

    full_text = "\n\n".join(pages)

    # Check if any actual text was extracted
    has_text = any(
        line.strip() and not line.strip().startswith("--- Page")
        for line in full_text.split("\n")
    )
    if not has_text:
        raise ValueError("PDF contains no extractable text (possibly scanned/image-based).")

    return full_text
