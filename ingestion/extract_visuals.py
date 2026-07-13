"""
ingestion/extract_visuals.py

Single pass over each PDF that decides, per page, whether to render a PNG
and whether that page has a figure caption — replacing the old two-script
split (extract_images.py + describe_images.py) that rendered images and
found captions independently, with no guarantee a caption's page number
matched a page that was actually rendered.

A caption is only ever emitted for a page that was actually rendered as a
PNG, and caption text on a page is itself treated as evidence the page is
visual (not just the image-block/text-density heuristic) — this closes the
gap where a figure's caption sits on a page the heuristic alone would have
skipped as "just text".

Output: one manifest per paper at data/pdfs/visuals/{paper_id}.json

Run:
    python -m ingestion.extract_visuals
"""

import os
import re
import json
import fitz

from sqlalchemy import text
from db.database import get_db
from ingestion.config import PDF_RAW_DIR, IMAGES_DIR, VISUALS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

DPI = 150  # 150 DPI = good quality, manageable file size

CAPTION_PATTERN = re.compile(
    r'(Fig(?:ure)?s?\.?\s*\d+[a-zA-Z]?[\.\:\s][^\n]{20,}(?:\n(?!Fig)[^\n]+)*)',
    re.IGNORECASE
)


def get_papers_metadata() -> dict:
    try:
        sql = text("SELECT paper_id, title FROM papers WHERE source='abstract'")
        with get_db() as conn:
            rows = conn.execute(sql).fetchall()
        return {row.paper_id: row.title for row in rows}
    except Exception as e:
        logger.error(f"Error fetching metadata: {e}")
        return {}


def find_captions(page_text: str) -> list[str]:
    captions = []
    for match in CAPTION_PATTERN.findall(page_text):
        caption = re.sub(r"\s+", " ", match.strip())[:600]
        if len(caption) < 40:
            continue
        if caption.lower().startswith("fig") and "doi" in caption.lower():
            continue
        captions.append(caption)
    return captions


def page_has_visual_content(page) -> bool:
    """
    Returns True if the page contains actual figures/images, or has very
    low text density relative to its area (likely a full-page figure).
    """
    blocks = page.get_text("dict")["blocks"]

    if any(b["type"] == 1 for b in blocks):
        return True

    text_content = page.get_text("text").strip()
    page_area = page.rect.width * page.rect.height
    text_density = len(text_content) / page_area if page_area > 0 else 0

    return text_density < 0.002 and len(text_content) > 10


def render_page(page, paper_dir: str, page_num: int) -> str | None:
    try:
        matrix = fitz.Matrix(DPI / 72, DPI / 72)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        if pix.width < 200 or pix.height < 200:
            return None

        image_path = os.path.join(paper_dir, f"page_{page_num:03d}.png")
        pix.save(image_path)
        return image_path

    except Exception as e:
        logger.error(f"[FAIL] Page {page_num} render failed: {e}")
        return None


def process_pdf(pdf_path: str, paper_id: str, title: str) -> list[dict]:
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"[FAIL] Cannot open PDF: {e}")
        return []

    paper_dir = os.path.join(IMAGES_DIR, paper_id)
    os.makedirs(paper_dir, exist_ok=True)

    visuals = []
    chunk_index = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        captions_on_page = find_captions(page.get_text("text"))
        is_visual = page_has_visual_content(page) or bool(captions_on_page)

        image_path = render_page(page, paper_dir, page_num + 1) if is_visual else None

        if not image_path:
            if captions_on_page:
                logger.warning(
                    f"{paper_id} page {page_num + 1}: caption found but page "
                    f"not renderable, skipping"
                )
            continue

        for caption in captions_on_page:
            visuals.append({
                "paper_id":      paper_id,
                "page":          page_num + 1,
                "caption":       caption,
                "chunk_index":   chunk_index,
                "title":         title,
                "embedding_text": f"{title}. {caption}",
                "image_path":    image_path,
            })
            chunk_index += 1

    doc.close()
    return visuals


def main():
    metadata = get_papers_metadata()
    pdf_files = [f for f in os.listdir(PDF_RAW_DIR) if f.endswith(".pdf")]

    logger.info(f"Found {len(pdf_files)} PDFs")

    total_visuals = 0
    total_skipped = 0

    for i, filename in enumerate(pdf_files, 1):
        paper_id = filename.replace(".pdf", "")
        title    = metadata.get(paper_id)

        if not title:
            total_skipped += 1
            continue

        output_path = os.path.join(VISUALS_DIR, f"{paper_id}.json")
        if os.path.exists(output_path):
            total_skipped += 1
            continue

        pdf_path = os.path.join(PDF_RAW_DIR, filename)
        logger.info(f"[{i}/{len(pdf_files)}] {title[:65]}...")

        visuals = process_pdf(pdf_path, paper_id, title)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(visuals, f, indent=2, ensure_ascii=False)

        total_visuals += len(visuals)
        logger.info(f"[OK] {len(visuals)} captions with images")

    logger.info("=" * 50)
    logger.info(f"Total captions extracted: {total_visuals}")
    logger.info(f"PDFs skipped: {total_skipped}")
    logger.info(f"Saved manifests to: {VISUALS_DIR}")


if __name__ == "__main__":
    main()
