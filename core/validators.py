#!/usr/bin/env python3
"""
Validators - Check whether a PDF can be opened and summarized from embedded text.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def validate_pdf(
    pdf_path: str | Path,
    min_text_characters: int = 20,
    verbose: bool = True,
) -> tuple[bool, dict]:
    """
    Validate a PDF for text-based summarization.

    Args:
        pdf_path: Path to PDF file.
        min_text_characters: Minimum extracted text required to mark it ready.
        verbose: Print validation details.

    Returns:
        Tuple of (passes, results).
    """
    path = Path(pdf_path)

    if not path.exists():
        return False, {"error": f"File not found: {path}", "passes": False}
    if path.suffix.lower() != ".pdf":
        return False, {"error": f"Not a PDF file: {path}", "passes": False}

    try:
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        if page_count == 0:
            return False, {"error": "PDF contains no pages", "passes": False}

        extracted_characters = 0
        pages_with_text = 0

        for page in reader.pages:
            text = (page.extract_text() or "").strip()
            extracted_characters += len(text)
            if text:
                pages_with_text += 1

        encrypted = bool(reader.is_encrypted)

    except Exception as exc:
        return False, {"error": f"Failed to read PDF: {exc}", "passes": False}

    passes = extracted_characters >= min_text_characters
    results = {
        "file": str(path),
        "passes": passes,
        "page_count": page_count,
        "pages_with_text": pages_with_text,
        "extracted_characters": extracted_characters,
        "encrypted": encrypted,
        "needs_ocr": not passes,
    }

    if verbose:
        print(f"\nValidating {path.name}:")
        print(f"  Pages: {page_count}")
        print(f"  Pages with extractable text: {pages_with_text}")
        print(f"  Extracted characters: {extracted_characters}")
        print(f"  Encrypted: {'yes' if encrypted else 'no'}")
        if passes:
            print("  Ready for text-based summarization")
        else:
            print("  Not enough extractable text; OCR may be required")

    return passes, results


def is_pdf_ready(
    pdf_path: str | Path,
    min_text_characters: int = 20,
    verbose: bool = True,
) -> bool:
    """Quick check whether a PDF is ready for text-based summarization."""
    passes, _ = validate_pdf(
        pdf_path,
        min_text_characters=min_text_characters,
        verbose=verbose,
    )
    return passes
