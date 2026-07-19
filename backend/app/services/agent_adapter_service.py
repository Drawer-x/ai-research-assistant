"""Compatibility adapter for current and future research-plan services."""

import importlib
import inspect
import logging
from typing import Any

logger = logging.getLogger(__name__)
LIST_FIELDS = ("reading_route", "stages", "weekly_plan", "tasks", "risks", "recommended_papers")


def _list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _fallback(topic: str, duration_weeks: int) -> dict:
    weeks = [{"week": week, "goal": "推进研究任务", "tasks": ["阅读论文", "整理研究笔记"]} for week in range(1, duration_weeks + 1)]
    return {
        "reading_route": ["背景调研", "方法分析", "实验与写作"],
        "stages": [{"name": "研究准备", "tasks": ["明确问题"], "output": "研究方案"}],
        "weekly_plan": weeks, "tasks": ["阅读论文", "实现原型", "撰写报告"],
        "risks": ["研究范围可能过大"], "recommended_papers": [], "is_mock": True,
    }


def safe_generate_research_plan(research_topic: str, research_goal: str, duration_weeks: int, current_level: str | None, papers: list[dict]) -> dict:
    fallback = _fallback(research_topic, duration_weeks)
    try:
        module = importlib.import_module("app.services.agent_service")
        function = next((getattr(module, name, None) for name in ("generate_research_plan", "create_research_plan", "generate_agent_plan") if callable(getattr(module, name, None))), None)
        if function is None:
            return fallback
        params = inspect.signature(function).parameters
        if set(("topic", "level", "duration_weeks")).issubset(params):
            result = function(research_topic, current_level or "beginner", duration_weeks)
        else:
            kwargs = {"research_topic": research_topic, "research_goal": research_goal, "duration_weeks": duration_weeks, "current_level": current_level, "papers": papers}
            result = function(**{key: value for key, value in kwargs.items() if key in params})
        if not isinstance(result, dict) or not any(result.get(field) for field in LIST_FIELDS):
            return fallback
        normalized = {field: _list(result.get(field)) for field in LIST_FIELDS}
        normalized["is_mock"] = result.get("is_mock") is not False
        return normalized
    except Exception as exc:
        logger.warning("科研计划使用 fallback（reason=%s）", type(exc).__name__)
        return fallback
