from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class QARequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class SummaryResponse(BaseModel):
    paper_id: int
    summary: dict[str, Any]
    is_mock: bool
    model_name: str


class QARecordResponse(BaseModel):
    id: int
    paper_id: int
    question: str
    answer: str
    evidence: list[Any]
    has_evidence: bool
    is_mock: bool
    created_at: datetime


class ComparePapersRequest(BaseModel):
    paper_ids: list[int] = Field(min_length=2, max_length=20)
    compare_dimensions: list[str] = Field(min_length=1, max_length=20)

    @field_validator("paper_ids")
    @classmethod
    def unique_positive_paper_ids(cls, value: list[int]) -> list[int]:
        if any(paper_id <= 0 for paper_id in value):
            raise ValueError("paper_ids 必须是正整数")
        if len(set(value)) != len(value):
            raise ValueError("paper_ids 不能重复")
        return value

    @field_validator("compare_dimensions")
    @classmethod
    def clean_dimensions(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("compare_dimensions 不能为空")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("compare_dimensions 不能重复")
        return cleaned


class ComparePapersResponse(BaseModel):
    paper_ids: list[int]
    compare_dimensions: list[str]
    comparison_table: list[dict[str, Any]]
    summary: str
    is_mock: bool


class ComparisonHistoryResponse(BaseModel):
    id: int
    paper_ids: list[int]
    compare_dimensions: list[str]
    result: dict[str, Any]
    is_mock: bool
    created_at: datetime
