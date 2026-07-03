import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

INPUT_FILE  = "oral_cancer_papers.json"
OUTPUT_FILE = "oral_cancer_papers_clean.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    papers = json.load(f)

logger.info(f"Total papers loaded: {len(papers)}")

ids   = [p["paperId"] for p in papers]
dupes = len(ids) - len(set(ids))
logger.info(f"Duplicate paperIds: {dupes}")

JUNK_PATTERNS = [
    "answer questions and earn cme",
    "cme/cne",
]


def is_junk_abstract(abstract):
    if not abstract:
        return True
    a = abstract.lower().strip()
    if len(a) < 150:
        return True
    for pat in JUNK_PATTERNS:
        if pat in a:
            return True
    return False


junk = [p["title"] for p in papers if is_junk_abstract(p.get("abstract"))]
logger.info(f"Papers with junk/placeholder/too-short abstracts: {len(junk)}")
for t in junk:
    logger.info(f"  - {t}")

ON_TOPIC_KEYWORDS = [
    "oral", "mouth", "oscc", "hnscc", "oropharyn", "buccal", "tongue",
    "gingiva", "head and neck", "betel", "leukoplakia"
]


def is_on_topic(paper):
    text = (paper.get("title", "") + " " + (paper.get("abstract") or "")).lower()
    return any(kw in text for kw in ON_TOPIC_KEYWORDS)


off_topic = [p["title"] for p in papers if not is_on_topic(p)]
logger.info(f"Papers that may be OFF-TOPIC (no oral/HN keywords found): {len(off_topic)}")
for t in off_topic:
    logger.info(f"  - {t}")

case_report_signals = ["case report", "a case of", "synchronous", "rare case"]
case_reports = [p["title"] for p in papers
                if any(sig in p["title"].lower() for sig in case_report_signals)]
logger.info(f"Likely single case reports (review before keeping): {len(case_reports)}")
for t in case_reports:
    logger.info(f"  - {t}")

clean_papers = [
    p for p in papers
    if not is_junk_abstract(p.get("abstract")) and is_on_topic(p)
]

logger.info("--- SUMMARY ---")
logger.info(f"Original: {len(papers)}")
logger.info(f"Removed (junk abstract or off-topic): {len(papers) - len(clean_papers)}")
logger.info(f"Final clean dataset: {len(clean_papers)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(clean_papers, f, indent=2, ensure_ascii=False)

logger.info(f"Saved cleaned dataset to {OUTPUT_FILE}")
