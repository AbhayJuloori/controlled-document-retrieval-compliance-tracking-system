from __future__ import annotations

import argparse

from controlled_docs.config import AppConfig
from controlled_docs.db import initialize_database, session_scope
from controlled_docs.embeddings import get_embedder
from controlled_docs.logging_utils import configure_logging
from controlled_docs.qa import AskQuery, QAService
from controlled_docs.retrieval import RetrievalService
from controlled_docs.utils import parse_date


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a controlled-document question")
    parser.add_argument("--role", required=True)
    parser.add_argument("--jurisdiction", required=True)
    parser.add_argument("--doc-type", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--include-nonapproved", action="store_true")
    args = parser.parse_args()

    config = AppConfig.from_env()
    configure_logging(config.log_level)
    session_factory = initialize_database(config)
    embedder = get_embedder(config)

    with session_scope(session_factory) as session:
        qa_service = QAService(RetrievalService(session, config, embedder))
        result = qa_service.ask(
            AskQuery(
                role=args.role,
                jurisdiction=args.jurisdiction,
                doc_type=args.doc_type,
                as_of_date=parse_date(args.as_of),
                question=args.question,
                top_k=args.top_k,
                include_nonapproved=args.include_nonapproved,
            )
        )
        print(result["answer"])
        if result["citations"]:
            print("Citations:")
            for citation in result["citations"]:
                print(f"  - {citation}")


if __name__ == "__main__":
    main()

