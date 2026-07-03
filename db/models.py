from sqlalchemy import (
    MetaData, Table, Column,
    Integer, Text, Boolean, ARRAY, TIMESTAMP,
    Index, func, text
)
from pgvector.sqlalchemy import Vector
from db.database import engine
from utils.logger import get_logger

logger = get_logger(__name__)

metadata = MetaData()

papers_table = Table("papers", metadata,

    Column("id",         Integer, primary_key=True, autoincrement=True),
    Column("paper_id",   Text,    unique=True, nullable=False),

    Column("title",               Text,        nullable=False),
    Column("abstract",            Text),
    Column("year",                Integer),
    Column("citation_count",      Integer,     default=0),
    Column("is_open_access",      Boolean,     default=False),
    Column("publication_types",   ARRAY(Text)),
    Column("open_access_pdf_url", Text),

    Column("embedding_text", Text),
    Column("embedding",      Vector(768)),

    Column("source",      Text,    default="abstract"),
    Column("chunk_index", Integer, default=0),

    Column("created_at", TIMESTAMP, server_default=func.now()),
)


Index(
    "papers_embedding_idx",
    papers_table.c.embedding,
    postgresql_using="ivfflat",
    postgresql_with={"lists": 100},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)

Index("papers_year_idx",           papers_table.c.year)
Index("papers_citation_count_idx", papers_table.c.citation_count)
Index("papers_source_idx",         papers_table.c.source)


def create_tables():
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
        metadata.create_all(engine)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")


if __name__ == "__main__":
    create_tables()
