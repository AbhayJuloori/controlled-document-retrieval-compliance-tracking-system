# Controlled Document Retrieval & Compliance Tracking System

Python + SQL system for ingesting synthetic controlled compliance documents, enforcing jurisdiction and document-type filters, tracking versions and status, supporting hybrid retrieval, and returning audit-ready answers with citations.

## What It Does

- Ingests from a document register workbook (`.xlsx`) and a local folder of `.txt` / `.md` files.
- Normalizes metadata, computes checksums, chunks content, embeds chunks, and stores them in SQL.
- Supports Postgres + `pgvector` in Docker and a SQLite JSON-vector fallback for local laptop runs.
- Enforces retrieval controls for `role`, `jurisdiction`, `doc_type`, and `as_of` date.
- Defaults to `APPROVED` documents only and requires `Auditor` role to include `DRAFT` / `OBSOLETE`.
- Logs ingestion, status transitions, query execution, and override behavior to an append-only `audit_log`.
- Provides a CLI and FastAPI surface for source-bounded Q&A with required citations.
- Ships a synthetic QA benchmark and compliance dashboard export.

## Repository Layout

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
│   ├── audit.py
│   ├── benchmark.py
│   ├── chunking.py
│   ├── compliance.py
│   ├── config.py
│   ├── db.py
│   ├── embeddings.py
│   ├── ingestion.py
│   ├── models.py
│   ├── qa.py
│   ├── retrieval.py
│   ├── schemas.py
│   └── server.py
├── tests/
├── .env.example
├── Dockerfile
├── Makefile
├── docker-compose.yml
└── pyproject.toml
```

## Data Model

- `documents`: document metadata, lifecycle status, and current version pointer.
- `document_versions`: effective dates, checksum, supersedence, source path.
- `chunks`: chunk text, embeddings, and metadata JSON.
- `access_policies`: simple role-based jurisdiction / doc-type allow lists.
- `audit_log`: append-only event history for ingestion, queries, and overrides.

`documents.current_version_id` is the single authoritative current-version reference. Status transitions are logged through the ingestion service.

## Quick Start

### Local SQLite fallback

```bash
cp .env.example .env
python3 -m venv .venv
. .venv/bin/activate
pip install ".[dev]"
python -m data.generate_synthetic_data
python -m scripts.ingest --register data/document_register.xlsx --docs-dir data/docs
python -m scripts.ask --role Analyst --jurisdiction US-FDA --doc-type SOP --as-of 2026-01-15 --question "Within how many business days must batch records be reviewed after manufacturing completion?"
python -m scripts.evaluate
python -m scripts.compliance_tracker --as-of 2026-01-15 --output artifacts/compliance_dashboard.csv
python -m scripts.serve
```

### Docker / Postgres + pgvector

```bash
cp .env.example .env
docker compose up --build
```

API will be available at [http://localhost:8000](http://localhost:8000).

## Example CLI Query

```bash
python -m scripts.ask \
  --role Analyst \
  --jurisdiction US-FDA \
  --doc-type SOP \
  --as-of 2026-01-15 \
  --question "Within how many business days must batch records be reviewed after manufacturing completion?"
```

Sample output:

```text
Batch production records shall be reviewed within 1 business day after manufacturing completion. [DOC:cad3fe6d-986b-567b-b9fd-7093cc96ce31 VER:2 CH:87691cbb-33f5-5dc6-8590-36d86b628551]
Citations:
  - [DOC:cad3fe6d-986b-567b-b9fd-7093cc96ce31 VER:2 CH:87691cbb-33f5-5dc6-8590-36d86b628551]
```

## API Example

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

## Benchmark and Evaluation

The synthetic benchmark contains 60 questions across `US-FDA`, `EU-MDR`, and `ISO13485`, spanning `SOP`, `WI`, `POLICY`, `TRAINING`, and `CAPA`.

Run:

```bash
python -m scripts.evaluate
```

Outputs:

- `artifacts/evaluation_report.csv`
- `artifacts/evaluation_summary.md`

Illustrative report snippet:

```csv
qid,question,recall_at_k,citation_accuracy,grounding_rate,expected_document_id,expected_version_number
USFDA_BATCH_RECORD_REVIEW-v2-q1,"As of 2026-01-15, within how many business days must batch records be reviewed after manufacturing completion?",1,1,1.0,cad3fe6d-986b-567b-b9fd-7093cc96ce31,2
```

## Compliance Tracker

Run:

```bash
python -m scripts.compliance_tracker --as-of 2026-01-15 --output artifacts/compliance_dashboard.csv
```

Dashboard columns:

- `document_id`
- `title`
- `status`
- `effective_date`
- `days_since_review`
- `risk_flag`

Flags include `REAPPROVAL_OVERDUE`, `DRAFT_IN_CONTROLLED_SET`, `OBSOLETE_ACTIVE_REFERENCE`, and `NO_EFFECTIVE_VERSION`.

## Environment Variables

- `DATABASE_URL`: SQLite by default; set Postgres URL for `pgvector`.
- `EMBEDDING_BACKEND`: `local` or `openai`.
- `OPENAI_API_KEY`: required only when `EMBEDDING_BACKEND=openai`.
- `OPENAI_EMBEDDING_MODEL`: default `text-embedding-3-small`.
- `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RETRIEVAL_TOP_K`, `REVIEW_WINDOW_DAYS`.

## Security Notes

- Do not commit `.env` files or API keys.
- The repository uses synthetic data only.
- Audit logs intentionally capture query filters and object IDs; avoid putting secrets into prompts.
- OpenAI embeddings are optional and disabled by default.

## Notes

- The source-bounded Q&A flow is deterministic and citation-first.
- The local embedding fallback uses a hashing vectorizer so the project works without paid API keys.
- The synthetic corpus includes jurisdictional conflicts, version drift, draft content, and obsolete references to exercise retrieval controls.
