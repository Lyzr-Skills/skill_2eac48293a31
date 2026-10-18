"""
main.py
-------
Entry point for the PDF Summariser skill.

Usage:
    python main.py --pdf document.pdf
    python main.py --pdf doc1.pdf doc2.pdf --depth detailed --format bullet --keywords --sections
    python main.py --pdf report.pdf --format json --output result.json
"""

import argparse
import sys

from extractor import extract_multiple_pdfs
from summariser import PDFSummariser
from utils import format_output, save_output


# ---------------------------------------------------------------------------
# Argument Parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf_summariser",
        description="📄 PDF Summariser — Extract and summarise PDF documents using AI.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--pdf",
        nargs="+",
        required=True,
        metavar="FILE",
        help="Path(s) to one or more PDF files to summarise.",
    )
    parser.add_argument(
        "--depth",
        choices=["short", "medium", "detailed"],
        default="medium",
        help=(
            "Summary depth level:\n"
            "  short    — 2-4 sentence overview\n"
            "  medium   — 1-2 paragraph summary (default)\n"
            "  detailed — Full detailed summary with all key points"
        ),
    )
    parser.add_argument(
        "--format",
        choices=["text", "bullet", "json"],
        default="text",
        dest="fmt",
        help=(
            "Output format:\n"
            "  text   — Plain text (default)\n"
            "  bullet — Bullet-point list\n"
            "  json   — Structured JSON"
        ),
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Optional: Save output to this file path (e.g., summary.txt or summary.json).",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o).",
    )
    parser.add_argument(
        "--keywords",
        action="store_true",
        help="Extract and include key topics/keywords in the output.",
    )
    parser.add_argument(
        "--sections",
        action="store_true",
        help="Summarise each detected document section individually.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    print("\n🚀 PDF Summariser Starting...")
    print(f"   Files   : {', '.join(args.pdf)}")
    print(f"   Depth   : {args.depth}")
    print(f"   Format  : {args.fmt}")
    print(f"   Model   : {args.model}")
    print(f"   Keywords: {args.keywords}")
    print(f"   Sections: {args.sections}")
    if args.output:
        print(f"   Output  : {args.output}")

    # --- Step 1: Extract ---
    print("\n📥 Extracting PDF text...")
    extracted_docs = extract_multiple_pdfs(args.pdf)

    failed = [d for d in extracted_docs if d.get("error")]
    if failed:
        print(f"\n⚠️  {len(failed)} file(s) failed to extract:")
        for f in failed:
            print(f"   ✗ {f['file']}: {f['error']}")

    valid_docs = [d for d in extracted_docs if not d.get("error")]
    if not valid_docs:
        print("\n❌ No valid PDFs to summarise. Exiting.")
        sys.exit(1)

    # --- Step 2: Summarise ---
    summariser = PDFSummariser(
        model=args.model,
        depth=args.depth,
        extract_keywords=args.keywords,
        summarise_sections=args.sections,
    )
    summaries = summariser.summarise_all(valid_docs)

    # --- Step 3: Format & Display ---
    all_output_parts = []
    for summary_data in summaries:
        formatted = format_output(summary_data, fmt=args.fmt)
        all_output_parts.append(formatted)
        print(formatted)

    # --- Step 4: Save (optional) ---
    if args.output:
        combined_output = "\n\n".join(all_output_parts)
        save_output(combined_output, args.output)

    print("\n✅ Done!\n")


if __name__ == "__main__":
    main()
