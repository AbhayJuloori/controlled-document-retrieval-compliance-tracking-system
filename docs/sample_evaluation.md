# Sample Evaluation Notes

After ingesting the synthetic dataset and running `python -m scripts.evaluate`, the project writes:

- `artifacts/evaluation_report.csv`
- `artifacts/evaluation_summary.md`

The benchmark measures:

- Recall@K for document/version retrieval.
- Citation accuracy for whether the answer cites the expected document/version.
- Grounding rate using sentence-overlap support against retrieved snippets.

The synthetic dataset includes jurisdictional drift and version conflicts so retrieval quality changes meaningfully with `as_of` dates.

