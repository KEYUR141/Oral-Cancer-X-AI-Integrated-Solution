"""
ingestion/extract_images.py

Renders PDF pages that contain visual content as PNG images.
Uses page rendering instead of embedded image extraction,
since most academic PDF figures are vector-rendered not embedded.

Run:
    python -m ingestion.extract_images
"""

import os
import fitz
from sqlalchemy import text
from db.database import get_db

PDF_DIR    = "data/pdfs/raw"
OUTPUT_DIR = "data/pdfs/images"
DPI        = 150    # resolution for page rendering
                    # 150 DPI = good quality, manageable file size
                    # 72 DPI = too blurry for Gemini Vision
                    # 300 DPI = too large, slow to process

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_papers_metadata() -> dict:
    try:
        sql = text("SELECT paper_id, title FROM papers WHERE source='abstract'")
        with get_db() as conn:
            rows = conn.execute(sql).fetchall()
        return {row.paper_id: row.title for row in rows}
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return {}


def page_has_visual_content(page) -> bool:
    """
    Returns True if page contains actual figures or images,
    not just text. Checks for image blocks in the page structure.
    Also checks if the page has significant non-text content
    by comparing text coverage to total page area.
    """
    blocks = page.get_text("dict")["blocks"]

    # Check for embedded image blocks
    has_image_blocks = any(b["type"] == 1 for b in blocks)
    if has_image_blocks:
        return True

    # Check for pages with very little text — likely figure pages
    text = page.get_text("text").strip()
    page_area = page.rect.width * page.rect.height
    text_density = len(text) / page_area if page_area > 0 else 0

    # Pages with very low text density but non-zero content
    # are likely figure-heavy pages worth capturing
    if text_density < 0.002 and len(text) > 10:
        return True

    return False


def render_page(page, paper_dir: str, page_num: int) -> dict | None:
    """
    Renders a single PDF page as a PNG image.
    Returns metadata dict or None if rendering fails.
    """
    try:
        matrix = fitz.Matrix(DPI / 72, DPI / 72)
        pix    = page.get_pixmap(matrix=matrix, alpha=False)

        # Skip nearly blank pages
        if pix.width < 200 or pix.height < 200:
            return None

        filename   = f"page_{page_num:03d}.png"
        image_path = os.path.join(paper_dir, filename)
        pix.save(image_path)

        return {
            "page":      page_num,
            "path":      image_path,
            "filename":  filename,
            "width":     pix.width,
            "height":    pix.height,
            "size_bytes": os.path.getsize(image_path),
        }

    except Exception as e:
        print(f"  [FAIL] Page {page_num} render failed: {e}")
        return None


def extract_images(pdf_path: str, paper_id: str) -> list[dict]:
    """
    Renders all pages with visual content from a PDF.
    Returns list of rendered page metadata.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  [FAIL] Cannot open PDF: {e}")
        return []

    paper_dir = os.path.join(OUTPUT_DIR, paper_id)
    os.makedirs(paper_dir, exist_ok=True)

    extracted = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        if not page_has_visual_content(page):
            continue

        result = render_page(page, paper_dir, page_num + 1)
        if result:
            result["paper_id"] = paper_id
            extracted.append(result)

    doc.close()
    return extracted


def main():
    metadata  = get_papers_metadata()
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

    print(f"Found {len(pdf_files)} PDFs\n")

    total_pages  = 0
    total_skipped = 0

    for i, filename in enumerate(pdf_files, 1):
        paper_id = filename.replace(".pdf", "")
        title    = metadata.get(paper_id, None)

        if not title:
            total_skipped += 1
            continue

        pdf_path = os.path.join(PDF_DIR, filename)
        print(f"[{i}/{len(pdf_files)}] {title[:65]}...")

        pages = extract_images(pdf_path, paper_id)
        total_pages += len(pages)
        print(f"  [OK] {len(pages)} pages with visual content")

    print(f"\n{'='*50}")
    print(f"Total pages rendered: {total_pages}")
    print(f"PDFs skipped: {total_skipped}")
    print(f"Saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()