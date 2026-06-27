import json
from sqlalchemy import insert
from db.database import get_db
from db.models import papers_table

INPUT_FILE = "data/pdfs/embeddings_chunks.json"

def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        print(f"Loaded {len(chunks)} Chunks from JSON")

        with get_db() as conn:
            inserted = 0

            for chunk in chunks:
                conn.execute(
                    insert(papers_table).values(
                        paper_id=           chunk["paper_id"],
                        title=              chunk["title"],
                        abstract=           chunk["text"],    # text stored in abstract column
                        embedding_text=     chunk["text"],
                        embedding=          chunk["embedding"],
                        source=             "fulltext",
                        chunk_index=        chunk["chunk_index"],
                        year=               None,
                        citation_count=     0,
                        is_open_access=     True,
                        publication_types=  [],
                        open_access_pdf_url=None,
                ).prefix_with("ON CONFLICT (paper_id) DO NOTHING")
                )

                inserted+=1

                if inserted % 200 == 0:
                    print(f"  Inserted {inserted}/{len(chunks)} chunks")
            print(f"Inserted {inserted} chunks in total.")
    
    except Exception as e:
        print(f"Error inserting chunks: {e}")
        raise

if __name__ =="__main__":
    main()
                