from dataclasses import dataclass
from typing import Any, Protocol, Sequence


class RetrievalError(Exception):
    pass


@dataclass(frozen=True)
class VectorMatch:
    vector_id: str
    score: float
    metadata: dict[str, Any]


class EmbeddingProvider(Protocol):
    dimension: int
    model_name: str

    async def embed(self, text: str) -> list[float]:
        ...

    async def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        ...


class VectorIndex(Protocol):
    async def upsert(self, vectors: Sequence[dict[str, Any]]) -> None:
        ...

    async def query(self, vector: Sequence[float], *, top_k: int, filters: dict[str, Any] | None = None) -> list[VectorMatch]:
        ...

    async def delete(self, vector_ids: Sequence[str]) -> None:
        ...

    async def check(self) -> str:
        ...
