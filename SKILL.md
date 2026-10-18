---
name: pdf-summarizer
description: Knowledge and utilities for extracting, validating, and summarizing PDF documents. Use when users ask to summarize a PDF, create executive summaries, extract key points, generate section-wise summaries, or identify action items from PDF content.
license: Complete terms in LICENSE.txt
---

# PDF Summarizer

A toolkit providing utilities and guidance for reliably extracting and summarizing PDF documents.

## Supported Tasks

Use this skill when the user asks to:
- Summarize an entire PDF.
- Create a short, medium, or detailed summary.
- Produce an executive summary.
- Summarize page-by-page or section-by-section.
- Extract key points, findings, decisions, risks, or action items.
- Focus the summary on specific topics or keywords.
- Validate whether a PDF contains usable extractable text.

## Core Principles

### Stay grounded in the PDF
Summaries must be based on the content actually present in the document.
- Do not invent facts, numbers, names, dates, or conclusions.
- Preserve important terminology used in the source.
- Clearly state when requested information is not present in the PDF.
- Distinguish source content from any additional interpretation.

### Preserve important details
Prioritize:
- Main purpose and conclusions.
- Important facts, metrics, dates, names, and requirements.
- Decisions, risks, dependencies, and action items.
- Repeated themes and high-impact findings.

Do not over-focus on boilerplate, repeated headers/footers, or low-value text.

### Handle long PDFs in chunks
For large PDFs:
1. Extract page text.
2. Split the document into logical chunks or page ranges.
3. Summarize each chunk.
4. Merge chunk summaries into one coherent final summary.
5. Remove duplicates while preserving important details.

## Recommended Summary Formats

### Quick Summary
Best for a fast overview.

```text
Summary
- Main point 1
- Main point 2
- Main point 3
```

### Executive Summary
Best for business or stakeholder documents.

```text
Executive Summary
<2-5 concise paragraphs>

Key Points
- ...

Risks / Issues
- ...

Action Items
- ...
```

### Detailed Summary
Best when the user needs more coverage.

```text
Overview
...

Section-wise Summary
1. Section name
   - ...

Important Data / Metrics
- ...

Decisions
- ...

Action Items
- ...
```

## Core Workflow

```python
from core.pdf_extractor import extract_pdf
from core.summarizer import summarize_text
from core.output_formatter import format_summary
from core.validators import validate_pdf

# 1. Validate the PDF
passes, info = validate_pdf("document.pdf", verbose=True)
if not passes:
    raise ValueError(info.get("error", "PDF validation failed"))

# 2. Extract text
pdf_data = extract_pdf("document.pdf")

# 3. Create a deterministic baseline summary
summary = summarize_text(
    pdf_data["text"],
    max_sentences=10,
    focus_terms=None,
)

# 4. Format the result
output = format_summary(
    title=pdf_data.get("title") or "PDF Summary",
    summary=summary,
    metadata=pdf_data,
)

print(output)
```

## Working with Scanned PDFs

This skill extracts embedded PDF text. If a PDF is image-only or scanned and contains little or no extractable text:
- Report that OCR is required.
- Do not pretend that blank extraction means the document is empty.
- If OCR tooling is available in the environment, OCR the relevant pages first and then summarize the OCR output.

## Available Utilities

### PDF Extractor (`core.pdf_extractor`)
Extracts text and basic metadata from a PDF:

```python
from core.pdf_extractor import extract_pdf

data = extract_pdf("document.pdf")
print(data["page_count"])
print(data["text"])
```

Optional page selection:

```python
data = extract_pdf("document.pdf", pages=[1, 2, 5])
```

Pages are 1-indexed for convenience.

### Summarizer (`core.summarizer`)
Provides a local extractive summarizer that does not require an API key:

```python
from core.summarizer import summarize_text

summary = summarize_text(
    text,
    max_sentences=8,
    focus_terms=["revenue", "risk", "timeline"],
)
```

The extractive summarizer is useful as a deterministic baseline. When an LLM is available, prefer semantic summarization while following the grounding rules in this skill.

### Output Formatter (`core.output_formatter`)
Formats summaries into readable Markdown:

```python
from core.output_formatter import format_summary

markdown = format_summary(
    title="Quarterly Report Summary",
    summary=summary,
    key_points=["Point A", "Point B"],
    action_items=["Action A"],
)
```

### Validators (`core.validators`)
Checks that a PDF exists, can be opened, has pages, and contains extractable text:

```python
from core.validators import validate_pdf, is_pdf_ready

passes, info = validate_pdf("document.pdf", verbose=True)

if is_pdf_ready("document.pdf"):
    print("Ready to summarize")
```

## Summary Quality Checklist

Before returning a summary, check that:
- The summary reflects the actual PDF content.
- Important numbers, dates, names, and decisions are preserved accurately.
- Repeated content is consolidated.
- The level of detail matches the user's request.
- No unsupported claims have been added.
- Action items are only included when the document actually contains or clearly implies them.
- Any unreadable, missing, or image-only content is explicitly noted.

## Philosophy

This skill provides:
- **Knowledge**: A reliable workflow for PDF summarization.
- **Utilities**: PDF extraction, validation, baseline summarization, and formatting.
- **Flexibility**: Supports short, detailed, executive, topic-focused, and page-focused summaries.

It does NOT provide:
- OCR by itself.
- Guaranteed extraction from encrypted or damaged PDFs.
- Automatic factual enrichment from the internet.
- Permission to infer missing content.

Use the PDF as the source of truth and keep summaries concise, accurate, and useful.

## Dependencies

```bash
pip install pypdf
```
