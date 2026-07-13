"""
embeddings/embed_captions.py

Embeds every figure caption from data/pdfs/visuals/*.json and upserts
them into `papers` as source='figure_captions'.

Input: data/pdfs/visuals/*.json  (written by ingestion/extract_visuals.py)

Run:
    python -m embeddings.embed_captions
"""

import os
import json

from ingestion.config import VISUALS_DIR
from embeddings.embedder import embed_texts
from db.upsert import upsert_rows
from utils.logger import get_logger

logger = get_logger(__name__)

BATCH_SIZE = 16


def main():
    manifest_files = [f for f in os.listdir(VISUALS_DIR) if f.endswith(".json")]
    logger.info(f"Found {len(manifest_files)} visuals manifests")

    captions = []
    for file_name in manifest_files:
        with open(os.path.join(VISUALS_DIR, file_name), "r", encoding="utf-8") as f:
            captions.extend(json.load(f))

    logger.info(f"Loaded {len(captions)} captions")

    texts = [c["embedding_text"] for c in captions]
    embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        embeddings.extend(embed_texts(batch, batch_size=BATCH_SIZE))
        logger.info(f"Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} captions")

    rows = [
        {
            "paper_id":       caption["paper_id"],
            "title":          caption["title"],
            "abstract":       caption["caption"],
            "embedding_text": caption["embedding_text"],
            "embedding":      vector,
            "source":         "figure_captions",
            "chunk_index":    caption["chunk_index"],
            "citation_count": 0,
            "is_open_access": True,
            "publication_types": [],
            "image_path":     caption["image_path"],
        }
        for caption, vector in zip(captions, embeddings)
    ]

    upsert_rows(rows)
    logger.info(f"Pushed {len(rows)} captions to database.")


if __name__ == "__main__":
    main()
