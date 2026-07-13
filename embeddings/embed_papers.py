"""
embeddings/embed_papers.py

Embeds title+abstract for each finalized paper and upserts them into
`papers` as source='abstract'.

Input: data/processed/oral_cancer_papers_final.json

Run:
    python -m embeddings.embed_papers
"""

import json

from ingestion.config import FINAL_PAPERS_FILE
from embeddings.embedder import embed_texts
from db.upsert import upsert_rows
from utils.logger import get_logger

logger = get_logger(__name__)


def build_embedding_text(paper: dict) -> str:
    title    = (paper.get("title") or "").strip()
    abstract = (paper.get("abstract") or "").strip()
    return f"{title}- {abstract}"


def main():
    with open(FINAL_PAPERS_FILE, "r", encoding="utf-8") as f:
        papers = json.load(f)

    logger.info(f"Loaded {len(papers)} papers")

    texts = [build_embedding_text(p) for p in papers]
    logger.info("Embedding papers in batches")
    embeddings = embed_texts(texts, show_progress_bar=True)

    rows = [
        {
            "paper_id":            paper.get("paperId"),
            "title":               paper.get("title"),
            "abstract":            paper.get("abstract"),
            "year":                paper.get("year"),
            "citation_count":      paper.get("citationCount", 0),
            "is_open_access":      paper.get("isOpenAccess", False),
            "publication_types":   paper.get("publicationTypes", []),
            "open_access_pdf_url": (paper.get("openAccessPdf") or {}).get("url"),
            "embedding_text":      build_embedding_text(paper),
            "embedding":           vector,
            "source":              "abstract",
            "chunk_index":         0,
        }
        for paper, vector in zip(papers, embeddings)
    ]

    upsert_rows(rows)
    logger.info(f"Pushed {len(rows)} abstracts to database.")


if __name__ == "__main__":
    main()
