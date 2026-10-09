from typing import Any

import numpy as np
from llama_index.core.embeddings import BaseEmbedding
from pydantic import Field, PrivateAttr


class ProfileHuggingFaceEmbedding(BaseEmbedding):
    model_name: str = Field(default="AITeamVN/Vietnamese_Embedding")
    _model: Any = PrivateAttr(default=None)

    def __init__(self, model_name: str = "AITeamVN/Vietnamese_Embedding", **kwargs: Any) -> None:
        super().__init__(model_name=model_name, **kwargs)
        self._model = None

    def _load(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _embed(self, texts: list[str]) -> list[list[float]]:
        vectors = np.asarray(self._load().encode(texts, normalize_embeddings=False), dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        normalized = vectors / np.clip(norms, 1e-12, None)
        return normalized.tolist()

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._embed([query])[0]

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._embed([text])[0]

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)
