"""
ingestion/run_pipeline.py

Runs the full ingestion pipeline in dependency order. Each stage keeps its
own skip-if-already-done behavior, so re-running is safe and resumable.

Usage:
    python -m ingestion.run_pipeline                      # run every stage
    python -m ingestion.run_pipeline --stage extract_visuals   # run one stage
"""

import argparse

from ingestion import fetch_papers, clean_papers, finalize_papers, download_pdfs
from ingestion import extract_fulltext, extract_visuals
from embeddings import embed_papers, embed_fulltext, embed_captions, build_visualization
from utils.logger import get_logger

logger = get_logger(__name__)

STAGES = [
    ("fetch_papers",      fetch_papers.main),
    ("clean_papers",      clean_papers.main),
    ("finalize_papers",   finalize_papers.main),
    ("embed_abstracts",   embed_papers.main),
    ("download_pdfs",     download_pdfs.main),
    ("extract_fulltext",  extract_fulltext.main),
    ("embed_fulltext",    embed_fulltext.main),
    ("extract_visuals",   extract_visuals.main),
    ("embed_captions",    embed_captions.main),
    ("build_visualization", build_visualization.main),
]


def main(stage: str = "all"):
    names = [name for name, _ in STAGES]
    if stage != "all" and stage not in names:
        raise ValueError(f"Unknown stage '{stage}'. Valid stages: {names}")

    for name, fn in STAGES:
        if stage != "all" and stage != name:
            continue
        logger.info(f"=== Running stage: {name} ===")
        fn()

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="all", help="Run a single stage instead of the full pipeline")
    args = parser.parse_args()
    main(args.stage)
