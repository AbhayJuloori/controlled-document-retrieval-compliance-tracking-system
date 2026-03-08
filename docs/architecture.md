# Architecture Notes

## Overview

The system is organized around a production-ish Python package in `src/controlled_docs` with SQLAlchemy models, ingestion services, retrieval services, QA orchestration, compliance reporting, and a FastAPI surface. The default runtime uses SQLite and JSON-backed vectors so the repository runs on a laptop without external services. `docker-compose.yml` provisions Postgres with `pgvector` and switches the application to a vector-native database path.

## Data Flow

1. `python -m data.generate_synthetic_data` creates synthetic controlled documents, an Excel document register, and a QA benchmark.
2. `python -m scripts.ingest` loads both the register and the docs folder, normalizes metadata, computes checksums, chunks content, embeds chunks, persists rows, and appends audit events.
3. `python -m scripts.ask` or `POST /ask` applies role-aware metadata filtering, version selection by `as_of_date`, hybrid retrieval, and a source-bounded answering chain.
4. `python -m scripts.evaluate` replays the benchmark and outputs retrieval/citation metrics plus a grounding heuristic report.
5. `python -m scripts.compliance_tracker` emits a CSV dashboard for re-approval windows and stale controlled content.

## Control Points

- `documents.current_version_id` is the single pointer for the current version.
- Status transitions and query overrides are appended to `audit_log`.
- Retrieval defaults to `APPROVED` only and requires `Auditor` role to include `DRAFT` or `OBSOLETE`.
- Answers are deterministic and built only from retrieved snippets, with required citations in `[DOC:... VER:... CH:...]` form.

