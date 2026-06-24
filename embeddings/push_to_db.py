import json
from sqlalchemy import text
from db.database import get_db
from db.models import papers_table

INPUT_FILE = "D:\project_Major\Oral-Cancer-X-AI-Integrated-Solution\embeddings\oral_cancer_papers_embedded.json"

ON_TOPIC_KEYWORDS = [
    "oral", "mouth", "oscc", "hnscc", "oropharyn",
    "buccal", "tongue", "gingiva", "head and neck",
    "betel", "leukoplakia"
]

def is_on_topic(paper):
    text = (
        (paper.get("title") or "") + " " +
        (paper.get("abstract") or "")
    ).lower()
    return any(kw in text for kw in ON_TOPIC_KEYWORDS)


def load_papers(filepath):
    try:

        with open(filepath, "r", encoding = "utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading papers from {filepath}: {e}")
        raise
    

def push_to_db(papers):
    try:
        insert_stmt = papers_table.insert().values(
            paper_id=         text(":paper_id"),
            title=            text(":title"),
            abstract=         text(":abstract"),
            year=             text(":year"),
            citation_count=   text(":citation_count"),
            is_open_access=   text(":is_open_access"),
            publication_types=text(":publication_types"),
            open_access_pdf_url=text(":open_access_pdf_url"),
            embedding_text=   text(":embedding_text"),
            embedding=        text(":embedding"),
            source=           text(":source"),
            chunk_index=      text(":chunk_index"),
        )
        final_papers = [p for p in papers if is_on_topic(p)]
        print(f"On-topic papers after filter: {len(final_papers)}")


        with get_db() as conn:
            inserted = 0
            for paper in final_papers:
                conn.execute(insert_stmt, {
                    "paper_id":           paper["paper_id"],
                    "title":              paper["title"],
                    "abstract":           paper.get("abstract"),
                    "year":               paper.get("year"),
                    "citation_count":     paper.get("citation_count", 0),
                    "is_open_access":     paper.get("is_open_access", False),
                    "publication_types":  paper.get("publication_types", []),
                    "open_access_pdf_url":paper.get("open_access_pdf_url"),
                    "embedding_text":     paper.get("embedding_text"),
                    "embedding":          paper["embedding"],
                    "source":             "abstract",
                    "chunk_index":        0,
                })
                inserted+=1
                if inserted % 20 == 0:
                    print(f"Inserted {inserted} papers...")
        print(f"Inserted {inserted} papers in total.")
    except Exception as e:
        print(f"Error inserting papers: {e}")
        raise

def main():
    print(f"Loading papers from {INPUT_FILE}")
    papers = load_papers(INPUT_FILE)
    print(f"Loaded {len(papers)} papers. Pushing to database...")
    push_to_db(papers)


if __name__ =="__main__":
    main()
