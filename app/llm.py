import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"


def build_prompt(query: str, retrieved_papers: list[dict]) -> str:
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
            -If the papers contain RELATED information but not the exact answer, provide
                what IS available and note what specific data is missing.
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
        logger.error(f"Error building prompt: {e}")
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

        logger.debug(f"\n{'='*60}\n{prompt}\n{'='*60}")

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
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
                    "image_path":     (
                        p["image_path"].replace("data/pdfs/images/", "/images/")
                        if p.get("image_path") else None
                    ),
                }
                for i, p in enumerate(retrieved_papers)
            ],
        }
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        raise


if __name__ == "__main__":
    from app.retrieval import retrieve

    query = "what is the survival rate for stage 2 oral cancer"
    logger.info(f"Query: {query}")
    logger.info("Retrieving papers...")

    papers = retrieve(query)
    logger.info(f"Retrieved {len(papers)} papers")

    logger.info("Generating answer...")
    result = generate_answer(query, papers)

    logger.info("=" * 60)
    logger.info(result["answer"])
    logger.info("=" * 60)
    logger.info(f"Sources used: {len(result['sources'])}")
    for s in result["sources"]:
        logger.info(f"  [{s['number']}] ({s['year']}) {s['title']}")
