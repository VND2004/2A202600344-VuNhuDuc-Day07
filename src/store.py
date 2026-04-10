from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # type: ignore[import-not-found]

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)
        embedding = self._embed_document(doc.content)
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding,
        }

    def _embed_document(self, text: str) -> list[float]:
        embed_document = getattr(self._embedding_fn, "embed_document", None)
        if callable(embed_document):
            return embed_document(text)
        return self._embedding_fn(text)

    def _embed_query(self, text: str) -> list[float]:
        embed_query = getattr(self._embedding_fn, "embed_query", None)
        if callable(embed_query):
            return embed_query(text)
        return self._embedding_fn(text)

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        query_vector = self._embed_query(query)
        scored = []
        for record in records:
            score = float(_dot(query_vector, record["embedding"]))
            scored.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": dict(record.get("metadata") or {}),
                    "score": score,
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]

        if self._use_chroma and self._collection is not None:
            chroma_ids = [f"{record['id']}::{self._next_index + i}" for i, record in enumerate(records)]
            self._next_index += len(records)
            self._collection.add(
                ids=chroma_ids,
                documents=[record["content"] for record in records],
                embeddings=[record["embedding"] for record in records],
                metadatas=[record["metadata"] for record in records],
            )
            return

        self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if top_k <= 0:
            return []

        if self._use_chroma and self._collection is not None:
            query_vector = self._embed_query(query)
            result = self._collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            docs = (result.get("documents") or [[]])[0]
            metadatas = (result.get("metadatas") or [[]])[0]
            distances = (result.get("distances") or [[]])[0]
            ids = (result.get("ids") or [[]])[0]

            output: list[dict[str, Any]] = []
            for idx, content in enumerate(docs):
                distance = float(distances[idx]) if idx < len(distances) else 0.0
                output.append(
                    {
                        "id": ids[idx] if idx < len(ids) else None,
                        "content": content,
                        "metadata": metadatas[idx] if idx < len(metadatas) and metadatas[idx] is not None else {},
                        "score": 1.0 - distance,
                    }
                )
            output.sort(key=lambda item: item["score"], reverse=True)
            return output

        return self._search_records(query=query, records=self._store, top_k=top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return int(self._collection.count())
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if top_k <= 0:
            return []

        if self._use_chroma and self._collection is not None:
            query_vector = self._embed_query(query)
            query_args: dict[str, Any] = {
                "query_embeddings": [query_vector],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            }
            if metadata_filter:
                query_args["where"] = metadata_filter

            result = self._collection.query(**query_args)
            docs = (result.get("documents") or [[]])[0]
            metadatas = (result.get("metadatas") or [[]])[0]
            distances = (result.get("distances") or [[]])[0]
            ids = (result.get("ids") or [[]])[0]

            output: list[dict[str, Any]] = []
            for idx, content in enumerate(docs):
                distance = float(distances[idx]) if idx < len(distances) else 0.0
                output.append(
                    {
                        "id": ids[idx] if idx < len(ids) else None,
                        "content": content,
                        "metadata": metadatas[idx] if idx < len(metadatas) and metadatas[idx] is not None else {},
                        "score": 1.0 - distance,
                    }
                )
            output.sort(key=lambda item: item["score"], reverse=True)
            return output

        if not metadata_filter:
            return self._search_records(query=query, records=self._store, top_k=top_k)

        filtered = []
        for record in self._store:
            metadata = record.get("metadata") or {}
            matched = all(metadata.get(key) == value for key, value in metadata_filter.items())
            if matched:
                filtered.append(record)

        return self._search_records(query=query, records=filtered, top_k=top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            try:
                found = self._collection.get(where={"doc_id": doc_id}, include=[])
                ids = found.get("ids") or []
                if ids:
                    self._collection.delete(ids=ids)
                    return True
                return False
            except Exception:
                return False

        original_size = len(self._store)
        self._store = [r for r in self._store if (r.get("metadata") or {}).get("doc_id") != doc_id]
        return len(self._store) < original_size
