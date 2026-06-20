import json

INPUT_FILE = "oral_cancer_papers_clean.json"
OUTPUT_FILE = "oral_cancer_papers_final.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    papers = json.load(f)

print(f"Starting count: {len(papers)}")

# Manual call: titles to drop (not generalizable enough / off-focus for OSCC RAG)
DROP_TITLES = [
    "Esophageal cancer in an adult with congenital esophageal stenosis: a case report",
]

before = len(papers)
papers = [p for p in papers if p["title"] not in DROP_TITLES]
after = len(papers)

print(f"Dropped {before - after} paper(s) by manual review:")
for t in DROP_TITLES:
    print(f"  - {t}")

print(f"\nKept (despite 'case report'-like title, has generalizable value):")
print("  - A Rare Synchronous Existence of Warthin's Tumour and Oral Cancer: A systematic review")
print("    (17-case systematic review, not a single case report)")

print(f"\nFinal dataset count: {len(papers)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(papers, f, indent=2, ensure_ascii=False)

print(f"Saved final dataset to {OUTPUT_FILE}")