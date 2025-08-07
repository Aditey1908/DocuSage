import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import fitz  # PyMuPDF

# Configure logging
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
OUT_ROOT = Path("data/processed")

MIN_CHARS = 40             # minimum characters for valid text extraction

def clean(t: str) -> str:
    """Clean extracted text by normalizing whitespace and removing artifacts."""
    t = t.replace("\x0c", " ")  # form feed
    t = re.sub(r"[ \t]+\n", "\n", t)  # trailing spaces before newline
    t = re.sub(r"\n{3,}", "\n\n", t)  # multiple newlines
    t = re.sub(r"[ \t]{2,}", " ", t)  # multiple spaces/tabs
    return t.strip()

def extract_text_from_pdf(pdf_filepath):
    """
    Simple function to extract text from PDF for Flask app usage
    Returns extracted text as string
    """
    try:
        if not os.path.exists(pdf_filepath):
            logger.error(f"PDF file not found: {pdf_filepath}")
            return "Error: PDF file not found."
        
        doc = fitz.open(pdf_filepath)
        text_parts = []
        
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(f"\n--- Page {page_num + 1} ---\n")
                    text_parts.append(clean(page_text))
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                continue
        
        doc.close()
        
        if text_parts:
            extracted_text = "\n".join(text_parts)
            logger.info(f"Successfully extracted text using PyMuPDF: {len(extracted_text)} characters")
            return extracted_text.strip()
        else:
            return "Error: No text could be extracted from the PDF."
            
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return f"Error: Failed to extract text from PDF - {str(e)}"

def save_extracted_text(text_content, text_filepath):
    """Save extracted text to a file"""
    try:
        with open(text_filepath, 'w', encoding='utf-8') as text_file:
            text_file.write(text_content)
        logger.info(f"Text saved to: {text_filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save text to {text_filepath}: {e}")
        return False

def process_pdf_simple(pdf_filepath, output_dir="downloads"):
    """
    Simple function to process a PDF file: extract text and save to .txt file
    Returns tuple: (extracted_text, text_filepath, success)
    """
    try:
        # Extract text from PDF
        logger.info(f"Extracting text from PDF: {pdf_filepath}")
        extracted_text = extract_text_from_pdf(pdf_filepath)
        
        # Generate text file path
        pdf_basename = os.path.basename(pdf_filepath)
        text_filename = os.path.splitext(pdf_basename)[0] + '.txt'
        text_filepath = os.path.join(output_dir, text_filename)
        
        # Save extracted text
        success = save_extracted_text(extracted_text, text_filepath)
        
        return extracted_text, text_filepath, success
        
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_filepath}: {e}")
        return f"Error processing PDF: {str(e)}", "", False

def ensure_dirs(stem: str):
    """Create output directories for a document."""
    out_dir = OUT_ROOT / stem
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

def detect_tables_pymupdf(page) -> List[Dict[str, Any]]:
    """Detect and extract tables using PyMuPDF's table detection."""
    tables = []
    try:
        # Find tables on the page
        tabs = page.find_tables()
        for i, tab in enumerate(tabs):
            # Extract table data
            table_data = tab.extract()
            if table_data and len(table_data) > 1:  # At least header + 1 row
                bbox = tab.bbox  # Table bounding box
                # Handle bbox properly - it might be a tuple or a Rect object
                if hasattr(bbox, 'x0'):
                    bbox_coords = [bbox.x0, bbox.y0, bbox.x1, bbox.y1]
                else:
                    bbox_coords = list(bbox) if bbox else [0, 0, 0, 0]
                
                tables.append({
                    "table_id": i + 1,
                    "bbox": bbox_coords,
                    "data": table_data,
                    "rows": len(table_data),
                    "cols": max(len(row) for row in table_data) if table_data else 0
                })
    except Exception as e:
        print(f"Table detection error: {e}")
    return tables

def table_to_text(table_data: List[List[str]], table_id: int) -> str:
    """Convert table data to formatted text."""
    if not table_data:
        return ""
    
    # Calculate column widths
    col_widths = []
    for col_idx in range(max(len(row) for row in table_data)):
        max_width = 0
        for row in table_data:
            if col_idx < len(row) and row[col_idx]:
                max_width = max(max_width, len(str(row[col_idx])))
        col_widths.append(max(max_width, 10))  # minimum width of 10
    
    # Format table
    result = f"\n[TABLE {table_id}]\n"
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+\n"
    
    result += separator
    for row_idx, row in enumerate(table_data):
        result += "|"
        for col_idx, cell in enumerate(row):
            if col_idx < len(col_widths):
                cell_str = str(cell) if cell else ""
                result += f" {cell_str:<{col_widths[col_idx]}} |"
        result += "\n"
        
        # Add separator after header row
        if row_idx == 0:
            result += separator
    
    result += separator
    result += f"[END TABLE {table_id}]\n\n"
    return result

