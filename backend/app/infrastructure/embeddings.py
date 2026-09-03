from collections.abc import Sequence
from typing import Any

from app.application.retrieval import RetrievalError
from app.settings import Settings


class SentenceTransformerEmbeddingProvider:
    """Lazy adapter for the configured sentence-transformers model."""

    def __init__(self, settings: Settings) -> None:
        if settings.embedding_provider != "sentence-transformers" or not settings.embedding_model:
            raise RetrievalError("Embedding provider/model is not configured")
        self.model_name = settings.embedding_model
        self._model: Any = None
        self.dimension = 0

    def _load(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RetrievalError("sentence-transformers is not installed") from exc
            self._model = SentenceTransformer(self.model_name)
            self.dimension = int(self._model.get_sentence_embedding_dimension())
        return self._model

    async def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise RetrievalError("Cannot embed empty text")
        return await self.embed_many([text]).__anext__() if False else (await self._embed_many([text]))[0]

    async def _embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._load()
        try:
            vectors = model.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True)
            return [vector.astype(float).tolist() for vector in vectors]
        except Exception as exc:
            raise RetrievalError("Embedding provider failed") from exc

    async def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts or any(not text.strip() for text in texts):
            raise RetrievalError("Cannot embed empty text")
        return await self._embed_many(texts)
