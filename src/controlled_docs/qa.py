from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

from controlled_docs.retrieval import RetrievalQuery, RetrievalResult, RetrievalService
from controlled_docs.utils import tokenize


@dataclass(slots=True)
class AskQuery:
    role: str
    jurisdiction: str
    doc_type: str
    as_of_date: date
    question: str
    top_k: int
    include_nonapproved: bool = False


class QAService:
    def __init__(self, retrieval_service: RetrievalService):
        self.retrieval_service = retrieval_service
        self.prompt = PromptTemplate.from_template(
            "You are an audit-ready compliance assistant.\n"
            "Answer only from the controlled-document context.\n"
            "Question: {question}\n"
            "Role: {role}\n"
            "Filters: jurisdiction={jurisdiction}; doc_type={doc_type}; as_of={as_of}; "
            "include_nonapproved={include_nonapproved}\n"
            "Context:\n{context}\n"
            "Return concise grounded statements with citations using "
            "[DOC:<document_id> VER:<version_number> CH:<chunk_id>]."
        )
        self.chain = (
            RunnableLambda(self._retrieve_payload)
            | RunnableLambda(self._render_prompt)
            | RunnableLambda(self._compose_answer)
        )

    def ask(self, query: AskQuery) -> dict:
        return self.chain.invoke(query)

    def _retrieve_payload(self, query: AskQuery) -> dict:
        retrieval_query = RetrievalQuery(
            role=query.role,
            jurisdiction=query.jurisdiction,
            doc_type=query.doc_type,
            as_of_date=query.as_of_date,
            question=query.question,
            top_k=query.top_k,
            include_nonapproved=query.include_nonapproved,
        )
        results = self.retrieval_service.retrieve(retrieval_query)
        return {"query": query, "results": results}

    def _render_prompt(self, payload: dict) -> dict:
        query: AskQuery = payload["query"]
        results: list[RetrievalResult] = payload["results"]
        context = "\n".join(
            f"- {result.title} | {result.effective_date} | {result.citation} | {result.snippet}"
            for result in results
        )
        payload["prompt"] = self.prompt.format(
            question=query.question,
            role=query.role,
            jurisdiction=query.jurisdiction,
            doc_type=query.doc_type,
            as_of=query.as_of_date,
            include_nonapproved=query.include_nonapproved,
            context=context or "(no matching context)",
        )
        return payload

    def _compose_answer(self, payload: dict) -> dict:
        query: AskQuery = payload["query"]
        results: list[RetrievalResult] = payload["results"]
        if not results:
            return self._insufficient_response(query)

        question_tokens = set(tokenize(query.question))
        candidates: list[tuple[int, str, str]] = []
        for result in results:
            sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", result.snippet) if segment.strip()]
            for sentence in sentences:
                overlap = len(question_tokens.intersection(set(tokenize(sentence))))
                candidates.append((overlap, sentence.rstrip("."), result.citation))
        candidates.sort(key=lambda item: item[0], reverse=True)

        selected: list[str] = []
        citations: list[str] = []
        for overlap, sentence, citation in candidates:
            if overlap == 0 and selected:
                continue
            statement = f"{sentence}. {citation}"
            if statement not in selected:
                selected.append(statement)
                citations.append(citation)
            if len(selected) == 3:
                break

        if not selected or candidates[0][0] == 0:
            return self._insufficient_response(query)

        return {
            "answer": " ".join(selected),
            "citations": citations,
            "searched": {
                "role": query.role,
                "jurisdiction": query.jurisdiction,
                "doc_type": query.doc_type,
                "as_of": str(query.as_of_date),
            },
            "results": [result.__dict__ for result in results],
            "prompt": payload["prompt"],
        }

    @staticmethod
    def _insufficient_response(query: AskQuery) -> dict:
        return {
            "answer": (
                "Insufficient evidence in controlled documents. "
                f"Searched role={query.role}, jurisdiction={query.jurisdiction}, "
                f"doc_type={query.doc_type}, as_of={query.as_of_date}."
            ),
            "citations": [],
            "searched": {
                "role": query.role,
                "jurisdiction": query.jurisdiction,
                "doc_type": query.doc_type,
                "as_of": str(query.as_of_date),
            },
            "results": [],
        }

