from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from openai import OpenAI
from sklearn.feature_extraction.text import HashingVectorizer

from controlled_docs.config import AppConfig


class Embedder(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


@dataclass(slots=True)
class LocalHashingEmbedder:
    n_features: int = 256

    def __post_init__(self) -> None:
        self._vectorizer = HashingVectorizer(
            n_features=self.n_features,
            alternate_sign=False,
            norm="l2",
            ngram_range=(1, 2),
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        matrix = self._vectorizer.transform(texts)
        dense = matrix.toarray().astype(float)
        return dense.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


@dataclass(slots=True)
class OpenAIEmbedder:
    api_key: str
    model: str

    def __post_init__(self) -> None:
        self._client = OpenAI(api_key=self.api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


def get_embedder(config: AppConfig) -> Embedder:
    if config.embedding_backend.lower() == "openai":
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_BACKEND=openai")
        return OpenAIEmbedder(api_key=config.openai_api_key, model=config.openai_embedding_model)
    return LocalHashingEmbedder()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    left_array = np.array(left, dtype=float)
    right_array = np.array(right, dtype=float)
    denominator = float(np.linalg.norm(left_array) * np.linalg.norm(right_array))
    if denominator == 0:
        return 0.0
    return float(np.dot(left_array, right_array) / denominator)

