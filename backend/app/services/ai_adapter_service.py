"""Stable Sprint 2 adapter around optional member-B AI services."""

from __future__ import annotations

import importlib
import inspect
from typing import Any


SUMMARY_FIELDS = (
    "background", "problem", "method", "experiment", "result", "innovation", "limitation",
)
QA_FAILURE_REASONS = {
    "missing_index",
    "corrupt_index",
    "empty_retrieval",
    "embedding_failure",
    "generation_failure",
    "rag_unavailable",
}


def _fallback_summary(paper_text: str) -> dict:
    preview = " ".join(paper_text.split())[:800] or "未提取到论文正文"
    return {
        "summary": {
            "background": preview,
            "problem": "待由 AI 提取或 fallback",
            "method": "待由 AI 提取或 fallback",
            "experiment": "待由 AI 提取或 fallback",
            "result": "待由 AI 提取或 fallback",
            "innovation": "待由 AI 提取或 fallback",
            "limitation": "待由 AI 提取或 fallback",
        },
        "is_mock": True,
        "model_name": "fallback-mock",
    }


def safe_generate_summary(paper_text: str) -> dict:
    fallback = _fallback_summary(paper_text)
    try:
        module = importlib.import_module("app.services.ai_summary_service")
        result_helper = getattr(module, "generate_paper_summary_result", None)
        if callable(result_helper):
            summary, is_mock, model_name = result_helper(paper_text)
        else:
            generator = getattr(module, "generate_paper_summary")
            summary = generator(paper_text)
            is_mock = bool(summary.pop("is_mock", True))
            model_name = "fallback-mock" if is_mock else "ai-service"
        if not isinstance(summary, dict) or any(
            not isinstance(summary.get(field), str) or not summary[field].strip()
            for field in SUMMARY_FIELDS
        ):
            return fallback
        if not isinstance(is_mock, bool) or not isinstance(model_name, str) or not model_name.strip():
            return fallback
        normalized = {field: summary[field].strip() for field in SUMMARY_FIELDS}
        return {"summary": normalized, "is_mock": is_mock, "model_name": model_name.strip()}
    except Exception:
        return fallback


def _fallback_answer() -> dict:
    return {
        "answer": "这是基于论文内容生成的 fallback 占位回答。",
        "evidence": [],
        "has_evidence": False,
        "is_mock": True,
        "failure_reason": "rag_unavailable",
    }


def safe_answer_question(
    question: str,
    paper_text: str,
    paper_id: int | None = None,
    user_id: int | None = None,
) -> dict:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question 不能为空")
    fallback = _fallback_answer()
    try:
        module = importlib.import_module("app.services.qa_service")
        answerer = getattr(module, "answer_question_about_paper")
        parameters = inspect.signature(answerer).parameters
        kwargs: dict[str, Any] = {}
        if "paper_id" in parameters:
            kwargs["paper_id"] = paper_id
        if "user_id" in parameters:
            kwargs["user_id"] = user_id
        result = answerer(question, paper_text, **kwargs)
        if (
            not isinstance(result, dict)
            or not isinstance(result.get("answer"), str)
            or not result["answer"].strip()
        ):
            return fallback
        evidence = result.get("evidence", [])
        if not isinstance(evidence, list) or any(
            not isinstance(item, str) or not item.strip() for item in evidence
        ):
            evidence = []
        is_real = result.get("is_mock") is False and bool(evidence)
        failure_reason = result.get("failure_reason")
        if is_real:
            failure_reason = None
        elif failure_reason not in QA_FAILURE_REASONS:
            failure_reason = "rag_unavailable"
        return {
            "answer": result["answer"].strip(),
            "evidence": evidence,
            "has_evidence": bool(evidence),
            "is_mock": not is_real,
            "failure_reason": failure_reason,
        }
    except Exception:
        return fallback


def _fallback_comparison(papers: list[dict], compare_dimensions: list[str]) -> dict:
    table = []
    for paper in papers:
        row: dict[str, Any] = {"paper_id": paper["paper_id"], "title": paper["title"]}
        row.update({dimension: "待由 AI 提取或 fallback" for dimension in compare_dimensions})
        table.append(row)
    return {
        "comparison_table": table,
        "summary": "AI 服务暂不可用，当前仅返回结构稳定的对比占位结果。",
        "is_mock": True,
    }


def safe_compare_papers(papers: list[dict], compare_dimensions: list[str]) -> dict:
    fallback = _fallback_comparison(papers, compare_dimensions)
    try:
        module = importlib.import_module("app.services.compare_service")
        comparer = getattr(module, "compare_papers")
        result = comparer(papers, compare_dimensions)
        if not isinstance(result, dict):
            return fallback
        table = result.get("comparison_table")
        summary = result.get("summary")
        expected_ids = [paper["paper_id"] for paper in papers]
        if (
            not isinstance(table, list)
            or len(table) != len(expected_ids)
            or not isinstance(summary, str)
            or not summary.strip()
            or result.get("is_mock") is not False
        ):
            return fallback
        normalized_table: list[dict[str, Any]] = []
        for expected_id, row in zip(expected_ids, table):
            if not isinstance(row, dict) or row.get("paper_id") != expected_id:
                return fallback
            normalized_row: dict[str, Any] = {
                "paper_id": expected_id,
                "title": str(row.get("title", "")).strip(),
            }
            if not normalized_row["title"]:
                return fallback
            for dimension in compare_dimensions:
                value = row.get(dimension)
                if not isinstance(value, str) or not value.strip():
                    return fallback
                normalized_row[dimension] = value.strip()
            normalized_table.append(normalized_row)
        return {"comparison_table": normalized_table, "summary": summary.strip(), "is_mock": False}
    except Exception:
        return fallback
