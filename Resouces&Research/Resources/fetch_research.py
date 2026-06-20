#Semantic Scholar API 


import requests
import json

response = requests.get(
    "https://api.semanticscholar.org/graph/v1/paper/search/bulk",
    params = {
        "query": "oral squamous cell carcinoma",
        "fields": "title,abstract,year,isOpenAccess,openAccessPdf,publicationTypes,citationCount",
        "openAccessPdf": "",  # filters to open access only — no value needed
        "publicationTypes": "Review,JournalArticle,ClinicalTrial,MetaAnalysis",
        "year": "2012-2025",
        "fieldsOfStudy": "Medicine"
    }
)

data = response.json()
print(f"Estimated total matches: {data['total']}")
papers = data["data"]

clean_papers = [p for p in papers if p.get("abstract")]
print(f"usable papers with abtracts:{len(clean_papers)}")


#Top 100 cited papers
sorted_top_cited = sorted(clean_papers, key = lambda p: p.get("citationCount", 0), reverse = True)[:100]

#Recent Research Papers apart from the citation after 2022
recent_papers = [p for p in clean_papers if p.get("year", 0) >= 2022]
sorted_year_papers = sorted(clean_papers, key = lambda p: p.get("year", 0), reverse = True)[:50]

combined = {p["paperId"]: p for p in sorted_top_cited + sorted_year_papers}

final_papers = list(combined.values())

print(f"Final Dataset: {len(final_papers)} papers")
    
with open("oral_cancer_papers.json", "w", encoding="utf-8") as f:
    json.dump(final_papers, f, indent=2, ensure_ascii=False)

print(f"Saved {len(final_papers)} papers to oral_cancer_papers.json")
