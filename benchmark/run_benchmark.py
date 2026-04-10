from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.chunking import DocumentStructureChunker, FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import create_embedder
from src.models import Document
from src.store import EmbeddingStore


RAW_DATA_DIR = BASE_DIR / "data" / "raw_data"
QUERIES_FILE = BASE_DIR / "benchmark" / "queries_gold.json"
RESULT_JSON = BASE_DIR / "benchmark" / "results" / "benchmark_results.json"
RESULT_MD = BASE_DIR / "benchmark" / "results" / "benchmark_results.md"
EMBEDDER = create_embedder()


@dataclass
class Strategy:
    name: str
    chunker: Any
    use_metadata_filter: bool


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> set[str]:
    return {tok for tok in re.findall(r"\w+", normalize(text), flags=re.UNICODE) if tok}


def keyword_hit_ratio(text: str, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 0.0
    norm = normalize(text)
    hits = sum(1 for kw in expected_keywords if normalize(kw) in norm)
    return hits / len(expected_keywords)


def token_overlap_f1(prediction_text: str, gold_text: str) -> float:
    pred = tokenize(prediction_text)
    gold = tokenize(gold_text)
    if not pred or not gold:
        return 0.0
    inter = len(pred & gold)
    if inter == 0:
        return 0.0
    precision = inter / len(pred)
    recall = inter / len(gold)
    return 2 * precision * recall / (precision + recall)


def load_queries(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_chunk_docs(chunker: Any) -> list[Document]:
    docs: list[Document] = []
    files = sorted(RAW_DATA_DIR.glob("*.md"))

    for file_path in files:
        artist = file_path.stem
        raw_text = file_path.read_text(encoding="utf-8")
        chunks = chunker.chunk(raw_text)

        for idx, chunk in enumerate(chunks):
            metadata = {
                "artist": artist,
                "source": str(file_path.relative_to(BASE_DIR)),
                "chunk_index": idx,
                "chunker": chunker.__class__.__name__,
            }
            if chunk.startswith("Section:"):
                first_line = chunk.splitlines()[0]
                metadata["section"] = first_line.replace("Section:", "").strip()

            docs.append(
                Document(
                    id=f"{artist}_{idx}",
                    content=chunk,
                    metadata=metadata,
                )
            )

    return docs


def evaluate_strategy(strategy: Strategy, queries: list[dict[str, Any]], top_k: int = 3) -> dict[str, Any]:
    store = EmbeddingStore(collection_name=f"benchmark_{strategy.name}", embedding_fn=EMBEDDER)
    store.add_documents(build_chunk_docs(strategy.chunker))

    per_query: list[dict[str, Any]] = []
    score_sum = 0.0

    for q in queries:
        metadata_filter = q.get("metadata_filter") if strategy.use_metadata_filter else None
        if metadata_filter:
            results = store.search_with_filter(q["question"], top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = store.search(q["question"], top_k=top_k)

        combined_context = "\n".join(item["content"] for item in results)
        top1_text = results[0]["content"] if results else ""

        keyword_score = keyword_hit_ratio(combined_context, q.get("expected_keywords", []))
        overlap_score = token_overlap_f1(top1_text, q["gold_answer"])
        final_score = 0.7 * keyword_score + 0.3 * overlap_score
        score_sum += final_score

        per_query.append(
            {
                "id": q["id"],
                "question": q["question"],
                "gold_answer": q["gold_answer"],
                "keyword_score": round(keyword_score, 4),
                "overlap_score": round(overlap_score, 4),
                "final_score": round(final_score, 4),
                "top_results": [
                    {
                        "score": round(float(r["score"]), 4),
                        "artist": (r.get("metadata") or {}).get("artist"),
                        "source": (r.get("metadata") or {}).get("source"),
                        "preview": r["content"][:180].replace("\n", " "),
                    }
                    for r in results
                ],
            }
        )

    avg_score = score_sum / len(queries) if queries else 0.0
    return {
        "strategy": strategy.name,
        "chunker": strategy.chunker.__class__.__name__,
        "use_metadata_filter": strategy.use_metadata_filter,
        "num_chunks": store.get_collection_size(),
        "avg_score": round(avg_score, 4),
        "queries": per_query,
    }


def to_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Benchmark Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Strategy | Chunker | Metadata Filter | Chunks | Avg Score |")
    lines.append("|---|---|---:|---:|---:|")

    for item in report["strategies"]:
        lines.append(
            f"| {item['strategy']} | {item['chunker']} | {str(item['use_metadata_filter'])} | {item['num_chunks']} | {item['avg_score']:.4f} |"
        )

    lines.append("")
    lines.append("## Query Details")
    lines.append("")

    for item in report["strategies"]:
        lines.append(f"### {item['strategy']}")
        lines.append("")
        lines.append("| Query ID | Keyword | Overlap | Final | Top-1 Artist | Top-1 Preview |")
        lines.append("|---|---:|---:|---:|---|---|")

        for q in item["queries"]:
            top1 = q["top_results"][0] if q["top_results"] else {}
            preview = str(top1.get("preview", "")).replace("|", " ")
            lines.append(
                f"| {q['id']} | {q['keyword_score']:.4f} | {q['overlap_score']:.4f} | {q['final_score']:.4f} | {top1.get('artist', '')} | {preview} |"
            )

        lines.append("")

    return "\n".join(lines)


def main() -> int:
    queries = load_queries(QUERIES_FILE)

    strategies = [
        Strategy(
            name="fixed_baseline",
            chunker=FixedSizeChunker(chunk_size=450, overlap=80),
            use_metadata_filter=False,
        ),
        Strategy(
            name="sentence_basic",
            chunker=SentenceChunker(max_sentences_per_chunk=3),
            use_metadata_filter=False,
        ),
        Strategy(
            name="recursive_with_filter",
            chunker=RecursiveChunker(chunk_size=450),
            use_metadata_filter=True,
        ),
        Strategy(
            name="markdown_structure_with_filter",
            chunker=DocumentStructureChunker(chunk_size=450),
            use_metadata_filter=True,
        ),
    ]

    results = [evaluate_strategy(strategy=s, queries=queries, top_k=3) for s in strategies]
    results.sort(key=lambda item: item["avg_score"], reverse=True)

    report = {
        "queries_file": str(QUERIES_FILE.relative_to(BASE_DIR)),
        "data_dir": str(RAW_DATA_DIR.relative_to(BASE_DIR)),
        "strategies": results,
    }

    RESULT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    RESULT_MD.write_text(to_markdown(report), encoding="utf-8")

    print("Benchmark completed.")
    print(f"- JSON: {RESULT_JSON}")
    print(f"- Markdown: {RESULT_MD}")
    print("\nRanking by avg_score:")
    for idx, item in enumerate(results, start=1):
        print(f"{idx}. {item['strategy']} -> {item['avg_score']:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
