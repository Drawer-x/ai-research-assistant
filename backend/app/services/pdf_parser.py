"""Utilities for extracting text and basic metadata from PDF papers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_ABSTRACT_RE = re.compile(
    r"(?is)\babstract\s*[:.\-—]?\s*(.+?)(?=\n\s*(?:1\.?\s+)?(?:introduction|keywords?)\b)"
)
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[ \t]+", " ", value.replace("\x00", "")).strip()


def _title_from_first_page(page: Any) -> str:
    """Choose the largest non-empty text block near the top of page one."""
    candidates: list[tuple[float, float, str]] = []
    page_height = float(page.rect.height or 1)
    for block in page.get_text("dict").get("blocks", []):
        if "lines" not in block:
            continue
        spans = [span for line in block["lines"] for span in line.get("spans", [])]
        text = _clean_text(" ".join(span.get("text", "") for span in spans))
        if not text or len(text) > 500:
            continue
        y_position = float(block.get("bbox", (0, 0, 0, 0))[1])
        if y_position > page_height * 0.45:
            continue
        font_size = max((float(span.get("size", 0)) for span in spans), default=0)
        candidates.append((font_size, -y_position, text))
    return max(candidates, default=(0, 0, ""))[2]


def _extract_abstract(full_text: str) -> str:
    match = _ABSTRACT_RE.search(full_text[:30_000])
    if not match:
        return ""
    abstract = re.sub(r"\s*\n\s*", " ", match.group(1))
    return _clean_text(abstract)[:10_000]


def extract_text_from_pdf(pdf_path: str | Path) -> dict:
    """Extract pages, full text and best-effort paper metadata.

    Parsing failures are represented by an empty result so callers can still
    persist an upload with ``parse_status=failed``.
    """
    result = {
        "title": "",
        "authors": "",
        "year": None,
        "venue": "",
        "abstract": "",
        "full_text": "",
        "pages": [],
    }
    try:
        import fitz

        with fitz.open(str(pdf_path)) as document:
            if document.needs_pass or document.page_count == 0:
                return result
            pages = [_clean_text(page.get_text("text")) for page in document]
            metadata = document.metadata or {}
            title = _clean_text(metadata.get("title"))
            if not title:
                title = _title_from_first_page(document[0])

        full_text = "\n\n".join(page for page in pages if page)
        year_match = _YEAR_RE.search(_clean_text(metadata.get("creationDate")))
        result.update(
            title=title,
            authors=_clean_text(metadata.get("author")),
            year=int(year_match.group()) if year_match else None,
            abstract=_extract_abstract(full_text),
            full_text=full_text,
            pages=pages,
        )
    # A malformed/encrypted PDF must not make the upload endpoint fail; the API
    # records it with parse_status="failed" instead.
    except Exception:
        pass
    return result
