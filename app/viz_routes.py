import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.retrieval import embed_query
from app.visualize import project_query, nearest_rows
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

VIZ_HTML_PATH      = os.path.join("static", "visualize.html")
VIZ_MANIFEST_PATH  = os.path.join("embeddings", "models", "viz_manifest.json")


class VizQueryRequest(BaseModel):
    query: str
    top_k: int = 15


class VizMatchSchema(BaseModel):
    id: int
    paper_id: str
    title: str
    source: str
    similarity: float


class VizQueryResponse(BaseModel):
    query: str
    query_point: list[float]
    matches: list[VizMatchSchema]


@router.get("/visualize")
def visualize_page():
    if not os.path.exists(VIZ_HTML_PATH):
        raise HTTPException(status_code=404, detail="Visualization page not found.")
    return FileResponse(VIZ_HTML_PATH, media_type="text/html")


@router.get("/visualize/manifest")
def visualize_manifest():
    if not os.path.exists(VIZ_MANIFEST_PATH):
        raise HTTPException(
            status_code=503,
            detail="Visualization manifest not built yet. Run: python -m embeddings.build_visualization"
        )
    return FileResponse(VIZ_MANIFEST_PATH, media_type="application/json")


@router.post("/visualize/query", response_model=VizQueryResponse)
def visualize_query(request: VizQueryRequest):
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty.")
        if len(request.query) > 1000:
            raise HTTPException(status_code=400, detail="Query is too long. Please limit to 1000 characters.")

        query_embedding = embed_query(request.query)

        return VizQueryResponse(
            query=request.query,
            query_point=project_query(query_embedding),
            matches=nearest_rows(query_embedding, top_k=request.top_k),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing visualize query: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the visualization query.")
