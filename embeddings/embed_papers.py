import json
from sentence_transformers import SentenceTransformer

INPUT_FILE = "D:\project_Major\Oral-Cancer-X-AI-Integrated-Solution\data\processed\oral_cancer_papers_final.json"
OUTPUT_FILE = "oral_cancer_papers_embedded.json"
MODEL_NAME = "pritamdeka/S-PubMedBert-MS-MARCO"

def build_embedding_text(paper:dict) -> str:
    title = (paper.get('title') or "").strip()
    abstract = (paper.get('abstract') or "").strip()
    return f"{title}- {abstract}"

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        papers = json.load(f)

    print(f"Loaded {len(papers)} papers")
    print(f"Loading embedding models: {MODEL_NAME} -First Run downloads ~400 mb")

    model = SentenceTransformer(MODEL_NAME)
    texts = [build_embedding_text(p) for p in papers]

    print("Embedding Papers in Batched")
    embeddings = model.encode(
        texts,
        batch_size = 16,
        show_progress_bar = True,
        normalize_embeddings = True, 
    )

    print(f'Embedding Dimension: {embeddings.shape[1]}')

    enriched = []

    for paper, vector in zip(papers, embeddings):
        enriched.append({
            "paper_id": paper.get("paperId"),
            "title": paper.get("title"),
            "abstract": paper.get("abstract"),
            "year": paper.get("year"),
            "citation_count": paper.get("citationCount", 0),
            "is_open_access": paper.get("isOpenAccess", False),
            "publication_types": paper.get("publicationTypes", []),
            "open_access_pdf_url": (paper.get("openAccessPdf") or {}).get("url"),
            "embedding_text": build_embedding_text(paper),
            "embedding": vector.tolist(),  # JSON-serializable
        })
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(enriched, f, ensure_ascii=False)
 
    print(f"Saved {len(enriched)} embedded papers to {OUTPUT_FILE}")
 
if __name__ == "__main__":
    main()

