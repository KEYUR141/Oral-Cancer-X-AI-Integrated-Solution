"""
embeddings/embed_fulltext.py

Embeds every extracted full-text chunk and upserts them into `papers`
as source='fulltext'.

Input: data/pdfs/extracted_text/*.json

Run:
    python -m embeddings.embed_fulltext
"""

import os
import json

from ingestion.config import EXTRACTED_TEXT_DIR
from embeddings.embedder import embed_texts
from db.upsert import upsert_rows
from utils.logger import get_logger

logger = get_logger(__name__)

BATCH_SIZE = 16


def main():
    json_files = [f for f in os.listdir(EXTRACTED_TEXT_DIR) if f.endswith(".json")]
    logger.info(f"Found {len(json_files)} files in the raw extracted text")

    all_chunks = []
    for file_name in json_files:
        filepath = os.path.join(EXTRACTED_TEXT_DIR, file_name)
        with open(filepath, "r", encoding="utf-8") as f:
            paper = json.load(f)

        for chunk in paper["chunks"]:
            all_chunks.append({
                "paper_id":    paper["paper_id"],
                "title":       paper["title"],
                "chunk_index": chunk["chunk_index"],
                "text":        chunk["text"],
            })

    logger.info(f"Total chunks to embed: {len(all_chunks)}")

    texts = [c["text"] for c in all_chunks]
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        all_embeddings.extend(embed_texts(batch, batch_size=BATCH_SIZE))
        logger.info(f"Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} chunks")

    rows = [
        {
            "paper_id":       chunk["paper_id"],
            "title":          chunk["title"],
            "abstract":       chunk["text"],
            "embedding_text": chunk["text"],
            "embedding":      vector,
            "source":         "fulltext",
            "chunk_index":    chunk["chunk_index"],
            "citation_count": 0,
            "is_open_access": True,
            "publication_types": [],
        }
        for chunk, vector in zip(all_chunks, all_embeddings)
    ]

    upsert_rows(rows)
    logger.info(f"Pushed {len(rows)} chunks to database.")


if __name__ == "__main__":
    main()
