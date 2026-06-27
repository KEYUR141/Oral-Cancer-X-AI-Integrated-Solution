import os
import json
import fitz
import re
from sqlalchemy import text
from db.database import get_db


PDF_DIR = "data/pdfs/raw"
OUTPUT_DIR = "data/pdfs/extracted_text"
MIN_CHARS = 100

CHUNK_SIZE = 1000
OVERLAP = 100

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_papers_metadata() -> dict:
    try:
        sql_data = text("SELECT paper_id, title FROM papers;")
        with get_db() as conn:
            rows = conn.execute(sql_data).fetchall()
        return {row.paper_id: row.title for row in rows}
    except Exception as e:
        print(f"Error fetching paper data: {e}")
        return {}

def clean_text(text:str) -> str:
    try:
        # Remove hyphenated line breaks (common in justified PDF text)
        text = re.sub(r"-\n([a-z])", r"\1", text)

        # Collapse multiple newlines into one
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Replace single newlines mid-paragraph with space
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

        # Collapse multiple spaces
        text = re.sub(r" {2,}", " ", text)

        # Remove lines that are just page numbers or very short (headers/footers)
        lines = text.split("\n")
        lines = [l for l in lines if len(l.strip()) > 20 or l.strip() == ""]
        text = "\n".join(lines)

        return text.strip()

    except Exception as e:
        print(f"Error fetching paper data: {e}")


def is_garbage_chunk(text: str) -> bool:
    """
    Returns True if this chunk is noise rather than research content.
    Catches: journal headers, URLs, author affiliations, license text,
    reference lists, and other non-content sections.
    """
    text_lower = text.lower()

    # Too many URLs — likely a references or header section
    url_count = text_lower.count("http")
    if url_count > 3:
        return True

    # License/copyright text
    if any(phrase in text_lower for phrase in [
        "creative commons",
        "all rights reserved",
        "this article is licensed",
        "open access article",
        "doi:",
    ]):
        return True

    # Author affiliation blocks (lots of commas, city names, postal codes)
    if text_lower.count(",") > 15 and len(text) < 500:
        return True

    # Pure reference lists (lots of numbers at start of lines)
    lines = text.split("\n")
    numbered_lines = sum(1 for l in lines if l.strip()[:2].rstrip(".").isdigit())
    if numbered_lines > len(lines) * 0.5:
        return True

    return False

def chunk_text(text:str, chunk_size: int  =CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    try:
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            if end >= len(text):
                chunks.append(text[start:].strip())
                break

            boundary = text.rfind(". ", start, end)
            if boundary != -1 and boundary > start + chunk_size // 2:
                end = boundary+1
            
            chunk = text[start:end].strip()
            if len(chunk) >= MIN_CHARS:
                chunks.append(chunk)

            start = end - overlap
        
        return chunks
    
    except Exception as e:
        print(f"Error fetching paper data: {e}")


def extract_pdf(pdf_path: str, paper_id: str, title: str) -> dict | None:
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  [FAIL] Cannot open PDF: {e}")
        return None
    
    full_text = ""

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text("text")

        if len(page_text.strip()) < MIN_CHARS:
            continue

        full_text += f"\n\n{page_text}"
    
    doc.close()

    if len(full_text.strip()) < MIN_CHARS:
        print(f"  [SKIP] No usable text extracted")
        return None
    
    cleaned = clean_text(full_text)
    chunks_raw = chunk_text(cleaned)

    chunks = [c for c in chunks_raw if not is_garbage_chunk(c)]

    if not chunks:
        print(f"  [SKIP] No chunks produced after cleaning")
        return None

    return {
        "paper_id": paper_id,
        "title":    title,
        "chunks": [
            {
                "chunk_index": i,
                "text":        chunk,
            }
            for i, chunk in enumerate(chunks)
        ]
    }

def main():
    metadata = get_papers_metadata()
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

    print(f"Found {len(pdf_files)} PDFs to process\n")

    success = 0
    failed  = 0
    skipped = 0

    for i, filename in enumerate(pdf_files, 1):
        paper_id    = filename.replace(".pdf", "")
        output_path = os.path.join(OUTPUT_DIR, f"{paper_id}.json")
        pdf_path    = os.path.join(PDF_DIR, filename)
        title       = metadata.get(paper_id, "Unknown title")

        print(f"[{i}/{len(pdf_files)}] {title[:65]}...")

        # Skip already processed
        if os.path.exists(output_path):
            skipped += 1
            print(f"  [SKIP] Already extracted")
            continue
        # Skip PDFs whose paper_id isn't in our database
        if paper_id not in metadata:
            print(f"  [SKIP] Not in database — {paper_id}")
            skipped += 1
            continue

        result = extract_pdf(pdf_path, paper_id, title)

        if result:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"  [OK]   {len(result['chunks'])} chunks extracted")
            success += 1
        else:
            failed += 1

    print(f"\n{'='*50}")
    print(f"Extracted:  {success} papers")
    print(f"Failed:     {failed}")
    print(f"Skipped:    {skipped} (already done)")
    print(f"Output in:  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()