import argparse
import math
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from typing import List, Tuple

import fitz  # PyMuPDF


LIG_MAP = {
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\xa0": " "
}
_LIG_RE = re.compile("|".join(map(re.escape, LIG_MAP.keys())))

def normalize(s: str) -> str:
    if not s:
        return ""
    s = _LIG_RE.sub(lambda m: LIG_MAP[m.group(0)], s)
    return s.replace("\t", " ").strip()

def dehyphenate(text: str) -> str:
    # join hyphenated line-breaks like "bene-\nfit" -> "benefit"
    text = re.sub(r"(\w)-\n([a-z])", r"\1\2", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text

# ---------- types ----------

Line = Tuple[float, float, float, str, float]  # (x0, y_mid, x1, text, avg_font_size)

# ---------- core extraction ----------

def extract_page_lines(page: fitz.Page) -> Tuple[List[Line], float]:
    # Some PDFs have empty span.text in "rawdict"; fall back to "dict"
    rd = page.get_text("rawdict")
    if not any(s.get("text","").strip()
               for b in rd.get("blocks", [])
               for l in b.get("lines", [])
               for s in l.get("spans", [])):
        rd = page.get_text("dict")

    lines: List[Line] = []
    for b in rd.get("blocks", []):
        for l in b.get("lines", []):
            spans = l.get("spans", [])
            if not spans:
                continue
            txt = normalize("".join(s.get("text","") for s in spans))
            if not txt:
                continue
            y_mid = sum(s["bbox"][1] for s in spans) / len(spans)
            x0 = min(s["bbox"][0] for s in spans)
            x1 = max(s["bbox"][2] for s in spans)
            fs = sum(s.get("size", 0.0) for s in spans) / len(spans)
            lines.append((x0, y_mid, x1, txt, fs))
    return lines, float(page.rect.height)

def normalize_for_boiler(s: str) -> str:
    # Lowercase, strip numbers/dates, collapse spaces
    s = s.lower()
    s = re.sub(r'\d+', '', s)          # remove all digits
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def build_boilerplate_mask(
    pages_lines: List[List[Line]],
    threshold: float = 0.7,
    band_px: int = 20,
) -> set:
    """
    Identify recurring header/footer lines, tolerant to small text changes.
    """
    num_pages = len(pages_lines)
    counts = Counter()

    for lines in pages_lines:
        seen = set()
        for _, y, _, txt, _ in lines:
            yb = int(round(y / band_px))
            norm_txt = normalize_for_boiler(txt)
            key = (yb, norm_txt)
            if norm_txt and key not in seen:
                counts[key] += 1
                seen.add(key)

    min_pages = max(2, int(math.ceil(num_pages * threshold)))
    boiler = {k for k, c in counts.items() if c >= min_pages}
    return boiler

def order_by_columns(lines: List[Line]) -> List[Line]:
    """
    Robust 1–3 column ordering via simple x-histogram peak picking.
    """
    if len(lines) < 10:
        return sorted(lines, key=lambda t: (t[1], t[0]))

    # Build coarse histogram of x midpoints
    mids = [ (ln[0] + ln[2]) / 2.0 for ln in lines ]
    buckets = Counter(int(round(x/40.0)) for x in mids)  # 40px buckets
    peaks = [k for k,_ in buckets.most_common(3)]
    peaks.sort()

    def assign_peak(xmid: float) -> int:
        if not peaks:
            return 0
        key = int(round(xmid/40.0))
        # nearest peak index
        return min(range(len(peaks)), key=lambda i: abs(key - peaks[i]))

    cols = {i: [] for i in range(len(peaks) or 1)}
    for x0, y, x1, txt, fs in lines:
        idx = assign_peak((x0 + x1) / 2.0)
        cols[idx].append((x0, y, x1, txt, fs))

    ordered: List[Line] = []
    for i in sorted(cols.keys()):
        ordered.extend(sorted(cols[i], key=lambda t: (t[1], t[0])))
    return ordered

def lines_to_paragraphs(ordered: List[Line], y_gap: float = 16.0) -> List[str]:
    paras: List[str] = []
    buf: List[str] = []
    last_y = None
    for _, y, _, txt, _ in ordered:
        if last_y is not None and abs(y - last_y) > y_gap and buf:
            p = " ".join(buf).strip()
            if p:
                paras.append(p)
            buf = []
        buf.append(txt)
        last_y = y
    if buf:
        p = " ".join(buf).strip()
        if p:
            paras.append(p)
    return paras

# ---------- optional layout assist (pdftotext -layout) ----------

def has_pdftotext() -> bool:
    return shutil.which("pdftotext") is not None

def pdftotext_layout_page(pdf_path: str, page_index: int) -> str:
    """
    Use Poppler's pdftotext -layout for a single page (1-based args).
    Returns empty string if anything fails.
    """
    if not has_pdftotext():
        return ""
    tmp_out = os.path.splitext(pdf_path)[0] + f".p{page_index+1}.layout.txt"
    try:
        subprocess.run(
            ["pdftotext", "-layout", "-f", str(page_index+1), "-l", str(page_index+1), pdf_path, tmp_out],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        with open(tmp_out, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception:
        return ""
    finally:
        try: os.remove(tmp_out)
        except Exception: pass

def looks_tabular_or_dense(lines: List[Line]) -> bool:
    # Many distinct x positions -> likely columns/tables
    mids = [ round((x0+x1)/2.0, 1) for x0,_,x1,_,_ in lines ]
    return len(set(mids)) > 25  # tuneable: 25 is conservative but effective

def contains_tableish_keywords(paras: List[str]) -> bool:
    if not paras:
        return False
    head = " ".join(paras[:4])  # peek at first few paragraphs
    keys = ("Table of Benefits", "Sum Insured", "Domestic Cover", "International Cover", "Plan")
    return any(k in head for k in keys)

# ---------- document pipeline ----------

def extract_document(
    pdf_path: str,
    header_threshold: float = 0.85,
    band_px: int = 20,
    use_layout_where_helpful: bool = True,
) -> str:
    doc = fitz.open(pdf_path)
    num_pages = len(doc)

    pages_lines: List[List[Line]] = []
    for i in range(num_pages):
        ls, _ = extract_page_lines(doc.load_page(i))
        pages_lines.append(ls)

    boiler = build_boilerplate_mask(pages_lines, threshold=header_threshold, band_px=band_px)

    parts: List[str] = []
    layout_available = has_pdftotext() if use_layout_where_helpful else False

    for i in range(num_pages):
        page = doc.load_page(i)

        # remove boilerplate
        keep = []
        for (x0, y, x1, txt, fs) in pages_lines[i]:
            yb = int(round(y / band_px))
            if (yb, txt) in boiler:
                continue
            keep.append((x0, y, x1, txt, fs))
        if not keep:
            continue

        # column-aware ordering
        ordered = order_by_columns(keep)
        paras = lines_to_paragraphs(ordered)
        paras = [normalize(p) for p in paras if p]

        # targeted layout assist for messy pages
        use_layout = layout_available and (looks_tabular_or_dense(keep) or contains_tableish_keywords(paras))
        if use_layout:
            laid = pdftotext_layout_page(pdf_path, i)
            if laid:
                parts.append(laid)
                continue  # done with this page

        # normal path
        page_text = "\n\n".join(paras).strip()
        if page_text:
            parts.append(page_text)

    doc.close()

    text = "\n\n".join(parts)
    text = dehyphenate(text)
    text = normalize(text)
    return text.strip()

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description="Fast PDF extractor for born-digital PDFs (no OCR).")
    ap.add_argument("pdf", help="Input PDF path")
    ap.add_argument("-o", "--out", help="Output .txt path (default: stdout)")
    ap.add_argument("--header-threshold", type=float, default=0.85,
                    help="Fraction of pages a header/footer must appear on to be removed (default: 0.85)")
    ap.add_argument("--band-px", type=int, default=20,
                    help="Y-band size in pixels for header/footer recurrence (default: 20)")
    ap.add_argument("--no-layout", action="store_true",
                    help="Disable pdftotext -layout even on table/column-dense pages")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        print(f"File not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)

    txt = extract_document(
        args.pdf,
        header_threshold=args.header_threshold,
        band_px=args.band_px,
        use_layout_where_helpful=not args.no_layout,
    )

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(txt + "\n")
    else:
        sys.stdout.write(txt + "\n")

if __name__ == "__main__":
    main()
