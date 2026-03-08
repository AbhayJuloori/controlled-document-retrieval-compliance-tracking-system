from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    role: str = Field(default="Analyst")
    jurisdiction: str
    doc_type: str
    as_of: str
    question: str
    top_k: int = 5
    include_nonapproved: bool = False


class AskResponse(BaseModel):
    answer: str
    citations: list[str]
    searched: dict[str, str]
    results: list[dict]

