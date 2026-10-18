#!/usr/bin/env python3
"""
PDF Extractor - Extract text and metadata from PDF documents.

Pages passed to extract_pdf are 1-indexed for convenience.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from pypdf import PdfReader


def _clean_text(text: str) -> str:
    """Normalize common whitespace issues without changing document meaning."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    cleaned: list[str] = []
    blank = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if cleaned and not blank:
                cleaned.append("")
            blank = True
            continue
        cleaned.append(stripped)
        blank = False

    return "\n".join(cleaned).strip()


def extract_pdf(
    pdf_path: str | Path,
    pages: Optional[Iterable[int]] = None,
    include_page_markers: bool = True,
) -> dict:
    """
    Extract text and metadata from a PDF.

    Args:
        pdf_path: Path to PDF file.
        pages: Optional iterable of 1-indexed page numbers. Defaults to all pages.
        include_page_markers: Prefix each page's text with a page marker.

    Returns:
        Dictionary containing path, metadata, page_count, selected_pages,
        per-page text, combined text, and extraction statistics.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file: {path}")

    reader = PdfReader(str(path))
    total_pages = len(reader.pages)

    if pages is None:
        selected = list(range(1, total_pages + 1))
    else:
        selected = sorted(set(int(page) for page in pages))
        invalid = [page for page in selected if page < 1 or page > total_pages]
        if invalid:
            raise ValueError(
                f"Invalid page number(s): {invalid}. PDF has {total_pages} page(s)."
            )

    page_texts = []
    combined_parts = []

    for page_number in selected:
        page = reader.pages[page_number - 1]
        raw_text = page.extract_text() or ""
        clean_text = _clean_text(raw_text)

        page_texts.append(
            {
                "page": page_number,
                "text": clean_text,
                "characters": len(clean_text),
            }
        )

        if include_page_markers:
            combined_parts.append(f"[Page {page_number}]\n{clean_text}".strip())
        else:
            combined_parts.append(clean_text)

    metadata = reader.metadata or {}

    def _meta(name: str):
        value = getattr(metadata, name, None)
        return str(value).strip() if value else None

    combined_text = "\n\n".join(part for part in combined_parts if part).strip()
    nonempty_pages = sum(1 for item in page_texts if item["text"])

    return {
        "path": str(path),
        "filename": path.name,
        "title": _meta("title"),
        "author": _meta("author"),
        "subject": _meta("subject"),
        "page_count": total_pages,
        "selected_pages": selected,
        "nonempty_pages": nonempty_pages,
        "characters": len(combined_text),
        "pages": page_texts,
        "text": combined_text,
    }
