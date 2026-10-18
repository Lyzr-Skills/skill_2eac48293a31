"""
summariser.py
-------------
Handles all LLM-based summarisation logic via the OpenAI API.
Supports:
  - Chunk-level and document-level summarisation
  - Section-by-section summarisation
  - Keyword/theme extraction
  - Configurable depth and model selection
"""

import os
from typing import List, Dict, Optional

from openai import OpenAI
from dotenv import load_dotenv

from utils import chunk_text, merge_summaries

load_dotenv()

# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------

DEPTH_INSTRUCTIONS = {
    "short": (
        "Provide a SHORT summary in 2-4 sentences. "
        "Capture only the most critical points."
    ),
    "medium": (
        "Provide a MEDIUM-LENGTH summary in 1-2 paragraphs (6-10 sentences). "
        "Cover the main ideas, key arguments, and important conclusions."
    ),
    "detailed": (
        "Provide a DETAILED summary covering all major points, supporting evidence, "
        "conclusions, and any notable data or statistics mentioned. "
        "Use multiple paragraphs as needed."
    ),
}

KEYWORD_PROMPT = (
    "Extract 5-10 key topics, themes, or keywords from the following text. "
    "Return ONLY a comma-separated list of keywords, nothing else.\n\n"
    "TEXT:\n{text}"
)

SECTION_PROMPT = (
    "Summarise the following section titled '{title}' in 2-4 sentences.\n\n"
    "SECTION CONTENT:\n{content}"
)

CHUNK_SUMMARY_PROMPT = (
    "You are a professional document summariser.\n"
    "{depth_instruction}\n\n"
    "TEXT CHUNK ({chunk_num} of {total_chunks}):\n{text}"
)

MERGE_PROMPT = (
    "You are a professional document summariser.\n"
    "Below are partial summaries of different sections of a single document. "
    "Combine them into one coherent, well-structured final summary.\n"
    "{depth_instruction}\n\n"
    "PARTIAL SUMMARIES:\n{summaries}"
)

SINGLE_DOC_PROMPT = (
    "You are a professional document summariser.\n"
    "{depth_instruction}\n\n"
    "DOCUMENT TEXT:\n{text}"
)


# ---------------------------------------------------------------------------
# Core Summariser Class
# ---------------------------------------------------------------------------

class PDFSummariser:
    """Orchestrates extraction → chunking → summarisation → keyword extraction."""

    def __init__(
        self,
        model: str = "gpt-4o",
        depth: str = "medium",
        extract_keywords: bool = False,
        summarise_sections: bool = False,
        max_chunk_tokens: int = 6000,
    ):
        """
        Args:
            model:               OpenAI model name.
            depth:               'short' | 'medium' | 'detailed'
            extract_keywords:    Whether to extract key topics.
            summarise_sections:  Whether to summarise each detected section.
            max_chunk_tokens:    Token budget per chunk.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not found. Set it in your environment or .env file."
            )
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.depth = depth
        self.depth_instruction = DEPTH_INSTRUCTIONS.get(depth, DEPTH_INSTRUCTIONS["medium"])
        self.extract_keywords = extract_keywords
        self.summarise_sections = summarise_sections
        self.max_chunk_tokens = max_chunk_tokens

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def summarise_document(self, extracted: Dict) -> Dict:
        """
        Summarise a single extracted document dict (from extractor.py).

        Args:
            extracted: Output of extractor.extract_text_from_pdf()

        Returns:
            Dict with keys: file, summary, keywords (opt), sections (opt), error (opt)
        """
        file_name = extracted.get("file", "unknown")
        full_text = extracted.get("full_text", "")

        if extracted.get("error"):
            return {"file": file_name, "summary": "", "error": extracted["error"]}

        if not full_text.strip():
            return {
                "file": file_name,
                "summary": "No extractable text found in this PDF.",
            }

        print(f"\n📄 Summarising: {file_name}")

        # Step 1 — Summarise main content (chunked if necessary)
        summary = self._summarise_text(full_text, file_name)

        result: Dict = {"file": file_name, "summary": summary}

        # Step 2 — Optional keyword extraction
        if self.extract_keywords:
            print("  🔍 Extracting keywords...")
            result["keywords"] = self._extract_keywords(full_text)

        # Step 3 — Optional section-level summaries
        if self.summarise_sections:
            sections = extracted.get("sections", [])
            if sections and not (len(sections) == 1 and sections[0]["title"] == "Document"):
                print(f"  📂 Summarising {len(sections)} sections...")
                result["sections"] = self._summarise_sections(sections)

        return result

    def summarise_all(self, extracted_list: List[Dict]) -> List[Dict]:
        """
        Summarise a list of extracted documents.

        Args:
            extracted_list: List of dicts from extractor.extract_multiple_pdfs()

        Returns:
            List of summary result dicts.
        """
        return [self.summarise_document(doc) for doc in extracted_list]

    # ------------------------------------------------------------------
    # Internal Methods
    # ------------------------------------------------------------------

    def _call_llm(self, prompt: str) -> str:
        """Send a prompt to the OpenAI API and return the response text."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def _summarise_text(self, text: str, label: str = "document") -> str:
        """
        Summarise a block of text, chunking if necessary.

        Args:
            text:  Full text to summarise.
            label: Label used for progress messages.

        Returns:
            Final summary string.
        """
        chunks = chunk_text(text, max_tokens=self.max_chunk_tokens, model=self.model)
        total = len(chunks)

        if total == 1:
            # Fits in one call
            print(f"  ⚡ Single-pass summarisation ({total} chunk)...")
            prompt = SINGLE_DOC_PROMPT.format(
                depth_instruction=self.depth_instruction,
                text=chunks[0],
            )
            return self._call_llm(prompt)

        # Multi-chunk: summarise each chunk, then merge
        print(f"  🔄 Multi-chunk summarisation ({total} chunks)...")
        partial_summaries: List[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            print(f"    Chunk {idx}/{total}...")
            prompt = CHUNK_SUMMARY_PROMPT.format(
                depth_instruction=self.depth_instruction,
                chunk_num=idx,
                total_chunks=total,
                text=chunk,
            )
            partial = self._call_llm(prompt)
            partial_summaries.append(partial)

        # Merge partials
        print("  🔗 Merging chunk summaries...")
        merge_prompt = MERGE_PROMPT.format(
            depth_instruction=self.depth_instruction,
            summaries="\n\n---\n\n".join(partial_summaries),
        )
        return self._call_llm(merge_prompt)

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract key topics/keywords from a text block.

        Args:
            text: Document text (will be truncated if too long).

        Returns:
            List of keyword strings.
        """
        # Use first ~3000 tokens for keyword extraction
        truncated = " ".join(text.split()[:2000])
        prompt = KEYWORD_PROMPT.format(text=truncated)
        raw = self._call_llm(prompt)
        keywords = [kw.strip() for kw in raw.split(",") if kw.strip()]
        return keywords

    def _summarise_sections(self, sections: List[Dict]) -> List[Dict]:
        """
        Summarise each detected section individually.

        Args:
            sections: List of {'title': str, 'content': str} dicts.

        Returns:
            List of {'title': str, 'summary': str} dicts.
        """
        results = []
        for sec in sections:
            title = sec.get("title", "Section")
            content = sec.get("content", "")
            if not content.strip():
                continue
            # Truncate very long sections for individual prompts
            truncated = " ".join(content.split()[:1500])
            prompt = SECTION_PROMPT.format(title=title, content=truncated)
            summary = self._call_llm(prompt)
            results.append({"title": title, "summary": summary})
        return results
