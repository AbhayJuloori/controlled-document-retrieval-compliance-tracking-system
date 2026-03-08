from __future__ import annotations

import argparse
from pathlib import Path

from controlled_docs.compliance import build_compliance_dashboard
from controlled_docs.config import AppConfig
from controlled_docs.db import initialize_database, session_scope
from controlled_docs.logging_utils import configure_logging
from controlled_docs.utils import parse_date


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate compliance dashboard CSV")
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/compliance_dashboard.csv"))
    args = parser.parse_args()

    config = AppConfig.from_env()
    configure_logging(config.log_level)
    session_factory = initialize_database(config)

    with session_scope(session_factory) as session:
        rows = build_compliance_dashboard(
            session, config, as_of_date=parse_date(args.as_of), output_path=args.output
        )
        print({"rows": len(rows), "output": str(args.output)})


if __name__ == "__main__":
    main()

