import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

INPUT_FILE  = "oral_cancer_papers_clean.json"
OUTPUT_FILE = "oral_cancer_papers_final.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    papers = json.load(f)

logger.info(f"Starting count: {len(papers)}")

DROP_TITLES = [
    "Esophageal cancer in an adult with congenital esophageal stenosis: a case report",
]

before = len(papers)
papers = [p for p in papers if p["title"] not in DROP_TITLES]
after  = len(papers)

logger.info(f"Dropped {before - after} paper(s) by manual review:")
for t in DROP_TITLES:
    logger.info(f"  - {t}")

logger.info("Kept (despite 'case report'-like title, has generalizable value):")
logger.info("  - A Rare Synchronous Existence of Warthin's Tumour and Oral Cancer: A systematic review")
logger.info("    (17-case systematic review, not a single case report)")

logger.info(f"Final dataset count: {len(papers)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(papers, f, indent=2, ensure_ascii=False)

logger.info(f"Saved final dataset to {OUTPUT_FILE}")
