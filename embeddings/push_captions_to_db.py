import json
import os
from sqlalchemy.dialects.postgresql import insert as pg_insert
from db.database import get_db
from db.models import papers_table
from sqlalchemy import text

from utils.logger import get_logger
logger = get_logger(__name__)

INPUT_FILE = "data/pdfs/figure_captions.json"


def get_year_for_paper(conn, paper_id:str)-> int | None:
    try:
        result = conn.execute(
            text("SELECT year FROM papers WHERE paper_id=:pid AND source='abstract'"),
            {"pid": paper_id}
        ).fetchone()
        return result.year if result else None
    except Exception as e:
        logger.error(f"Error fetching year for paper_id {paper_id}: {e}")
        return None
    
def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            captions = json.load(f)

        logger.info(f"Loaded {len(captions)} captions from JSON")

        with get_db() as conn:
            inserted = 0

            for caption in captions:
                paper_id = caption["paper_id"]
                year = get_year_for_paper(conn, paper_id)

                stmt = pg_insert(papers_table).values(
                    paper_id=            paper_id,
                    title=               caption.get("title"),
                    abstract=            caption.get("caption"),
                    embedding_text=      caption.get("caption"),
                    embedding=           caption.get("embedding"),
                    source=              "figure_caption",
                    chunk_index=         0,
                    year=                year,
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
                    logger.info(f"Inserted {inserted}/{len(captions)} captions")

        logger.info(f"Done. {inserted} captions pushed to database.")

    except Exception as e:
        logger.error(f"Error inserting captions: {e}")
        raise

if __name__ == "__main__":
    main()