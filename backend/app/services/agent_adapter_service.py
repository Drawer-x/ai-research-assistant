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
    weeks = [
        {
            "week": week,
            "goal": "完成总结、验收与汇报" if week == duration_weeks else f"推进 {topic} 的第 {week} 周任务",
            "tasks": ["核对本周目标和证据", "记录可复现步骤与结果"],
            "deliverables": [f"第 {week} 周进展记录"],
        }
        for week in range(1, duration_weeks + 1)
    ]
    return {
        "reading_route": [
            {
                "order": 1,
                "name": f"{topic} 的基础证据",
                "goal": "明确问题、术语和评价指标",
                "tasks": ["整理来源可追踪的核心文献"],
                "output": "问题边界与阅读清单",
            }
        ],
        "stages": [
            {
                "name": "研究准备与最小验证",
                "start_week": 1,
                "end_week": duration_weeks,
                "goals": [f"完成 {topic} 的最小可验证研究计划"],
                "tasks": ["界定问题、执行验证并整理结论"],
                "deliverables": ["验证记录与研究报告"],
                "output": "验证记录与研究报告",
            }
        ],
        "weekly_plan": weeks,
        "tasks": [
            {
                "name": f"完成 {topic} 的最小验证",
                "category": "research",
                "priority": "high",
                "estimated_hours": max(1, min(168, duration_weeks * 4)),
                "dependencies": [],
                "acceptance_criteria": "形成来源、步骤、结果和限制均可核对的记录。",
            }
        ],
        "risks": [
            {
                "risk": "研究范围超过可用周期",
                "probability": "medium",
                "impact": "high",
                "mitigation": "收敛为一个可测指标和一个可复现基线。",
            }
        ],
        "recommended_papers": [],
        "is_mock": True,
    }


def safe_generate_research_plan(
    research_topic: str,
    research_goal: str,
    duration_weeks: int,
    current_level: str | None,
    papers: list[dict],
) -> dict:
    """Call the available service and normalize its top-level response fields."""
    fallback = _fallback(research_topic, duration_weeks)
    try:
        module = importlib.import_module("app.services.agent_service")
        function = next(
            (
                getattr(module, name, None)
                for name in (
                    "generate_research_plan",
                    "create_research_plan",
                    "generate_agent_plan",
                )
                if callable(getattr(module, name, None))
            ),
            None,
        )
        if function is None:
            return fallback
        params = inspect.signature(function).parameters
        if {"topic", "level", "duration_weeks"}.issubset(params):
            result = function(research_topic, current_level or "beginner", duration_weeks)
        else:
            kwargs = {
                "research_topic": research_topic,
                "research_goal": research_goal,
                "duration_weeks": duration_weeks,
                "current_level": current_level,
                "papers": papers,
            }
            result = function(**{key: value for key, value in kwargs.items() if key in params})
        if not isinstance(result, dict) or not any(result.get(field) for field in LIST_FIELDS):
            return fallback
        normalized = {field: _list(result.get(field)) for field in LIST_FIELDS}
        normalized["is_mock"] = result.get("is_mock") is not False
        return normalized
    except Exception as exc:
        logger.warning("科研计划使用 fallback（reason=%s）", type(exc).__name__)
        return fallback
