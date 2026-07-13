"""
ingestion/fetch_papers.py

Searches Semantic Scholar for oral squamous cell carcinoma papers,
keeps the top-cited and most-recent subset, and saves the raw result.

Output: data/processed/oral_cancer_papers.json

Run:
    python -m ingestion.fetch_papers
"""

import json
import requests

from ingestion.config import RAW_PAPERS_FILE
from utils.logger import get_logger

logger = get_logger(__name__)

SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
SEARCH_PARAMS = {
    "query":            "oral squamous cell carcinoma",
    "fields":           "title,abstract,year,isOpenAccess,openAccessPdf,publicationTypes,citationCount",
    "openAccessPdf":    "",
    "publicationTypes": "Review,JournalArticle,ClinicalTrial,MetaAnalysis",
    "year":             "2012-2025",
    "fieldsOfStudy":    "Medicine",
}


def main():
    response = requests.get(SEARCH_URL, params=SEARCH_PARAMS)
    data = response.json()
    logger.info(f"Estimated total matches: {data['total']}")

    papers = data["data"]
    clean_papers = [p for p in papers if p.get("abstract")]
    logger.info(f"Usable papers with abstracts: {len(clean_papers)}")

    sorted_top_cited   = sorted(clean_papers, key=lambda p: p.get("citationCount", 0), reverse=True)[:100]
    sorted_year_papers = sorted(clean_papers, key=lambda p: p.get("year", 0), reverse=True)[:50]

    combined     = {p["paperId"]: p for p in sorted_top_cited + sorted_year_papers}
    final_papers = list(combined.values())

    logger.info(f"Final dataset: {len(final_papers)} papers")

    with open(RAW_PAPERS_FILE, "w", encoding="utf-8") as f:
        json.dump(final_papers, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(final_papers)} papers to {RAW_PAPERS_FILE}")


if __name__ == "__main__":
    main()