def extract_text_blocks(page) -> Tuple[str, List[Dict[str, Any]]]:
    """Extract text and metadata about text blocks."""
    blocks_meta = []
    full_text = ""
    
    # Get text with block information
    blocks = page.get_text("dict")
    
    for block in blocks.get("blocks", []):
        if "lines" in block:  # Text block
            block_text = ""
            for line in block["lines"]:
                line_text = ""
                for span in line["spans"]:
                    line_text += span["text"]
                block_text += line_text + "\n"
            
            if block_text.strip():
                bbox = block["bbox"]
                blocks_meta.append({
                    "type": "text",
                    "bbox": bbox,
                    "chars": len(block_text.strip()),
                    "text": block_text.strip()
                })
                full_text += block_text
    
    return clean(full_text), blocks_meta

def extract_images_info(page, page_num: int) -> List[str]:
    """Extract information about images on the page."""
    image_info = []
    try:
        image_list = page.get_images()
        for i, img in enumerate(image_list):
            xref = img[0]
            pix = fitz.Pixmap(page.parent, xref)
            
            if pix.n - pix.alpha < 4:  # GRAY or RGB
                image_info.append(f"[IMAGE {i+1}: {pix.width}x{pix.height} pixels]")
            pix = None
    except Exception as e:
        print(f"Image extraction error: {e}")
    
    return image_info

def process_pdf(pdf_path: Path):
    """Process a single PDF file and extract all content to a single text file."""
    stem = pdf_path.stem
    out_dir = ensure_dirs(stem)
    output_file = out_dir / f"{stem}.txt"
    doc = fitz.open(pdf_path)

    with output_file.open("w", encoding="utf-8") as fout:
        # Write document header
        fout.write(f"DOCUMENT: {pdf_path.name}\n")
        fout.write("=" * 80 + "\n")
        fout.write(f"Total Pages: {len(doc)}\n")
        fout.write(f"Extracted on: {pdf_path.stat().st_mtime}\n")
        fout.write("=" * 80 + "\n\n")
        
        total_tables = 0
        total_images = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Write page header
            fout.write(f"\n{'='*20} PAGE {page_num + 1} {'='*20}\n\n")
            
            # Extract text
            full_text, text_blocks = extract_text_blocks(page)
            
            # Extract tables
            tables = detect_tables_pymupdf(page)
            
            # Extract image info
            image_info = extract_images_info(page, page_num + 1)
            
            # Write page content
            if full_text.strip():
                fout.write("TEXT CONTENT:\n")
                fout.write("-" * 40 + "\n")
                fout.write(full_text)
                fout.write("\n\n")
            
            # Write tables
            if tables:
                fout.write("TABLES ON THIS PAGE:\n")
                fout.write("-" * 40 + "\n")
                for table in tables:
                    table_text = table_to_text(table["data"], table["table_id"])
                    fout.write(table_text)
                    total_tables += 1
            
            # Write image info
            if image_info:
                fout.write("IMAGES ON THIS PAGE:\n")
                fout.write("-" * 40 + "\n")
                for img_info in image_info:
                    fout.write(img_info + "\n")
                    total_images += 1
                fout.write("\n")
            
            # Page summary
            fout.write(f"Page {page_num + 1} Summary:\n")
            fout.write(f"- Text blocks: {len(text_blocks)}\n")
            fout.write(f"- Tables: {len(tables)}\n")
            fout.write(f"- Images: {len(image_info)}\n")
            fout.write(f"- Page size: {page.rect.width:.1f} x {page.rect.height:.1f}\n")
            fout.write("\n" + "="*60 + "\n")
        
        # Write document summary at the end
        fout.write(f"\n\nDOCUMENT SUMMARY:\n")
        fout.write("=" * 80 + "\n")
        fout.write(f"Total Pages: {len(doc)}\n")
        fout.write(f"Total Tables Extracted: {total_tables}\n")
        fout.write(f"Total Images Found: {total_images}\n")
        fout.write(f"Extraction Method: PyMuPDF\n")
        fout.write("=" * 80 + "\n")
    
    # Print summary before closing
    print(f"✅ {pdf_path.name} → {output_file}")
    print(f"   📄 {len(doc)} pages, 📊 {total_tables} tables, 🖼️ {total_images} images")
    
    doc.close()

def main():
    """Main function to process all PDFs in the raw directory."""
    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    if not pdfs:
        print("Put PDFs in data/raw/ and re-run.")
        return
    
    print(f"Found {len(pdfs)} PDF(s) to process:")
    for pdf in pdfs:
        print(f"  - {pdf.name}")
    
    for pdf_path in pdfs:
        try:
            process_pdf(pdf_path)
        except Exception as e:
            print(f"❌ {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
