"""
ingestion/extract_captions.py

Extracts figure captions from downloaded PDFs using regex pattern matching.
Figure captions are precise medical descriptions written by the researchers
themselves — better quality than vision model descriptions for this use case.

Output: data/pdfs/figure_captions.json

Run:
    python -m ingestion.extract_captions
"""

import os
import re
import json
import fitz
from sqlalchemy import text
from db.database import get_db

# ── Config ────────────────────────────────────────────────────────────────────
PDF_DIR     = "data/pdfs/raw"
OUTPUT_FILE = "data/pdfs/figure_captions.json"

# ── Fetch paper metadata ──────────────────────────────────────────────────────
def get_paper_metadata() -> dict:
    sql = text("SELECT paper_id, title FROM papers WHERE source='abstract'")
    with get_db() as conn:
        rows = conn.execute(sql).fetchall()
    return {row.paper_id: row.title for row in rows}


# ── Caption extractor ─────────────────────────────────────────────────────────
def extract_captions(pdf_path: str, paper_id: str) -> list[dict]:
    """
    Extracts figure captions from a single PDF.

    Looks for patterns like:
      - "Figure 1. Kaplan-Meier survival curve..."
      - "Fig. 2A. Histopathology image showing..."
      - "FIGURE 3: Clinical photograph of..."

    Returns list of caption dicts with page number and caption text.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  [FAIL] Cannot open: {e}")
        return []

    captions = []

    # Pattern matches "Figure X", "Fig X", "Fig. X", "FIGURE X"
    # followed by optional letter (2A, 3B) and period/colon
    # then captures the caption text until double newline or end
    caption_pattern = re.compile(
        r'(Fig(?:ure)?s?\.?\s*\d+[a-zA-Z]?[\.\:\s][^\n]{20,}(?:\n(?!Fig)[^\n]+)*)',
        re.IGNORECASE
    )

    for page_num in range(len(doc)):
        page_text = doc[page_num].get_text("text")

        matches = caption_pattern.findall(page_text)

        for match in matches:
            # Clean up the caption
            caption = match.strip()
            caption = re.sub(r'\s+', ' ', caption)  # collapse whitespace
            caption = caption[:600]                   # limit length

            # Filter out very short matches (likely false positives)
            if len(caption) < 40:
                continue

            # Filter out matches that look like reference list entries
            if caption.lower().startswith("fig") and "doi" in caption.lower():
                continue

            captions.append({
                "paper_id":    paper_id,
                "page":        page_num + 1,
                "caption":     caption,
                "chunk_index": len(captions),
            })

    doc.close()
    return captions


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    metadata  = get_paper_metadata()
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

    print(f"Found {len(pdf_files)} PDFs\n")

    all_captions = []
    processed    = 0
    skipped      = 0

    for i, filename in enumerate(pdf_files, 1):
        paper_id = filename.replace(".pdf", "")
        title    = metadata.get(paper_id)

        if not title:
            skipped += 1
            continue

        pdf_path = os.path.join(PDF_DIR, filename)
        print(f"[{i}/{len(pdf_files)}] {title[:65]}...")

        captions = extract_captions(pdf_path, paper_id)

        # Attach title to each caption for embedding context
        for cap in captions:
            cap["title"] = title
            cap["embedding_text"] = f"{title}. {cap['caption']}"

        all_captions.extend(captions)
        processed += 1
        print(f"  [OK] {len(captions)} captions found")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_captions, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"Processed:       {processed} papers")
    print(f"Skipped:         {skipped} (not in DB)")
    print(f"Total captions:  {len(all_captions)}")
    print(f"Saved to:        {OUTPUT_FILE}")


if __name__ == "__main__":
    main()