from collections.abc import Sequence
import math
from typing import Any

from app.application.retrieval import RetrievalError, VectorMatch
from app.settings import Settings


class InMemoryVectorIndex:
    """In-memory cosine similarity vector index fallback."""

    def __init__(self) -> None:
        self._vectors: dict[str, dict[str, Any]] = {}

    async def upsert(self, vectors: Sequence[dict[str, Any]]) -> None:
        for vector_item in vectors:
            vector_id = str(vector_item["id"])
            values = [float(v) for v in vector_item["values"]]
            metadata = dict(vector_item.get("metadata", {}))
            self._vectors[vector_id] = {
                "id": vector_id,
                "values": values,
                "metadata": metadata,
            }

    async def query(self, vector: Sequence[float], *, top_k: int = 10, filters: dict[str, Any] | None = None) -> list[VectorMatch]:
        if not self._vectors:
            return []
        query_vec = [float(v) for v in vector]
        norm_q = math.sqrt(sum(x * x for x in query_vec)) or 1.0

        matches: list[VectorMatch] = []
        for vid, item in self._vectors.items():
            meta = item["metadata"]
            if filters:
                match_filters = True
                for fk, fval in filters.items():
                    if meta.get(fk) != fval:
                        match_filters = False
                        break
                if not match_filters:
                    continue

            vec = item["values"]
            norm_v = math.sqrt(sum(x * x for x in vec)) or 1.0
            dot = sum(a * b for a, b in zip(query_vec, vec))
            score = dot / (norm_q * norm_v)
            matches.append(VectorMatch(vector_id=vid, score=score, metadata=meta))

        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:top_k]

    async def delete(self, vector_ids: Sequence[str]) -> None:
        for vid in vector_ids:
            self._vectors.pop(vid, None)

    async def check(self) -> str:
        return "healthy"


class PineconeVectorIndex:
    """Pinecone vector index integration adhering to VectorIndex protocol."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._fallback = InMemoryVectorIndex()
        self._pc: Any = None
        self._index: Any = None

    def _get_index(self) -> Any:
        if not self._settings.pinecone_configured():
            return None
        if self._index is None:
            try:
                from pinecone import Pinecone
                api_key = self._settings.pinecone_api_key.get_secret_value()  # type: ignore
                index_name = self._settings.pinecone_index_name
                self._pc = Pinecone(api_key=api_key)
                self._index = self._pc.Index(index_name)
            except Exception:
                return None
        return self._index

    async def upsert(self, vectors: Sequence[dict[str, Any]]) -> None:
        await self._fallback.upsert(vectors)
        index = self._get_index()
        if index is not None:
            try:
                pinecone_vectors = [
                    {
                        "id": str(v["id"]),
                        "values": [float(x) for x in v["values"]],
                        "metadata": v.get("metadata", {}),
                    }
                    for v in vectors
                ]
                index.upsert(vectors=pinecone_vectors)
            except Exception as exc:
                raise RetrievalError("Pinecone vector upsert failed") from exc

    async def query(self, vector: Sequence[float], *, top_k: int = 10, filters: dict[str, Any] | None = None) -> list[VectorMatch]:
        index = self._get_index()
        if index is not None:
            try:
                query_res = index.query(
                    vector=[float(v) for v in vector],
                    top_k=top_k,
                    include_metadata=True,
                    filter=filters,
                )
                results: list[VectorMatch] = []
                for match in query_res.get("matches", []):
                    results.append(
                        VectorMatch(
                            vector_id=str(match["id"]),
                            score=float(match["score"]),
                            metadata=dict(match.get("metadata", {})),
                        )
                    )
                if results:
                    return results
            except Exception:
                pass
        return await self._fallback.query(vector, top_k=top_k, filters=filters)

    async def delete(self, vector_ids: Sequence[str]) -> None:
        await self._fallback.delete(vector_ids)
        index = self._get_index()
        if index is not None:
            try:
                index.delete(ids=list(vector_ids))
            except Exception as exc:
                raise RetrievalError("Pinecone vector delete failed") from exc

    async def check(self) -> str:
        if not self._settings.pinecone_configured():
            return "not_configured"
        index = self._get_index()
        return "healthy" if index is not None else "configured"
