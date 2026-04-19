# Controlled Document Retrieval & Compliance Tracking System

A compliance-focused retrieval system for controlled documents with lifecycle awareness, jurisdiction filters, and audit-ready citations.

The project is designed around a practical problem: retrieving the right approved document version for the right user, at the right point in time, without losing traceability. Instead of treating document search as generic semantic search, it enforces document status, role-based access, jurisdiction, document type, and effective-date rules before returning a source-bounded answer.

## What the system does

- Ingests a document register workbook plus a local folder of controlled documents
- Normalizes metadata, versions, checksums, and document status
- Chunks and embeds content for retrieval
- Supports Postgres + `pgvector` in Docker and a SQLite JSON-vector fallback for local runs
- Enforces retrieval controls for `role`, `jurisdiction`, `doc_type`, and `as_of` date
- Defaults to `APPROVED` content only unless an authorized role requests broader access
- Logs ingestion, overrides, status transitions, and query activity to an append-only audit log
- Exposes both a CLI flow and a FastAPI service for citation-first Q&A

## Why this project matters

Many RAG demos show retrieval quality, but not governance. In regulated environments, the hard part is often not finding a relevant paragraph. It is proving that the returned answer came from the correct document version, that draft or obsolete content was excluded, and that the retrieval respected role and jurisdiction constraints. This project is built around that layer of control.

## Repository layout

```text
controlled-document-retrieval-compliance-tracking-system/
├── data/
│   ├── docs/
│   ├── document_register.xlsx
│   ├── generate_synthetic_data.py
│   └── qa_benchmark.jsonl
├── docs/
│   ├── architecture.md
│   └── sample_evaluation.md
├── scripts/
│   ├── ask.py
│   ├── compliance_tracker.py
│   ├── evaluate.py
│   ├── ingest.py
│   └── serve.py
├── src/controlled_docs/
├── tests/
├── .env.example
├── Dockerfile
├── Makefile
├── docker-compose.yml
└── pyproject.toml
```

## Core data model

- `documents`: document metadata, lifecycle status, and current-version pointer
- `document_versions`: effective dates, checksums, supersedence, and source paths
- `chunks`: chunk text, embeddings, and metadata JSON
- `access_policies`: role-based jurisdiction and document-type constraints
- `audit_log`: append-only history for ingestion, retrieval, and override events

`documents.current_version_id` is treated as the canonical current-version reference.

## Quick start

### Local SQLite fallback

```bash
cp .env.example .env
python3 -m venv .venv
. .venv/bin/activate
pip install ".[dev]"
python -m data.generate_synthetic_data
python -m scripts.ingest --register data/document_register.xlsx --docs-dir data/docs
python -m scripts.ask --role Analyst --jurisdiction US-FDA --doc-type SOP --as_of 2026-01-15 --question "Within how many business days must batch records be reviewed after manufacturing completion?"
python -m scripts.evaluate
python -m scripts.compliance_tracker --as_of 2026-01-15 --output artifacts/compliance_dashboard.csv
python -m scripts.serve
```

### Docker with Postgres + `pgvector`

```bash
cp .env.example .env
docker compose up --build
```

API: [http://localhost:8000](http://localhost:8000)

## Example query

```bash
python -m scripts.ask \
  --role Analyst \
  --jurisdiction US-FDA \
  --doc-type SOP \
  --as_of 2026-01-15 \
  --question "Within how many business days must batch records be reviewed after manufacturing completion?"
```

Sample output:

```text
Batch production records shall be reviewed within 1 business day after manufacturing completion. [DOC:cad3fe6d-986b-567b-b9fd-7093cc96ce31 VER:2 CH:87691cbb-33f5-5dc6-8590-36d86b628551]
Citations:
  - [DOC:cad3fe6d-986b-567b-b9fd-7093cc96ce31 VER:2 CH:87691cbb-33f5-5dc6-8590-36d86b628551]
```

## API example

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Analyst",
    "jurisdiction": "US-FDA",
    "doc_type": "SOP",
    "as_of": "2026-01-15",
    "question": "Within how many business days must batch records be reviewed after manufacturing completion?"
  }'
```

## Evaluation and outputs

The synthetic benchmark includes 60 questions across `US-FDA`, `EU-MDR`, and `ISO13485`, spanning `SOP`, `WI`, `POLICY`, `TRAINING`, and `CAPA`.

Run:

```bash
python -m scripts.evaluate
```

Outputs:

- `artifacts/evaluation_report.csv`
- `artifacts/evaluation_summary.md`

You can also generate a compliance dashboard export with:

```bash
python -m scripts.compliance_tracker --as_of 2026-01-15 --output artifacts/compliance_dashboard.csv
```

Flags include:

- `REAPPROVAL_OVERDUE`
- `DRAFT_IN_CONTROLLED_SET`
- `OBSOLETE_ACTIVE_REFERENCE`
- `NO_EFFECTIVE_VERSION`

## Environment variables

- `DATABASE_URL`: SQLite by default, or Postgres for `pgvector`
- `EMBEDDING_BACKEND`: `local` or `openai`
- `OPENAI_API_KEY`: required only for OpenAI embeddings
- `OPENAI_EMBEDDING_MODEL`: default `text-embedding-3-small`
- `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RETRIEVAL_TOP_K`, `REVIEW_WINDOW_DAYS`

## Security notes

- The repository uses synthetic data only
- `.env` files and API keys should not be committed
- Audit logs intentionally capture filters and object IDs, so prompts should not contain secrets
- OpenAI embeddings are optional and disabled by default

## Notes

- The retrieval flow is citation-first and source-bounded
- The local fallback uses a hashing vectorizer so the system works without paid API keys
- The synthetic corpus intentionally includes conflicting jurisdictions, version drift, draft content, and obsolete references to exercise the control layer
