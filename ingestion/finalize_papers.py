"""
ingestion/finalize_papers.py

Applies a manually-curated drop list on top of the cleaned paper set.

Input:  data/processed/oral_cancer_papers_clean.json
Output: data/processed/oral_cancer_papers_final.json

Run:
    python -m ingestion.finalize_papers
"""

import json

from ingestion.config import CLEAN_PAPERS_FILE, FINAL_PAPERS_FILE
from utils.logger import get_logger

logger = get_logger(__name__)

DROP_TITLES = [
    "Esophageal cancer in an adult with congenital esophageal stenosis: a case report",
]


def main():
    with open(CLEAN_PAPERS_FILE, "r", encoding="utf-8") as f:
        papers = json.load(f)

    logger.info(f"Starting count: {len(papers)}")

    before = len(papers)
    papers = [p for p in papers if p["title"] not in DROP_TITLES]
    after  = len(papers)

    logger.info(f"Dropped {before - after} paper(s) by manual review:")
    for t in DROP_TITLES:
        logger.info(f"  - {t}")

    logger.info(f"Final dataset count: {len(papers)}")

    with open(FINAL_PAPERS_FILE, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved final dataset to {FINAL_PAPERS_FILE}")


if __name__ == "__main__":
    main()
