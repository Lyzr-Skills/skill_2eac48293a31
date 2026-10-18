# PDF Summariser Skill

## Overview
This skill extracts text from one or more PDF files and generates structured, intelligent summaries using an LLM (OpenAI GPT). It supports single-page, multi-page, and multi-document summarisation with configurable summary depth and output formats.

---

## Features
- **EXTRACT** text from PDF files using `pdfplumber`
- **SUMMARISE** content using OpenAI GPT models
- **CONFIGURABLE** summary depth: `short`, `medium`, `detailed`
- **MULTI-DOCUMENT** support — summarise multiple PDFs at once
- **STRUCTURED OUTPUT** — plain text, bullet points, or JSON
- **SECTION-AWARE** — attempts to identify and summarise sections/chapters individually
- **KEYWORD EXTRACTION** — pulls key topics/themes from the document
- **EXPORT** summaries to `.txt` or `.json` files

---

## File Structure
```
pdf_summariser/
├── SKILL.md               # This file
├── main.py                # Entry point
├── extractor.py           # PDF text extraction logic
├── summariser.py          # LLM summarisation logic
├── utils.py               # Helpers (chunking, formatting, export)
└── requirements.txt       # Dependencies
```

---

## Requirements
Install dependencies:
```bash
pip install -r requirements.txt
```

### `requirements.txt`
```
openai>=1.0.0
pdfplumber>=0.9.0
tiktoken>=0.5.0
python-dotenv>=1.0.0
```

---

## Environment Variables
Create a `.env` file in the root of the skill directory:
```
OPENAI_API_KEY=your_openai_api_key_here
```

---

## Usage

### Basic Usage
```bash
python main.py --pdf path/to/document.pdf
```

### Full Options
```bash
python main.py \
  --pdf path/to/document.pdf \
  --depth medium \
  --format bullet \
  --output summary_output.txt
```

### Multiple PDFs
```bash
python main.py \
  --pdf file1.pdf file2.pdf file3.pdf \
  --depth detailed \
  --format json \
  --output summaries.json
```

---

## Arguments

| Argument    | Type     | Default   | Description                                                  |
|-------------|----------|-----------|--------------------------------------------------------------|
| `--pdf`     | str (list) | required | Path(s) to PDF file(s) to summarise                         |
| `--depth`   | str      | `medium`  | Summary depth: `short`, `medium`, `detailed`                 |
| `--format`  | str      | `text`    | Output format: `text`, `bullet`, `json`                      |
| `--output`  | str      | None      | File path to save the output (optional)                      |
| `--model`   | str      | `gpt-4o`  | OpenAI model to use                                          |
| `--keywords`| flag     | False     | Extract and include keywords/themes                          |
| `--sections`| flag     | False     | Summarise document by detected sections                      |

---

## Output Examples

### `--format text`
```
SUMMARY OF: annual_report.pdf
=================================
This document covers the company's financial performance for FY2024...
Key Themes: Revenue Growth, Sustainability, Market Expansion
```

### `--format bullet`
```
SUMMARY OF: annual_report.pdf
• Revenue increased by 18% year-over-year
• New markets opened in Southeast Asia
• Sustainability initiatives reduced carbon footprint by 25%
```

### `--format json`
```json
{
  "file": "annual_report.pdf",
  "summary": "This document covers...",
  "keywords": ["revenue", "growth", "sustainability"],
  "sections": [
    { "title": "Financial Highlights", "summary": "..." },
    { "title": "Strategic Goals", "summary": "..." }
  ]
}
```

---

## How It Works
1. **Extract** — `extractor.py` uses `pdfplumber` to pull raw text from each page
2. **Chunk** — `utils.py` splits long documents into token-safe chunks (respects model context window)
3. **Summarise** — `summariser.py` sends each chunk to the OpenAI API with a tailored prompt
4. **Merge** — Multiple chunk summaries are merged into one coherent final summary
5. **Format & Export** — Output is formatted and optionally saved to a file

---

## Notes
- Very large PDFs are automatically chunked to fit within the model's context window
- Scanned/image-only PDFs are not supported (text layer required)
- For best results, use PDFs with selectable text
