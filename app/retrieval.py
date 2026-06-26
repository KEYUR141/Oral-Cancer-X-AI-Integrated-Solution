from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from db.database import get_db

MODEL_NAME ="pritamdeka/S-PubMedBERT-MS-MARCO"
TOP_K = 10

model = SentenceTransformer(MODEL_NAME)

def embed_query(query:str) -> list[float]:
   
    try:
        vector = model.encode(
            query,
            normalize_embeddings=True
        )

        return vector.tolist()
    except Exception as e:
        print(f"Error embedding query: {e}")
        raise

def retrieve(query:str, top_k:int = TOP_K) -> list[dict]:
    try:
        query_vector = embed_query(query)
        sql = text("""
            SELECT
            paper_id,
            title,
            abstract,
            year,
            citation_count,
            publication_types,
            open_access_pdf_url,
            1 - (embedding <=> CAST(:query_vector AS vector)) AS similarity
        FROM papers
        WHERE source = 'abstract'
        ORDER BY embedding <=> CAST(:query_vector AS vector)
        LIMIT :top_k
        """)

        papers = []
        MIN_SIMILARITY_THRESHOLD = 0.88
        
        with get_db() as conn:
            result = conn.execute(sql,{
                "query_vector": query_vector,
                "top_k": top_k
            })
            rows = result.fetchall()

            
            
            for row in rows:
                similarity = round(float(row.similarity), 4)
                if similarity < MIN_SIMILARITY_THRESHOLD:
                    continue
                
                papers.append({
                "paper_id":           row.paper_id,
                "title":              row.title,
                "abstract":           row.abstract,
                "year":               row.year,
                "citation_count":     row.citation_count,
                "publication_types":  row.publication_types,
                "open_access_pdf_url":row.open_access_pdf_url,
                "similarity":         round(float(row.similarity), 4),
                })

        return papers
    
    except Exception as e:
        print(f"Error retrieving papers: {e}")
        raise


if __name__ == "__main__":
    test_query = "My friends are bad"
    print(f"Query: {test_query}\n")

    results = retrieve(test_query)

    for i, paper in enumerate(results, 1):
        print(f"{i}. [{paper['similarity']}] ({paper['year']}) {paper['title']}")