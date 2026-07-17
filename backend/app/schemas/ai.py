from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class QARequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def non_blank_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("question 不能为空")
        return cleaned


class SummaryResponse(BaseModel):
    paper_id: int
    summary_id: int | None = None
    summary: dict[str, str]
    is_mock: bool
    model_name: str


class QAResponse(BaseModel):
    answer: str
    evidence: list[str]
    has_evidence: bool
    is_mock: bool
    failure_reason: str | None = None
    qa_record_id: int | None = None


class QARecordResponse(BaseModel):
    id: int
    paper_id: int
    question: str
    answer: str
    evidence: list[str]
    has_evidence: bool
    is_mock: bool
    created_at: datetime


class ComparePapersRequest(BaseModel):
    paper_ids: list[int] = Field(min_length=2, max_length=20)
    compare_dimensions: list[str] = Field(min_length=1, max_length=20)

    @field_validator("paper_ids", mode="before")
    @classmethod
    def reject_boolean_paper_ids(cls, value):
        if isinstance(value, list) and any(isinstance(paper_id, bool) for paper_id in value):
            raise ValueError("paper_ids 必须是正整数")
        return value

    @field_validator("paper_ids")
    @classmethod
    def unique_positive_paper_ids(cls, value: list[int]) -> list[int]:
        if any(isinstance(paper_id, bool) or paper_id <= 0 for paper_id in value):
            raise ValueError("paper_ids 必须是正整数")
        if len(set(value)) != len(value):
            raise ValueError("paper_ids 不能重复")
        return value

    @field_validator("compare_dimensions")
    @classmethod
    def clean_dimensions(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value):
            raise ValueError("compare_dimensions 不能包含空白项")
        cleaned = [item.strip() for item in value]
        if any(len(item) > 100 for item in cleaned):
            raise ValueError("compare_dimensions 单项最长 100 个字符")
        if {"paper_id", "title"} & set(cleaned):
            raise ValueError("compare_dimensions 不能使用保留字段 paper_id 或 title")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("compare_dimensions 不能重复")
        return cleaned


class ComparePapersResponse(BaseModel):
    comparison_id: int | None = None
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
