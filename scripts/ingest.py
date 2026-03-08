from __future__ import annotations

import argparse
from pathlib import Path

from controlled_docs.config import AppConfig
from controlled_docs.db import initialize_database, session_scope
from controlled_docs.embeddings import get_embedder
from controlled_docs.ingestion import IngestionService
from controlled_docs.logging_utils import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest controlled documents")
    parser.add_argument("--register", type=Path, default=Path("data/document_register.xlsx"))
    parser.add_argument("--docs-dir", type=Path, default=Path("data/docs"))
    parser.add_argument("--actor", default="system")
    args = parser.parse_args()

    config = AppConfig.from_env()
    configure_logging(config.log_level)
    session_factory = initialize_database(config)
    embedder = get_embedder(config)

    with session_scope(session_factory) as session:
        service = IngestionService(session, config, embedder)
        register_summary = service.ingest_register(args.register, actor=args.actor)
        folder_summary = service.ingest_folder(args.docs_dir, actor=args.actor)
        print(
            {
                "register": register_summary.__dict__,
                "folder": folder_summary.__dict__,
            }
        )


if __name__ == "__main__":
    main()

