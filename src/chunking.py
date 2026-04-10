from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        normalized = text.strip()
        if not normalized:
            return []

        # Keep punctuation attached to each sentence while splitting on whitespace after . ! ?
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalized) if s.strip()]
        if not sentences:
            return [normalized]

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunks.append(" ".join(sentences[i : i + self.max_sentences_per_chunk]).strip())
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        if not self.separators:
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        chunks = self._split(text, self.separators)
        return [c for c in chunks if c]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text.strip()]

        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size].strip()
                for i in range(0, len(current_text), self.chunk_size)
                if current_text[i : i + self.chunk_size].strip()
            ]

        sep = remaining_separators[0]
        next_separators = remaining_separators[1:]

        if sep == "":
            return [
                current_text[i : i + self.chunk_size].strip()
                for i in range(0, len(current_text), self.chunk_size)
                if current_text[i : i + self.chunk_size].strip()
            ]

        if sep not in current_text:
            return self._split(current_text, next_separators)

        parts = current_text.split(sep)
        tentative: list[str] = []
        buffer = ""
        for part in parts:
            candidate = part if not buffer else f"{buffer}{sep}{part}"
            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    tentative.append(buffer)
                if len(part) <= self.chunk_size:
                    buffer = part
                else:
                    tentative.extend(self._split(part, next_separators))
                    buffer = ""
        if buffer:
            tentative.append(buffer)

        final_chunks: list[str] = []
        for chunk in tentative:
            chunk = chunk.strip()
            if not chunk:
                continue
            if len(chunk) <= self.chunk_size:
                final_chunks.append(chunk)
            else:
                final_chunks.extend(self._split(chunk, next_separators))
        return final_chunks


class DocumentStructureChunker:
    """
    Chunk markdown text by document structure (headings).

    Behavior:
        - Detect markdown headings (#, ##, ..., ######).
        - Group body content under each heading section.
        - Prefix each chunk with heading breadcrumb for context retention.
        - If a section is too large, split it further using RecursiveChunker.
    """

    HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self._fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        lines = text.splitlines()
        sections: list[tuple[str, str]] = []
        heading_stack: list[tuple[int, str]] = []
        buffer: list[str] = []

        def flush_current() -> None:
            body = "\n".join(buffer).strip()
            if not body:
                return
            if heading_stack:
                path = " > ".join(title for _, title in heading_stack)
            else:
                path = "Document"
            sections.append((path, body))

        for line in lines:
            match = self.HEADING_RE.match(line)
            if not match:
                buffer.append(line)
                continue

            flush_current()
            buffer = []

            level = len(match.group(1))
            title = match.group(2).strip()
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))

        flush_current()

        # No headings found: fallback to recursive chunking for raw markdown/text.
        if not sections:
            return self._fallback.chunk(text)

        chunks: list[str] = []
        for path, body in sections:
            prefix = f"Section: {path}\n\n"
            if len(prefix) + len(body) <= self.chunk_size:
                chunks.append(prefix + body)
                continue

            for sub in self._fallback.chunk(body):
                candidate = (prefix + sub).strip()
                if len(candidate) <= self.chunk_size:
                    chunks.append(candidate)
                else:
                    # Safety net when prefix itself makes candidate exceed chunk_size.
                    chunks.extend(self._fallback.chunk(candidate))

        return [c for c in chunks if c.strip()]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0

    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_chunks = FixedSizeChunker(chunk_size=chunk_size, overlap=max(0, min(50, chunk_size // 5))).chunk(text)
        sentence_chunks = SentenceChunker(max_sentences_per_chunk=max(1, chunk_size // 100)).chunk(text)
        recursive_chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)
        structure_chunks = DocumentStructureChunker(chunk_size=chunk_size).chunk(text)

        def _stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count else 0.0
            return {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return {
            "fixed_size": _stats(fixed_chunks),
            "by_sentences": _stats(sentence_chunks),
            "recursive": _stats(recursive_chunks),
            "document_structure": _stats(structure_chunks),
        }
