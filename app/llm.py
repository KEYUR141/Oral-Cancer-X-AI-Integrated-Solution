import os
import google.generativeai as genai

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

genai.configure(api_key = GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

def build_prompt(query:str, retrieved_papers:list[dict]) -> str:
    try:
        context_blocks = []
        for i, paper in enumerate(retrieved_papers, 1):
            block = (
            f"[{i}] {paper['title']} ({paper['year']})\n"
            f"Similarity Score: {paper['similarity']}\n"
            f"Abstract: {paper['abstract']}"
        )
            context_blocks.append(block)

        context = "\n\n".join(context_blocks)

        prompt = f"""You are a medical research assistant specializing in oral cancer.
            You help doctors and researchers find answers grounded in peer-reviewed literature.

            STRICT RULES:
            - Answer ONLY using the provided research papers below.
            - Do NOT use any knowledge outside of the provided context.
            - Cite every claim using the paper number in square brackets e.g. [1], [3].
            - If the provided papers do not contain enough information to answer, say:
                "The available research does not provide sufficient information on this topic."
            - Do NOT speculate or add information beyond what the papers state.
            - Keep the answer clear, structured, and clinically useful.
            - End your answer with a "Sources" section listing the papers you cited.

            RESEARCH PAPERS:
            {context}

            QUESTION:
            {query}

            ANSWER:"""

        return prompt
    
    except Exception as e:
        print(f"Error building prompt: {e}")
        raise


def generate_answer(query: str, retrieved_papers: list[dict]) -> str:
    try:
        if not retrieved_papers:
            return {
                "query":   query,
                "answer":  "No relevant research papers were found for this query. "
                           "Please try rephrasing your question using clinical terminology.",
                "sources": [],
            }
        
        prompt = build_prompt(query, retrieved_papers)

        print("=" * 60)
        print(prompt)
        print("=" * 60)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2,   # low temperature = factual, consistent answers
                                # not creative — you want grounded medical responses
                max_output_tokens=1500,
            ),
        )

        return {
            "query":   query,
            "answer":  response.text,
            "sources": [
                {
                    "number":         i + 1,
                    "title":          p["title"],
                    "year":           p["year"],
                    "similarity":     p["similarity"],
                    "citation_count": p["citation_count"],
                    "pdf_url":        p.get("open_access_pdf_url"),
                }
                for i, p in enumerate(retrieved_papers)
            ],
            
        }
    except Exception as e:
        print(f"Error generating answer: {e}")
        raise

if __name__ == "__main__":
    from app.retrieval import retrieve

    query = "what are the risk factors for oral cancer in South Asia"
    print(f"Query: {query}\n")
    print("Retrieving papers...")

    papers = retrieve(query)
    print(f"Retrieved {len(papers)} papers\n")

    print("Generating answer...\n")
    result = generate_answer(query, papers)

    

    print("=" * 60)
    print(result["answer"])
    print("=" * 60)
    print(f"\nSources used: {len(result['sources'])}")
    for s in result["sources"]:
        print(f"  [{s['number']}] ({s['year']}) {s['title']}")
        
