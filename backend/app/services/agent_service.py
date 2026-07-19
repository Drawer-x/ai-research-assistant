"""Generate validated research plans with a deterministic local fallback."""

import logging
import time
from typing import Any

from app.core.config import settings
from app.services.ai_errors import AIErrorReason, AIServiceError
from .llm_client import chat_with_deepseek
from .structured_output import StructuredOutputError, parse_json_object

logger = logging.getLogger(__name__)


def _mock_plan(topic: str, duration_weeks: int) -> dict:
    return {
        "topic": topic,
        "stages": [{"name": "背景学习", "tasks": ["阅读综述论文", "了解基础概念"], "output": "完成研究背景笔记"}],
        "weekly_plan": [
            {"week": week, "goal": "了解基础概念" if week == 1 else "推进研究任务", "tasks": ["阅读 2 篇相关论文", "整理研究笔记"]}
            for week in range(1, duration_weeks + 1)
        ],
        "risks": ["选题范围较大，建议先聚焦具体任务"],
        "is_mock": True,
    }


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise StructuredOutputError(AIErrorReason.MALFORMED_RESPONSE, f"{field} 必须是非空数组")
    cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if len(cleaned) != len(value):
        raise StructuredOutputError(AIErrorReason.MALFORMED_RESPONSE, f"{field} 包含无效内容")
    return cleaned


def _validate_plan(data: dict[str, Any], duration_weeks: int) -> dict[str, Any]:
    raw_stages = data.get("stages")
    raw_weeks = data.get("weekly_plan")
    if not isinstance(raw_stages, list) or not raw_stages:
        raise StructuredOutputError(AIErrorReason.MALFORMED_RESPONSE, "stages 必须是非空数组")
    if not isinstance(raw_weeks, list) or not raw_weeks:
        raise StructuredOutputError(AIErrorReason.MALFORMED_RESPONSE, "weekly_plan 必须是非空数组")

    stages: list[dict[str, Any]] = []
    for item in raw_stages:
        if not isinstance(item, dict):
            raise StructuredOutputError(AIErrorReason.MALFORMED_RESPONSE, "stage 结构无效")
        name, output = item.get("name"), item.get("output")
        if not isinstance(name, str) or not name.strip() or not isinstance(output, str) or not output.strip():
            raise StructuredOutputError(AIErrorReason.MALFORMED_RESPONSE, "stage 字段不完整")
        stages.append({"name": name.strip(), "tasks": _string_list(item.get("tasks"), "stage.tasks"), "output": output.strip()})

    weekly_plan: list[dict[str, Any]] = []
    seen_weeks: set[int] = set()
    for item in raw_weeks:
        if not isinstance(item, dict):
            raise StructuredOutputError(AIErrorReason.MALFORMED_RESPONSE, "weekly_plan 结构无效")
        week, goal = item.get("week"), item.get("goal")
        if not isinstance(week, int) or isinstance(week, bool) or not 1 <= week <= duration_weeks:
            raise StructuredOutputError(AIErrorReason.MALFORMED_RESPONSE, "weekly_plan.week 超出范围")
        if week in seen_weeks or not isinstance(goal, str) or not goal.strip():
            raise StructuredOutputError(AIErrorReason.MALFORMED_RESPONSE, "weekly_plan 字段无效")
        seen_weeks.add(week)
        weekly_plan.append({"week": week, "goal": goal.strip(), "tasks": _string_list(item.get("tasks"), "weekly_plan.tasks")})
    if seen_weeks != set(range(1, duration_weeks + 1)):
        raise StructuredOutputError(AIErrorReason.MALFORMED_RESPONSE, "weekly_plan 未覆盖完整周期")
    weekly_plan.sort(key=lambda item: item["week"])
    return {"stages": stages, "weekly_plan": weekly_plan, "risks": _string_list(data.get("risks"), "risks")}


def generate_research_plan(topic: str, level: str, duration_weeks: int) -> dict:
    topic = topic.strip() if isinstance(topic, str) else ""
    level = level.strip() if isinstance(level, str) else ""
    if not topic:
        raise ValueError("topic 不能为空")
    if not level:
        raise ValueError("level 不能为空")
    if isinstance(duration_weeks, bool) or not isinstance(duration_weeks, int) or not 1 <= duration_weeks <= 52:
        raise ValueError("duration_weeks 必须在 1 到 52 之间")
    prompt = f'''用户研究方向：{topic}\n研究水平：{level}\n周期：{duration_weeks}周
请仅返回 JSON。stages 每项必须包含 name、tasks、output；weekly_plan 必须覆盖第 1 到 {duration_weeks} 周且每项包含 week、goal、tasks；risks 为非空字符串数组。'''
    started = time.monotonic()
    logger.info("进入真实 Agent service（API key configured=%s）", bool(settings.ecnu_api_key))
    try:
        plan = _validate_plan(parse_json_object(chat_with_deepseek(prompt)), duration_weeks)
        logger.info("Agent service 成功（elapsed_ms=%d）", int((time.monotonic() - started) * 1000))
        return {"topic": topic, **plan, "is_mock": False}
    except AIServiceError as exc:
        logger.warning("Agent service 使用 fallback（reason=%s, elapsed_ms=%d）", exc.reason.value, int((time.monotonic() - started) * 1000))
        return _mock_plan(topic, duration_weeks)
