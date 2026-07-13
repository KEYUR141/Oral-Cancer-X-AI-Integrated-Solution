from sqlalchemy.dialects.postgresql import insert as pg_insert
from db.database import get_db
from db.models import papers_table


def upsert_rows(rows: list[dict]) -> int:
    """
    Upsert a batch of rows into `papers`. Each dict must contain at least
    paper_id, source, and chunk_index. Conflicts on the (paper_id, source,
    chunk_index) unique index are ignored, matching papers_unique_chunk.
    """
    if not rows:
        return 0

    stmt = pg_insert(papers_table).values(rows).on_conflict_do_nothing(
        index_elements=["paper_id", "source", "chunk_index"]
    )

    with get_db() as conn:
        conn.execute(stmt)

    return len(rows)
