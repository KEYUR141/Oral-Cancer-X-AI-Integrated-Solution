"""
embeddings/build_visualization.py

Fits a UMAP projection of every row's 768-dim embedding down to 3D, and
saves two artifacts for the live /visualize page:
  - embeddings/models/umap_model.joblib  (fitted model + center/scale, so a
    future query embedding can be projected into this SAME learned space)
  - embeddings/models/viz_manifest.json  (precomputed points + metadata for
    the frontend's initial render)

Run:
    python -m embeddings.build_visualization
"""

import os
import json
import re
import numpy as np
import joblib
from umap import UMAP
from sqlalchemy import select

from db.database import get_db
from db.models import papers_table
from utils.logger import get_logger

logger = get_logger(__name__)

MODELS_DIR    = os.path.join("embeddings", "models")
MODEL_PATH    = os.path.join(MODELS_DIR, "umap_model.joblib")
MANIFEST_PATH = os.path.join(MODELS_DIR, "viz_manifest.json")

SOURCES = {
    "abstract":        {"label": "Abstract",        "color": "#22c55e"},
    "fulltext":        {"label": "Fulltext chunk",  "color": "#38bdf8"},
    "figure_captions": {"label": "Figure caption",  "color": "#f97316"},
}


def snippet(text_: str | None, length: int = 220) -> str:
    if not text_:
        return ""
    collapsed = re.sub(r"\s+", " ", text_).strip()
    return collapsed[:length]


def fetch_all_rows():
    stmt = select(
        papers_table.c.id,
        papers_table.c.paper_id,
        papers_table.c.title,
        papers_table.c.abstract,
        papers_table.c.source,
        papers_table.c.embedding,
    ).order_by(papers_table.c.id)

    with get_db() as conn:
        return conn.execute(stmt).fetchall()


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    rows = fetch_all_rows()
    logger.info(f"Loaded {len(rows)} rows")

    vectors = np.array([r.embedding for r in rows], dtype=np.float32)

    logger.info("Fitting UMAP(n_components=3, metric='cosine')")
    reducer = UMAP(n_components=3, metric="cosine", random_state=42)
    raw = reducer.fit_transform(vectors)

    center = raw.mean(axis=0)
    radii  = np.linalg.norm(raw - center, axis=1)
    scale  = float(1.2 / np.percentile(radii, 95))

    coords = (raw - center) * scale

    joblib.dump({"model": reducer, "center": center, "scale": scale}, MODEL_PATH)
    logger.info(f"Saved fitted UMAP model to {MODEL_PATH}")

    source_ids = {name: i for i, name in enumerate(SOURCES)}
    points = []
    meta = []

    for row, coord in zip(rows, coords):
        points.append([
            round(float(coord[0]), 4),
            round(float(coord[1]), 4),
            round(float(coord[2]), 4),
            source_ids.get(row.source, 0),
        ])
        meta.append({
            "id":       row.id,
            "paper_id": row.paper_id,
            "title":    row.title,
            "source":   row.source,
            "snippet":  snippet(row.abstract),
        })

    manifest = {
        "sources": {name: {**info, "id": source_ids[name]} for name, info in SOURCES.items()},
        "points":  points,
        "meta":    meta,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False)

    logger.info(f"Saved {len(points)} points to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
