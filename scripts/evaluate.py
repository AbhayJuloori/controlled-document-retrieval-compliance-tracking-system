from __future__ import annotations

from pathlib import Path

from controlled_docs.benchmark import evaluate_benchmark
from controlled_docs.config import AppConfig
from controlled_docs.db import initialize_database, session_scope
from controlled_docs.embeddings import get_embedder
from controlled_docs.logging_utils import configure_logging
from controlled_docs.qa import QAService
from controlled_docs.retrieval import RetrievalService


def main() -> None:
    config = AppConfig.from_env()
    configure_logging(config.log_level)
    session_factory = initialize_database(config)
    embedder = get_embedder(config)
    benchmark_path = Path("data/qa_benchmark.jsonl")
    csv_output_path = Path("artifacts/evaluation_report.csv")
    markdown_output_path = Path("artifacts/evaluation_summary.md")

    with session_scope(session_factory) as session:
        retrieval_service = RetrievalService(session, config, embedder)
        qa_service = QAService(retrieval_service)
        metrics = evaluate_benchmark(
            session,
            qa_service,
            retrieval_service,
            benchmark_path=benchmark_path,
            csv_output_path=csv_output_path,
            markdown_output_path=markdown_output_path,
            top_k=config.retrieval_top_k,
        )
        print(metrics)
        print(f"CSV report: {csv_output_path}")
        print(f"Markdown summary: {markdown_output_path}")


if __name__ == "__main__":
    main()

