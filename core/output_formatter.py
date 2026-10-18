#!/usr/bin/env python3
"""
Output Formatter - Format PDF summaries as readable Markdown.
"""

from __future__ import annotations

from typing import Iterable, Optional


def _clean_items(items: Optional[Iterable[str]]) -> list[str]:
    return [str(item).strip() for item in (items or []) if str(item).strip()]


def format_summary(
    title: str,
    summary: str,
    key_points: Optional[Iterable[str]] = None,
    action_items: Optional[Iterable[str]] = None,
    risks: Optional[Iterable[str]] = None,
    metadata: Optional[dict] = None,
) -> str:
    """Format summary components into Markdown."""
    title = (title or "PDF Summary").strip()
    sections = [f"# {title}"]

    if metadata:
        meta_lines = []
        if metadata.get("filename"):
            meta_lines.append(f"- File: {metadata['filename']}")
        if metadata.get("page_count") is not None:
            meta_lines.append(f"- Pages: {metadata['page_count']}")
        if metadata.get("author"):
            meta_lines.append(f"- Author: {metadata['author']}")
        if meta_lines:
            sections.append("## Document Info\n" + "\n".join(meta_lines))

    if summary and summary.strip():
        sections.append("## Summary\n" + summary.strip())

    points = _clean_items(key_points)
    if points:
        sections.append("## Key Points\n" + "\n".join(f"- {item}" for item in points))

    risk_items = _clean_items(risks)
    if risk_items:
        sections.append("## Risks / Issues\n" + "\n".join(f"- {item}" for item in risk_items))

    actions = _clean_items(action_items)
    if actions:
        sections.append("## Action Items\n" + "\n".join(f"- {item}" for item in actions))

    return "\n\n".join(sections).strip() + "\n"
