from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from controlled_docs.qa import AskQuery, QAService
from controlled_docs.retrieval import RetrievalQuery, RetrievalService
from controlled_docs.utils import ensure_parent_dir, parse_date, tokenize


@dataclass(slots=True)
class BenchmarkQuestion:
    qid: str
    role: str
    jurisdiction: str
    doc_type: str
    as_of: date
    question: str
    expected_document_id: str
    expected_version_number: int
    expected_phrase: str


def load_benchmark(path: Path) -> list[BenchmarkQuestion]:
    questions: list[BenchmarkQuestion] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            questions.append(
                BenchmarkQuestion(
                    qid=payload["qid"],
                    role=payload["role"],
                    jurisdiction=payload["jurisdiction"],
                    doc_type=payload["doc_type"],
                    as_of=parse_date(payload["as_of"]),
                    question=payload["question"],
                    expected_document_id=payload["expected_document_id"],
                    expected_version_number=int(payload["expected_version_number"]),
                    expected_phrase=payload["expected_phrase"],
                )
            )
    return questions


def grounding_rate(answer: str, retrieved_snippets: list[str]) -> float:
    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", answer) if segment.strip()]
    if not sentences:
        return 0.0
    supported = 0
    snippet_tokens = [set(tokenize(snippet)) for snippet in retrieved_snippets]
    for sentence in sentences:
        sentence_tokens = set(tokenize(re.sub(r"\[DOC:.*?\]", "", sentence)))
        for snippet_token_set in snippet_tokens:
            if not sentence_tokens:
                continue
            overlap = len(sentence_tokens.intersection(snippet_token_set)) / len(sentence_tokens)
            if overlap >= 0.5:
                supported += 1
                break
    return supported / len(sentences)


def evaluate_benchmark(
    session: Session,
    qa_service: QAService,
    retrieval_service: RetrievalService,
    *,
    benchmark_path: Path,
    csv_output_path: Path,
    markdown_output_path: Path,
    top_k: int = 5,
) -> dict[str, float]:
    questions = load_benchmark(benchmark_path)
    ensure_parent_dir(csv_output_path)
    ensure_parent_dir(markdown_output_path)

    rows: list[dict[str, str | float | int]] = []
    recall_hits = 0
    citation_hits = 0
    grounding_scores: list[float] = []

    for item in questions:
        retrieval_results = retrieval_service.retrieve(
            RetrievalQuery(
                role=item.role,
                jurisdiction=item.jurisdiction,
                doc_type=item.doc_type,
                as_of_date=item.as_of,
                question=item.question,
                top_k=top_k,
            )
        )
        qa_result = qa_service.ask(
            AskQuery(
                role=item.role,
                jurisdiction=item.jurisdiction,
                doc_type=item.doc_type,
                as_of_date=item.as_of,
                question=item.question,
                top_k=top_k,
            )
        )

        recall = any(
            result.document_id == item.expected_document_id
            and result.version_number == item.expected_version_number
            for result in retrieval_results
        )
        citations = qa_result["citations"]
        citation_accuracy = any(
            item.expected_document_id in citation and f"VER:{item.expected_version_number}" in citation
            for citation in citations
        )
        grounding = grounding_rate(qa_result["answer"], [result.snippet for result in retrieval_results])

        recall_hits += int(recall)
        citation_hits += int(citation_accuracy)
        grounding_scores.append(grounding)

        rows.append(
            {
                "qid": item.qid,
                "question": item.question,
                "recall_at_k": int(recall),
                "citation_accuracy": int(citation_accuracy),
                "grounding_rate": round(grounding, 3),
                "expected_document_id": item.expected_document_id,
                "expected_version_number": item.expected_version_number,
            }
        )

    with csv_output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    metrics = {
        "questions": len(questions),
        "recall_at_k": recall_hits / len(questions),
        "citation_accuracy": citation_hits / len(questions),
        "grounding_rate": sum(grounding_scores) / len(grounding_scores),
    }
    markdown_output_path.write_text(
        "# Evaluation Summary\n\n"
        f"- Questions: {metrics['questions']}\n"
        f"- Recall@{top_k}: {metrics['recall_at_k']:.2%}\n"
        f"- Citation accuracy: {metrics['citation_accuracy']:.2%}\n"
        f"- Grounding rate: {metrics['grounding_rate']:.2%}\n",
        encoding="utf-8",
    )
    return metrics

