from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        normalized_question = (question or "").strip()
        if not normalized_question:
            return "Please provide a question."

        retrieved = self.store.search(normalized_question, top_k=max(1, top_k))

        if not retrieved:
            prompt = (
                "You are a helpful assistant. "
                "No knowledge-base context was retrieved. "
                f"Question: {normalized_question}\n"
                "Answer briefly and clearly."
            )
            try:
                response = self.llm_fn(prompt)
                return response if isinstance(response, str) and response.strip() else "I don't have enough information to answer that."
            except Exception:
                return "I don't have enough information to answer that."

        context_lines: list[str] = []
        for idx, item in enumerate(retrieved, start=1):
            content = str(item.get("content", "")).strip()
            score = item.get("score", None)
            if score is None:
                context_lines.append(f"[{idx}] {content}")
            else:
                context_lines.append(f"[{idx}] (score={float(score):.4f}) {content}")

        context_block = "\n".join(context_lines)
        prompt = (
            "You are a retrieval-augmented assistant.\n"
            "Use ONLY the context below to answer the question.\n"
            "If the answer is not in context, say you do not know.\n\n"
            f"Context:\n{context_block}\n\n"
            f"Question: {normalized_question}\n"
            "Answer:"
        )

        try:
            response = self.llm_fn(prompt)
        except Exception:
            response = ""

        if isinstance(response, str) and response.strip():
            return response
        return "I don't have enough information to answer that."
