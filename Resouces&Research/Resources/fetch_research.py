import logging
import requests
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

response = requests.get(
    "https://api.semanticscholar.org/graph/v1/paper/search/bulk",
    params={
        "query":            "oral squamous cell carcinoma",
        "fields":           "title,abstract,year,isOpenAccess,openAccessPdf,publicationTypes,citationCount",
        "openAccessPdf":    "",
        "publicationTypes": "Review,JournalArticle,ClinicalTrial,MetaAnalysis",
        "year":             "2012-2025",
        "fieldsOfStudy":    "Medicine"
    }
)

data = response.json()
logger.info(f"Estimated total matches: {data['total']}")
papers = data["data"]

clean_papers = [p for p in papers if p.get("abstract")]
logger.info(f"Usable papers with abstracts: {len(clean_papers)}")

sorted_top_cited   = sorted(clean_papers, key=lambda p: p.get("citationCount", 0), reverse=True)[:100]
recent_papers      = [p for p in clean_papers if p.get("year", 0) >= 2022]
sorted_year_papers = sorted(clean_papers, key=lambda p: p.get("year", 0), reverse=True)[:50]

combined     = {p["paperId"]: p for p in sorted_top_cited + sorted_year_papers}
final_papers = list(combined.values())

logger.info(f"Final dataset: {len(final_papers)} papers")

with open("oral_cancer_papers.json", "w", encoding="utf-8") as f:
    json.dump(final_papers, f, indent=2, ensure_ascii=False)

logger.info(f"Saved {len(final_papers)} papers to oral_cancer_papers.json")
