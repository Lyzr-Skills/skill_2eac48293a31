#!/usr/bin/env python3
"""
Summarizer - Lightweight deterministic extractive summarization utilities.

This module intentionally does not call an external LLM. It provides a local
baseline summary that can be replaced by semantic/LLM summarization when available.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable, Optional


_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\[])")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]{1,}")

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by",
    "can", "could", "did", "do", "does", "for", "from", "had", "has", "have",
    "he", "her", "hers", "him", "his", "how", "i", "if", "in", "into", "is",
    "it", "its", "may", "might", "more", "most", "not", "of", "on", "or", "our",
    "ours", "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "then", "there", "these", "they", "this", "those", "to", "too",
    "us", "was", "we", "were", "what", "when", "where", "which", "who", "why", "will",
    "with", "would", "you", "your", "yours"
}


def split_sentences(text: str) -> list[str]:
    """Split text into reasonably clean sentences."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []

    sentences = [part.strip() for part in _SENTENCE_RE.split(text) if part.strip()]
    if len(sentences) == 1:
        sentences = [
            part.strip()
            for part in re.split(r"(?<=[.!?])\s+|\s+[•▪◦]\s+", text)
            if part.strip()
        ]
    return sentences


def _keywords(text: str) -> list[str]:
    words = [word.lower() for word in _WORD_RE.findall(text)]
    return [word for word in words if word not in _STOPWORDS and len(word) > 2]


def summarize_text(
    text: str,
    max_sentences: int = 8,
    focus_terms: Optional[Iterable[str]] = None,
) -> str:
    """
    Create an extractive summary by ranking sentences with keyword frequency.

    Args:
        text: Source text.
        max_sentences: Maximum number of source sentences to include.
        focus_terms: Optional terms that receive extra ranking weight.

    Returns:
        Summary string containing selected source sentences in source order.
    """
    if max_sentences < 1:
        raise ValueError("max_sentences must be at least 1")

    sentences = split_sentences(text)
    if not sentences:
        return ""
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    all_keywords = _keywords(text)
    frequencies = Counter(all_keywords)
    if frequencies:
        max_frequency = max(frequencies.values())
        weights = {word: count / max_frequency for word, count in frequencies.items()}
    else:
        weights = {}

    focus = {term.strip().lower() for term in (focus_terms or []) if term and term.strip()}

    scored: list[tuple[float, int, str]] = []
    for index, sentence in enumerate(sentences):
        words = _keywords(sentence)
        if not words:
            continue

        # Frequency score normalized to reduce the advantage of very long sentences.
        score = sum(weights.get(word, 0.0) for word in words)
        score /= math.sqrt(max(len(words), 1))

        lower_sentence = sentence.lower()
        for term in focus:
            if term in lower_sentence:
                score += 1.5

        # Small preference for earlier sentences because introductions often carry context.
        score += max(0.0, 0.2 - index * 0.002)

        scored.append((score, index, sentence))

    if not scored:
        return " ".join(sentences[:max_sentences])

    top = sorted(scored, key=lambda item: item[0], reverse=True)[:max_sentences]
    top_in_order = sorted(top, key=lambda item: item[1])
    return " ".join(sentence for _, _, sentence in top_in_order)


def summarize_pages(
    pages: Iterable[dict],
    sentences_per_page: int = 2,
    focus_terms: Optional[Iterable[str]] = None,
) -> list[dict]:
    """Create a compact extractive summary for each extracted PDF page."""
    results = []
    for page in pages:
        results.append(
            {
                "page": page.get("page"),
                "summary": summarize_text(
                    page.get("text", ""),
                    max_sentences=sentences_per_page,
                    focus_terms=focus_terms,
                ),
            }
        )
    return results
