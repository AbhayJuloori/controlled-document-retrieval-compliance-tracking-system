PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff

.PHONY: setup sample-data ingest lint test run api evaluate compliance clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

sample-data:
	$(VENV)/bin/python -m data.generate_synthetic_data

ingest:
	$(VENV)/bin/python -m scripts.ingest --register data/document_register.xlsx --docs-dir data/docs

lint:
	$(RUFF) check src scripts tests data

test:
	$(PYTEST)

run: sample-data ingest
	$(VENV)/bin/python -m scripts.ask --role Analyst --jurisdiction US-FDA --doc-type SOP --as-of 2026-01-15 --question "Within how many business days must batch records be reviewed after manufacturing completion?"

api:
	$(VENV)/bin/python -m scripts.serve

evaluate: sample-data ingest
	$(VENV)/bin/python -m scripts.evaluate

compliance: sample-data ingest
	$(VENV)/bin/python -m scripts.compliance_tracker --as-of 2026-01-15 --output artifacts/compliance_dashboard.csv

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache artifacts/*.csv artifacts/*.md artifacts/*.db

