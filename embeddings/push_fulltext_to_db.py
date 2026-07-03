import json
from sqlalchemy.dialects.postgresql import insert as pg_insert
from db.database import get_db
from db.models import papers_table
from utils.logger import get_logger

logger = get_logger(__name__)

INPUT_FILE = "data/pdfs/embedded_chunks.json"


def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        logger.info(f"Loaded {len(chunks)} chunks from JSON")

        with get_db() as conn:
            inserted = 0

            for chunk in chunks:
                stmt = pg_insert(papers_table).values(
                    paper_id=            chunk["paper_id"],
                    title=               chunk["title"],
                    abstract=            chunk["text"],
                    embedding_text=      chunk["text"],
                    embedding=           chunk["embedding"],
                    source=              "fulltext",
                    chunk_index=         chunk["chunk_index"],
                    year=                None,
                    citation_count=      0,
                    is_open_access=      True,
                    publication_types=   [],
                    open_access_pdf_url= None,
                ).on_conflict_do_nothing(
                    index_elements=["paper_id", "source", "chunk_index"]
                )

                conn.execute(stmt)
                inserted += 1
                if inserted % 200 == 0:
                    logger.info(f"Inserted {inserted}/{len(chunks)} chunks")

        logger.info(f"Done. {inserted} chunks pushed to database.")

    except Exception as e:
        logger.error(f"Error inserting chunks: {e}")
        raise


if __name__ == "__main__":
    main()
