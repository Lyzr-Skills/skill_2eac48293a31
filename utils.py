"""
utils.py
--------
Helper functions: token-aware chunking, text formatting, and file export.
"""

import json
import os
from typing import List, Dict, Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


# ---------------------------------------------------------------------------
# Token / Chunking Helpers
# ---------------------------------------------------------------------------

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Estimate the number of tokens in a string."""
    if TIKTOKEN_AVAILABLE:
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    # Fallback: rough word-based estimate
    return int(len(text.split()) * 1.35)


def chunk_text(text: str, max_tokens: int = 6000, model: str = "gpt-4o") -> List[str]:
    """
    Split text into chunks that fit within max_tokens.
    Splits on paragraph boundaries where possible.

    Args:
        text:       Full document text.
        max_tokens: Maximum tokens per chunk.
        model:      Model name (used for tokeniser selection).

    Returns:
        List of text chunks.
    """
    paragraphs = text.split("\n\n")
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para, model)

        # If a single paragraph exceeds the limit, force-split it by sentences
        if para_tokens > max_tokens:
            sentences = para.replace(". ", ".\n").split("\n")
            for sentence in sentences:
                s_tokens = count_tokens(sentence, model)
                if current_tokens + s_tokens > max_tokens:
                    if current_chunk:
                        chunks.append("\n\n".join(current_chunk))
                    current_chunk = [sentence]
                    current_tokens = s_tokens
                else:
                    current_chunk.append(sentence)
                    current_tokens += s_tokens
            continue

        if current_tokens + para_tokens > max_tokens:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_tokens = para_tokens
        else:
            current_chunk.append(para)
            current_tokens += para_tokens

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks if chunks else [text]


# ---------------------------------------------------------------------------
# Formatting Helpers
# ---------------------------------------------------------------------------

def format_output(summary_data: Dict, fmt: str = "text") -> str:
    """
    Format a summary result dict for display/export.

    Args:
        summary_data: Dict produced by summariser.py.
        fmt:          'text' | 'bullet' | 'json'

    Returns:
        Formatted string.
    """
    if fmt == "json":
        return json.dumps(summary_data, indent=2, ensure_ascii=False)

    file_name = summary_data.get("file", "Document")
    header = f"\n{'='*60}\nSUMMARY OF: {file_name}\n{'='*60}\n"

    if fmt == "bullet":
        lines = [header]
        # Convert summary sentences to bullets
        raw = summary_data.get("summary", "")
        bullets = _text_to_bullets(raw)
        lines.append(bullets)
        if summary_data.get("keywords"):
            lines.append("\n📌 KEY TOPICS: " + ", ".join(summary_data["keywords"]))
        if summary_data.get("sections"):
            lines.append("\n\n📂 SECTION SUMMARIES:")
            for sec in summary_data["sections"]:
                lines.append(f"\n  ▶ {sec['title']}")
                lines.append(_text_to_bullets(sec["summary"], indent="    "))
        return "\n".join(lines)

    # Default: plain text
    lines = [header, summary_data.get("summary", "")]
    if summary_data.get("keywords"):
        lines.append("\n📌 KEY TOPICS: " + ", ".join(summary_data["keywords"]))
    if summary_data.get("sections"):
        lines.append("\n\n📂 SECTION SUMMARIES:")
        for sec in summary_data["sections"]:
            lines.append(f"\n  ▶ {sec['title']}\n  {sec['summary']}")
    return "\n".join(lines)


def _text_to_bullets(text: str, indent: str = "") -> str:
    """Convert a paragraph of text into bullet points (split by sentence)."""
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return "\n".join(f"{indent}• {s}" for s in sentences if s)


# ---------------------------------------------------------------------------
# Export Helpers
# ---------------------------------------------------------------------------

def save_output(content: str, output_path: str) -> None:
    """
    Save formatted output to a file.

    Args:
        content:     String content to write.
        output_path: Destination file path.
    """
    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n💾 Output saved to: {output_path}")


def merge_summaries(summaries: List[str]) -> str:
    """
    Merge multiple chunk-level summaries into one coherent block.

    Args:
        summaries: List of partial summary strings.

    Returns:
        Joined summary string.
    """
    return " ".join(s.strip() for s in summaries if s.strip())
