#!/usr/bin/env python3
# pdf_to_txt_fast.py
# Usage: python pdf_to_txt_fast.py input.pdf [output.txt]

import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_txt_fast.py input.pdf [output.txt]")
        sys.exit(1)

    in_path = Path(sys.argv[1])
    if not in_path.is_file():
        print(f"Input not found: {in_path}")
        sys.exit(1)

    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else in_path.with_suffix(".txt")

    # Import here so the script starts instantly if help/error is shown
    import pymupdf4llm  # pip install pymupdf pymupdf4llm

    # Convert entire PDF to a single Markdown-formatted string (fast, no OCR/LLM)
    md_text = pymupdf4llm.to_markdown(str(in_path))

    # Save as .txt (Markdown is still plain text; keeps headings & tables readable)
    out_path.write_bytes(md_text.encode("utf-8"))

    print(f"Wrote: {out_path}")

if __name__ == "__main__":
    main()
