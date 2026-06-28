import os
import json
from sentence_transformers import SentenceTransformer

INPUT_DIR   = "data/pdfs/extracted_text"
OUTPUT_FILE = "data/pdfs/embedded_chunks.json"
MODEL_NAME  = "pritamdeka/S-PubMedBert-MS-MARCO"
BATCH_SIZE  = 16

model = SentenceTransformer(MODEL_NAME)

def main():
    try:
        json_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".json")]
        print(f"Found {len(json_files)} in the raw extracted text")

        all_chunks = []

        for file_name in json_files:
            filepath = os.path.join(INPUT_DIR, file_name)
            with open(filepath, "r", encoding = "utf-8") as f:
                paper = json.load(f)

            for chunk in paper['chunks']:
                all_chunks.append({
                "paper_id":    paper["paper_id"],
                "title":       paper["title"],
                "chunk_index": chunk["chunk_index"],
                "text":        chunk["text"],
                })
            
            print(f"Total chunks to embed: {len(all_chunks)}")

        texts = [c['text'] for c in all_chunks]

        print("Embedding chunks...\n")
        all_embeddings = []

        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            batch_vecs  = model.encode(
            batch,
            batch_size=BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
            )
            all_embeddings.extend(batch_vecs)

            done = min(i + BATCH_SIZE, len(texts))
            print(f"  Embedded {done}/{len(texts)} chunks")

        enriched = []
        for chunk, vector in zip(all_chunks, all_embeddings):
            enriched.append({
            "paper_id":    chunk["paper_id"],
            "title":       chunk["title"],
            "chunk_index": chunk["chunk_index"],
            "text":        chunk["text"],
            "embedding":   vector.tolist(),
        })
            
        with open(OUTPUT_FILE,"w", encoding="utf-8") as f:
            json.dump(enriched, f, indent =2, ensure_ascii=False)
        
        print(f"\nSaved {len(enriched)} embedded chunks to {OUTPUT_FILE}")
    
    except Exception as e:
        print(f"Error Raised: {e}")

if __name__ == "__main__":
    main()