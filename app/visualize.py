import os
import joblib
import numpy as np
from sqlalchemy import text

from db.database import get_db
from utils.logger import get_logger

logger = get_logger(__name__)

MODEL_PATH = os.path.join("embeddings", "models", "umap_model.joblib")

_umap_bundle: dict | None = None


def get_umap_bundle() -> dict:
    global _umap_bundle
    if _umap_bundle is None:
        _umap_bundle = joblib.load(MODEL_PATH)
    return _umap_bundle


def project_query(query_embedding: list[float]) -> list[float]:
    bundle = get_umap_bundle()
    raw = bundle["model"].transform(
        np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
    )[0]
    coords = (raw - bundle["center"]) * bundle["scale"]
    return [round(float(c), 4) for c in coords]


def nearest_rows(query_embedding: list[float], top_k: int = 15) -> list[dict]:
    sql = text("""
        SELECT id, paper_id, title, source,
               1 - (embedding <=> CAST(:query_vector AS vector)) AS similarity
        FROM papers
        ORDER BY embedding <=> CAST(:query_vector AS vector)
        LIMIT :top_k
    """)
    with get_db() as conn:
        rows = conn.execute(sql, {"query_vector": query_embedding, "top_k": top_k}).fetchall()

    return [
        {
            "id":         row.id,
            "paper_id":   row.paper_id,
            "title":      row.title,
            "source":     row.source,
            "similarity": round(float(row.similarity), 4),
        }
        for row in rows
    ]
