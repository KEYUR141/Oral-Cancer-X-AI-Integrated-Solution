"""
ingestion/clean_papers.py

Dedupes and filters the raw paper list: drops junk/placeholder abstracts
and off-topic papers.

Input:  data/processed/oral_cancer_papers.json
Output: data/processed/oral_cancer_papers_clean.json

Run:
    python -m ingestion.clean_papers
"""

import json

from ingestion.config import RAW_PAPERS_FILE, CLEAN_PAPERS_FILE
from utils.logger import get_logger

logger = get_logger(__name__)

JUNK_PATTERNS = [
    "answer questions and earn cme",
    "cme/cne",
]

ON_TOPIC_KEYWORDS = [
    "oral", "mouth", "oscc", "hnscc", "oropharyn", "buccal", "tongue",
    "gingiva", "head and neck", "betel", "leukoplakia",
]


def is_junk_abstract(abstract):
    if not abstract:
        return True
    a = abstract.lower().strip()
    if len(a) < 150:
        return True
    return any(pat in a for pat in JUNK_PATTERNS)


def is_on_topic(paper):
    text = (paper.get("title", "") + " " + (paper.get("abstract") or "")).lower()
    return any(kw in text for kw in ON_TOPIC_KEYWORDS)


def main():
    with open(RAW_PAPERS_FILE, "r", encoding="utf-8") as f:
        papers = json.load(f)

    logger.info(f"Total papers loaded: {len(papers)}")

    ids   = [p["paperId"] for p in papers]
    dupes = len(ids) - len(set(ids))
    logger.info(f"Duplicate paperIds: {dupes}")

    junk = [p["title"] for p in papers if is_junk_abstract(p.get("abstract"))]
    logger.info(f"Papers with junk/placeholder/too-short abstracts: {len(junk)}")

    off_topic = [p["title"] for p in papers if not is_on_topic(p)]
    logger.info(f"Papers that may be OFF-TOPIC (no oral/HN keywords found): {len(off_topic)}")

    case_report_signals = ["case report", "a case of", "synchronous", "rare case"]
    case_reports = [
        p["title"] for p in papers
        if any(sig in p["title"].lower() for sig in case_report_signals)
    ]
    logger.info(f"Likely single case reports (review before keeping): {len(case_reports)}")

    clean_papers = [
        p for p in papers
        if not is_junk_abstract(p.get("abstract")) and is_on_topic(p)
    ]

    logger.info("--- SUMMARY ---")
    logger.info(f"Original: {len(papers)}")
    logger.info(f"Removed (junk abstract or off-topic): {len(papers) - len(clean_papers)}")
    logger.info(f"Final clean dataset: {len(clean_papers)}")

    with open(CLEAN_PAPERS_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_papers, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved cleaned dataset to {CLEAN_PAPERS_FILE}")


if __name__ == "__main__":
    main()
