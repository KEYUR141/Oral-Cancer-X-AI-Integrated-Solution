from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.retrieval import retrieve
from app.llm import generate_answer
from utils.logger import get_logger
import time

logger = get_logger(__name__)

app = FastAPI(
    title="Oral Cancer RAG API",
    description="An API for retrieving and generating answers to questions about oral cancer using a retrieval-augmented generation (RAG) approach.",
    version="1.0.0",
)


class QueryRequest(BaseModel):
    query: str
    top_k: int = 10


class SourceSchema(BaseModel):
    number: int
    title: str
    year: int
    similarity: float
    citation_count: int
    pdf_url: str | None = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[SourceSchema]
    papers_retrieved: int
    response_time_ms: float


@app.get('/health')
async def health_check():
    return {
        "status":  "Healthy",
        "Service": "Oral Cancer RAG API",
        "Version": "1.0.0",
    }


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty."
            )

        if len(request.query) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Query is too long. Please limit to 1000 characters."
            )

        start_time = time.time()

        papers = retrieve(request.query, top_k=request.top_k)
        result = generate_answer(request.query, papers)

        elapsed_time_ms = int((time.time() - start_time) * 1000)

        return QueryResponse(
            query=            result["query"],
            answer=           result["answer"],
            sources=          result["sources"],
            papers_retrieved= len(papers),
            response_time_ms= elapsed_time_ms,
        )

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the query."
        )
