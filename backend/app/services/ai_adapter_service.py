"""Stable Sprint 2 adapter around optional member-B AI services."""

from __future__ import annotations

import importlib
from typing import Any


SUMMARY_FIELDS = (
    "background", "problem", "method", "experiment", "result", "innovation", "limitation",
)


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
            is_mock = bool(summary.pop("is_mock", False))
            model_name = "fallback-mock" if is_mock else "ai-service"
        if not isinstance(summary, dict) or any(field not in summary for field in SUMMARY_FIELDS):
            return fallback
        return {"summary": summary, "is_mock": bool(is_mock), "model_name": str(model_name)}
    except Exception:
        return fallback


def _fallback_answer() -> dict:
    return {
        "answer": "这是基于论文内容生成的 fallback 占位回答。",
        "evidence": [],
        "has_evidence": False,
        "is_mock": True,
    }


def safe_answer_question(question: str, paper_text: str, paper_id: int | None = None) -> dict:
    fallback = _fallback_answer()
    try:
        module = importlib.import_module("app.services.qa_service")
        answerer = getattr(module, "answer_question_about_paper")
        try:
            result = answerer(question, paper_text, paper_id=paper_id)
        except TypeError:
            result = answerer(question, paper_text)
        if not isinstance(result, dict) or not isinstance(result.get("answer"), str):
            return fallback
        evidence = result.get("evidence", [])
        if not isinstance(evidence, list):
            evidence = []
        return {
            "answer": result["answer"],
            "evidence": evidence,
            "has_evidence": bool(result.get("has_evidence", evidence)),
            "is_mock": bool(result.get("is_mock", False)),
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
        "summary": "这是多论文对比的 fallback 总结，后续可由成员 B 替换为真实 AI 输出。",
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
        if not isinstance(table, list) or not isinstance(summary, str):
            return fallback
        return {"comparison_table": table, "summary": summary, "is_mock": bool(result.get("is_mock", False))}
    except Exception:
        return fallback
