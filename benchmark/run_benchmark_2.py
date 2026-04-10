from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.chunking import DocumentStructureChunker, FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import create_embedder
from src.models import Document
from src.store import EmbeddingStore

BENCHMARK_FILE = BASE_DIR / "benchmark" / "benchmark.json"
RAW_DATA_DIR = BASE_DIR / "data" / "raw_data"
RESULT_FILE = BASE_DIR / "benchmark" / "results" / "benchmark_2_results.json"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def tokenize(text: str) -> set[str]:
    return {tok for tok in re.findall(r"\w+", normalize(text), flags=re.UNICODE) if tok}


def overlap_f1(pred: str, gold: str) -> float:
    pred_tokens = tokenize(pred)
    gold_tokens = tokenize(gold)
    if not pred_tokens or not gold_tokens:
        return 0.0

    inter = len(pred_tokens & gold_tokens)
    if inter == 0:
        return 0.0

    precision = inter / len(pred_tokens)
    recall = inter / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def load_queries(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_chunker(chunker_name: str):
    if chunker_name == "sentence":
        return SentenceChunker(max_sentences_per_chunk=3)
    if chunker_name == "recursive":
        return RecursiveChunker(chunk_size=150)
    if chunker_name == "fixed":
        return FixedSizeChunker(chunk_size=150, overlap=30)
    return DocumentStructureChunker(chunk_size=150)


def build_store_docs(chunker_name: str) -> list[Document]:
    chunker = build_chunker(chunker_name)

    docs: list[Document] = []
    for file_path in sorted(RAW_DATA_DIR.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        artist = file_path.stem
        for idx, chunk in enumerate(chunker.chunk(text)):
            docs.append(
                Document(
                    id=f"{artist}_{idx}",
                    content=chunk,
                    metadata={
                        "artist": artist,
                        "source": str(file_path.relative_to(BASE_DIR)),
                        "chunk_index": idx,
                    },
                )
            )
    return docs


def get_embedder(use_mock: bool = False):
    if use_mock:
        return create_embedder("mock")
    return create_embedder("local")


def answer_from_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return "Khong tim thay thong tin phu hop trong kho du lieu."

    # Return only one concise answer text from top retrieval result.
    text = str(results[0].get("content", "")).strip()
    return re.sub(r"\s+", " ", text)


def run_for_chunker(chunker: str, top_k: int, use_mock: bool) -> dict[str, Any]:
    queries = load_queries(BENCHMARK_FILE)

    embedder = get_embedder(use_mock=use_mock)
    store = EmbeddingStore(collection_name=f"benchmark2_{chunker}", embedding_fn=embedder)
    store.add_documents(build_store_docs(chunker_name=chunker))

    rows: list[dict[str, Any]] = []
    score_sum = 0.0

    for item in queries:
        question = item["question"]
        gold = item["answer"]

        results = store.search(question, top_k=max(3, top_k))
        predicted = answer_from_results(results)
        f1 = overlap_f1(predicted, gold)
        score_sum += f1

        top_chunks = []
        for result in results[:3]:
            metadata = result.get("metadata") or {}
            top_chunks.append(
                {
                    "score": round(float(result.get("score", 0.0)), 4),
                    "artist": metadata.get("artist"),
                    "source": metadata.get("source"),
                    "content": str(result.get("content", "")).strip(),
                }
            )

        rows.append(
            {
                "id": item["id"],
                "question": question,
                "predicted_answer": predicted,
                "benchmark_answer": gold,
                "overlap_f1": round(f1, 4),
                "top_3_chunks": top_chunks,
            }
        )

    avg_f1 = score_sum / len(rows) if rows else 0.0

    report = {
        "chunker": chunker,
        "top_k": max(3, top_k),
        "embedder": getattr(embedder, "_backend_name", embedder.__class__.__name__),
        "avg_overlap_f1": round(avg_f1, 4),
        "results": rows,
    }
    return report


def run(chunkers: list[str], top_k: int, use_mock: bool) -> dict[str, Any]:
    method_reports = [run_for_chunker(chunker=name, top_k=top_k, use_mock=use_mock) for name in chunkers]
    method_reports.sort(key=lambda item: item["avg_overlap_f1"], reverse=True)

    return {
        "benchmark_file": str(BENCHMARK_FILE.relative_to(BASE_DIR)),
        "top_k": max(3, top_k),
        "methods": method_reports,
    }


def persist_report(report: dict[str, Any]) -> None:
    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def print_report(report: dict[str, Any]) -> None:
    print("Done. Top 3 chunk cao nhat cho tung phuong phap chunk:")
    print(f"- benchmark_file: {report['benchmark_file']}")
    print(f"- top_k (thuc thi): {report['top_k']}")
    print(f"- output: {RESULT_FILE}")
    print("")

    for method in report["methods"]:
        print(f"=== Method: {method['chunker']} | avg_overlap_f1={method['avg_overlap_f1']:.4f} ===")
        for row in method["results"]:
            print(f"Q{row['id']}: {row['question']}")
            print(f"Tra loi: {row['predicted_answer']}")
            print(f"Benchmark: {row['benchmark_answer']}")
            print(f"Overlap F1: {row['overlap_f1']:.4f}")
            for i, chunk in enumerate(row["top_3_chunks"], start=1):
                print(
                    f"  Top {i} | score={chunk['score']:.4f} | artist={chunk.get('artist')} | source={chunk.get('source')}"
                )
                print(f"  Chunk: {chunk['content'][:220]}")
            print("")


def main() -> int:
    load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

    parser = argparse.ArgumentParser(description="Run benchmark from benchmark/benchmark.json")
    parser.add_argument(
        "--chunker",
        choices=["all", "structure", "sentence", "recursive", "fixed"],
        default="all",
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--mock", action="store_true", help="Use MockEmbedder instead of LocalEmbedder")
    args = parser.parse_args()

    chunkers = ["structure", "sentence", "recursive", "fixed"] if args.chunker == "all" else [args.chunker]
    report = run(chunkers=chunkers, top_k=args.top_k, use_mock=args.mock)
    persist_report(report)
    print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
