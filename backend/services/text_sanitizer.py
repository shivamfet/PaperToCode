"""Sanitize PDF-extracted text to mitigate prompt injection attacks."""

import re

# Patterns that attempt to override LLM instructions (case-insensitive, line-level)
_INJECTION_PATTERNS = [
    re.compile(r"^.*ignore\s+(all\s+)?previous\s+instructions.*$", re.IGNORECASE),
    re.compile(r"^.*ignore\s+all\s+instructions.*$", re.IGNORECASE),
    re.compile(r"^.*do\s+not\s+follow.*instructions.*$", re.IGNORECASE),
    re.compile(r"^.*you\s+are\s+now\b.*$", re.IGNORECASE),
    re.compile(r"^\s*system\s*:.*$", re.IGNORECASE),
    re.compile(r"^\s*assistant\s*:.*$", re.IGNORECASE),
    re.compile(r"^\s*user\s*:.*$", re.IGNORECASE),
]

# HTML/Markdown injection patterns (inline)
_INLINE_STRIP_PATTERNS = [
    re.compile(r"<script[\s>].*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<iframe[\s>].*?</iframe>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<script[^>]*>", re.IGNORECASE),
    re.compile(r"</script>", re.IGNORECASE),
    re.compile(r"<iframe[^>]*>", re.IGNORECASE),
    re.compile(r"</iframe>", re.IGNORECASE),
    re.compile(r"!\[.*?\]\(.*?\)"),  # Markdown image injection
]


def sanitize_pdf_text(text: str) -> str:
    """Remove prompt injection patterns and excessive whitespace from PDF text.

    Designed to be called before sending extracted text to the LLM.
    Normal academic content (LaTeX, code, references) passes through unchanged.
    """
    if not text:
        return text

    # Strip HTML/Markdown injection patterns (inline)
    for pattern in _INLINE_STRIP_PATTERNS:
        text = pattern.sub("", text)

    # Filter lines that match prompt injection patterns
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        if any(p.match(line) for p in _INJECTION_PATTERNS):
            continue
        clean_lines.append(line)
    text = "\n".join(clean_lines)

    # Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {5,}", "  ", text)

    return text
