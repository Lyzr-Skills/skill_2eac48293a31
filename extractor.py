"""
extractor.py
------------
Handles PDF text extraction using pdfplumber.
Supports single and multi-page documents with section detection.
"""

import pdfplumber
import os
import re
from typing import List, Dict, Optional


def extract_text_from_pdf(pdf_path: str) -> Dict:
    """
    Extract full text and metadata from a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A dict with keys:
            - 'file': filename
            - 'total_pages': int
            - 'pages': list of {'page_num': int, 'text': str}
            - 'full_text': concatenated text of all pages
            - 'sections': list of {'title': str, 'content': str} (if detected)
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    pages = []
    full_text_parts = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            pages.append({"page_num": i, "text": text})
            if text:
                full_text_parts.append(text)

    full_text = "\n\n".join(full_text_parts)
    sections = detect_sections(full_text)

    return {
        "file": os.path.basename(pdf_path),
        "path": pdf_path,
        "total_pages": total_pages,
        "pages": pages,
        "full_text": full_text,
        "sections": sections,
    }


def detect_sections(text: str) -> List[Dict]:
    """
    Attempt to detect sections/chapters in the text using common heading patterns.

    Args:
        text: Full document text.

    Returns:
        List of {'title': str, 'content': str} dicts.
    """
    # Common heading patterns: ALL CAPS lines, numbered sections, "Chapter X", etc.
    heading_pattern = re.compile(
        r"(?m)^(?:"
        r"(?:Chapter|Section|Part)\s+[\dIVXivx]+[:\.\s].*|"  # Chapter/Section/Part headings
        r"\d+[\.\d]*\s+[A-Z][^\n]{3,50}|"                    # Numbered headings e.g. "1.2 Introduction"
        r"[A-Z][A-Z\s]{4,60}$"                                # ALL CAPS headings
        r")"
    )

    matches = list(heading_pattern.finditer(text))

    if len(matches) < 2:
        # Not enough structure detected — return as a single section
        return [{"title": "Document", "content": text}]

    sections = []
    for idx, match in enumerate(matches):
        title = match.group().strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections.append({"title": title, "content": content})

    return sections


def extract_multiple_pdfs(pdf_paths: List[str]) -> List[Dict]:
    """
    Extract text from multiple PDF files.

    Args:
        pdf_paths: List of file paths.

    Returns:
        List of extraction result dicts.
    """
    results = []
    for path in pdf_paths:
        try:
            result = extract_text_from_pdf(path)
            results.append(result)
            print(f"  ✅ Extracted: {result['file']} ({result['total_pages']} pages)")
        except Exception as e:
            print(f"  ❌ Failed to extract {path}: {e}")
            results.append({
                "file": os.path.basename(path),
                "path": path,
                "error": str(e),
                "total_pages": 0,
                "pages": [],
                "full_text": "",
                "sections": [],
            })
    return results
