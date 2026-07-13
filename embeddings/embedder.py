from sentence_transformers import SentenceTransformer

MODEL_NAME = "pritamdeka/S-PubMedBert-MS-MARCO"

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str], batch_size: int = 16, show_progress_bar: bool = False) -> list[list[float]]:
    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=show_progress_bar,
    )
    return embeddings.tolist()
