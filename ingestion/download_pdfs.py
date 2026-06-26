import os
import time
from wsgiref.headers import Headers
import requests
from sqlalchemy import text
from db.database import get_db


OUTPUT_DIR = "data/pdfs/raw"
DELAY_SECS = 1.5
TIMEOUT_SECS = 30
HEADERS ={
    "User-Agent": "Mozilla/5.0 (research project; oral cancer RAG system)"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_papers_with_pdfs() -> list[dict]:
    try:
        sql = text("""
            SELECT paper_id, title, open_access_pdf_url
            FROM papers
            WHERE open_access_pdf_url IS NOT NULL
            ORDER BY citation_count DESC
        """)

        with get_db() as conn:
            rows = conn.execute(sql).fetchall()

        return [
            {
                "paper_id": row.paper_id,
                "title": row.title,
                "url": row.open_access_pdf_url
            }
            for row in rows
        ]
    except Exception as e:
        print(f"Error fetching papers with PDFs: {e}")
        raise

def download_pdf(paper:dict) -> bool:
    try:
        output_path = os.path.join(OUTPUT_DIR, f"{paper['paper_id']}.pdf")

        if os.path.exists(output_path):
            return True
        
        response = requests.get(
            paper['url'],
            headers = HEADERS,
            timeout = TIMEOUT_SECS,
            stream = True
        )

        if response.status_code != 200:
            print(f"Skipped downloading {paper['paper_id']}: HTTP {response.status_code}")
            return False
        

        # Verify it's actually a PDF
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower() and not paper["url"].endswith(".pdf"):
            print(f"  [SKIP] Not a PDF (Content-Type: {content_type}) — {paper['title'][:60]}")
            return False

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        size_kb = os.path.getsize(output_path) / 1024
        print(f"  [OK]   {size_kb:.0f}KB — {paper['title'][:60]}")
        return True

    except requests.exceptions.Timeout:
        print(f"  [FAIL] Timeout — {paper['title'][:60]}")
        return False
    except Exception as e:
        print(f"  [FAIL] {e} — {paper['title'][:60]}")
        return False
    
def main():
    try:
        papers = get_papers_with_pdfs()
        print(f"Found {len(papers)} papers with PDF URLs. Starting download...")
        
        success = 0
        failure = 0
        skipped = 0

        for i, paper in enumerate(papers, 1):
            output_path = os.path.join(OUTPUT_DIR, f"{paper['paper_id']}.pdf")

            if os.path.exists(output_path):
                print(f"[{i}/{len(papers)}] [SKIP] Already exists — {paper['title'][:60]}")
                skipped += 1
                continue
            
            print(f"{i}/{len(papers)} Downloading: {paper['title'][:60]} ...")
            result = download_pdf(paper)

            if result:
                success+=1
            else:
                failure+=1

            time.sleep(DELAY_SECS)
        print(f"\n{'='*50}")
        print(f"Downloaded: {success}")
        print(f"Failed:     {failure}")
        print(f"Skipped:    {skipped} (already existed)")
        print(f"Total PDFs in folder: {success + skipped}")
    
    except Exception as e:
        print(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()

