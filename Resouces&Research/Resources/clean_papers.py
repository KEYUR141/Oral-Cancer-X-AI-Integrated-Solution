import json

# Point this at YOUR actual saved file
INPUT_FILE = "oral_cancer_papers.json"
OUTPUT_FILE = "oral_cancer_papers_clean.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    papers = json.load(f)

print(f"Total papers loaded: {len(papers)}")

# 1. Duplicate check
ids = [p["paperId"] for p in papers]
dupes = len(ids) - len(set(ids))
print(f"Duplicate paperIds: {dupes}")

# 2. Known placeholder / junk abstract patterns to flag
JUNK_PATTERNS = [
    "answer questions and earn cme",
    "cme/cne",
]

def is_junk_abstract(abstract):
    if not abstract:
        return True
    a = abstract.lower().strip()
    if len(a) < 150:  # real abstracts are almost always longer than this
        return True
    for pat in JUNK_PATTERNS:
        if pat in a:
            return True
    return False

junk = [p["title"] for p in papers if is_junk_abstract(p.get("abstract"))]
print(f"\nPapers with junk/placeholder/too-short abstracts: {len(junk)}")
for t in junk:
    print(f"  - {t}")

# 3. Off-topic check (simple keyword gate — flag anything that doesn't mention
#    oral/mouth/OSCC/HNSCC/oropharyngeal terms anywhere in title or abstract)
ON_TOPIC_KEYWORDS = [
    "oral", "mouth", "oscc", "hnscc", "oropharyn", "buccal", "tongue",
    "gingiva", "head and neck", "betel", "leukoplakia"
]

def is_on_topic(paper):
    text = (paper.get("title", "") + " " + (paper.get("abstract") or "")).lower()
    return any(kw in text for kw in ON_TOPIC_KEYWORDS)

off_topic = [p["title"] for p in papers if not is_on_topic(p)]
print(f"\nPapers that may be OFF-TOPIC (no oral/HN keywords found): {len(off_topic)}")
for t in off_topic:
    print(f"  - {t}")

# 4. Case report filter (optional — flag, don't auto-remove)
case_report_signals = ["case report", "a case of", "synchronous", "rare case"]
case_reports = [p["title"] for p in papers
                 if any(sig in p["title"].lower() for sig in case_report_signals)]
print(f"\nLikely single case reports (review before keeping): {len(case_reports)}")
for t in case_reports:
    print(f"  - {t}")

# 5. Build cleaned dataset: drop junk abstracts + off-topic, keep everything else
clean_papers = [
    p for p in papers
    if not is_junk_abstract(p.get("abstract")) and is_on_topic(p)
]

print(f"\n--- SUMMARY ---")
print(f"Original: {len(papers)}")
print(f"Removed (junk abstract or off-topic): {len(papers) - len(clean_papers)}")
print(f"Final clean dataset: {len(clean_papers)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(clean_papers, f, indent=2, ensure_ascii=False)

print(f"\nSaved cleaned dataset to {OUTPUT_FILE}")