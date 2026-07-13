from sqlalchemy import text
from db.database import get_db
from embeddings.embedder import embed_texts
from utils.logger import get_logger

logger = get_logger(__name__)

TOP_K = 10
MIN_SIMILARITY_THRESHOLD = 0.88


def embed_query(query: str) -> list[float]:
    try:
        return embed_texts([query])[0]
    except Exception as e:
        logger.error(f"Error embedding query: {e}")
        raise


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    try:
        query_vector = embed_query(query)
        sql = text("""
            SELECT DISTINCT ON (p.paper_id)
                p.paper_id,
                p.title,
                p.abstract,
                COALESCE(p.year, a.year) AS year,
                COALESCE(p.citation_count, a.citation_count) AS citation_count,
                COALESCE(p.publication_types, a.publication_types) AS publication_types,
                COALESCE(p.open_access_pdf_url, a.open_access_pdf_url) AS open_access_pdf_url,
                COALESCE(p.image_path, a.image_path) AS image_path,
                p.source,
                p.similarity
            FROM (
                SELECT
                    paper_id,
                    title,
                    abstract,
                    year,
                    citation_count,
                    publication_types,
                    open_access_pdf_url,
                    image_path,
                    source,
                    1 - (embedding <=> CAST(:query_vector AS vector)) AS similarity
                FROM papers
                WHERE source IN ('abstract', 'fulltext','figure_captions')
                ORDER BY embedding <=> CAST(:query_vector AS vector)
                LIMIT :top_k
            ) p
            LEFT JOIN papers a
                ON a.paper_id = p.paper_id
                AND a.source = 'abstract'
            ORDER BY p.paper_id, p.similarity DESC
        """)

        papers = []
        

        with get_db() as conn:
            result = conn.execute(sql, {
                "query_vector": query_vector,
                "top_k": top_k * 30
            })
            rows = result.fetchall()

            for row in rows:
                similarity = round(float(row.similarity), 4)
                if similarity < MIN_SIMILARITY_THRESHOLD:
                    continue

                papers.append({
                    "paper_id":            row.paper_id,
                    "title":               row.title,
                    "abstract":            row.abstract,
                    "year":                row.year,
                    "citation_count":      row.citation_count,
                    "publication_types":   row.publication_types,
                    "open_access_pdf_url": row.open_access_pdf_url,
                    "image_path":          row.image_path,
                    "source":              row.source,
                    "similarity":          round(float(row.similarity), 4),
                })

        return papers

    except Exception as e:
        logger.error(f"Error retrieving papers: {e}")
        raise


if __name__ == "__main__":
    test_query = "histopathology IHC staining OSCC tumor specimens"
    logger.info(f"Query: {test_query}\n")

    results = retrieve(test_query)

    for i, paper in enumerate(results, 1):
        source_tag = f"[{paper['source'].upper()}]"
        image_tag  = " 🖼" if paper["image_path"] else ""
        logger.info(
            f"{i}. {source_tag}{image_tag} [{paper['similarity']}] "
            f"({paper['year']}) {paper['title'][:60]}"
        )
