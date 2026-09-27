"""Chroma vector-ID adapter; exact texts always hydrate from an authority store."""
from typing import Any

from .adapters import VectorStore


def chroma_store(collection: Any, authority: Any, embed_query: Any) -> VectorStore:
    def vector_query(text: str, limit: int):
        result = collection.query(query_embeddings=[embed_query(text)], n_results=limit)
        return result.get("ids", [[]])[0]
    return VectorStore(vector_query, authority)
