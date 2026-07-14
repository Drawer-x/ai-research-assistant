"""Generate a structured paper summary with a deterministic local fallback."""

import json
import re

from app.core.config import settings
from app.services.llm_client import LLMServiceError, chat_with_deepseek


SUMMARY_FIELDS = (
    "background", "problem", "method", "experiment", "result", "innovation", "limitation",
)


def _extract_json(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?|```", "", text, flags=re.IGNORECASE).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        data = json.loads(match.group())
    if not isinstance(data, dict):
        raise ValueError("模型返回值不是 JSON 对象")
    return {field: str(data.get(field) or "未提及").strip() for field in SUMMARY_FIELDS}


def _local_fallback(paper_text: str) -> dict:
    normalized = re.sub(r"\s+", " ", paper_text).strip()
    preview = normalized[:800] if normalized else "未提取到论文正文"
    return {
        "background": preview,
        "problem": "AI 服务暂不可用，请稍后重新生成以提取研究问题。",
        "method": "AI 服务暂不可用，未自动提取核心方法。",
        "experiment": "AI 服务暂不可用，未自动提取实验设置。",
        "result": "AI 服务暂不可用，未自动提取实验结果。",
        "innovation": "AI 服务暂不可用，未自动提取创新点。",
        "limitation": "AI 服务暂不可用，未自动提取局限性。",
    }


def generate_paper_summary_result(paper_text: str) -> tuple[dict, bool, str]:
    """Return ``(summary, is_mock, model_name)`` for correct persistence."""
    if not paper_text.strip():
        return _local_fallback(paper_text), True, "local-fallback"

    prompt = f"""
你是一名专业科研助手。请严格根据下面的论文内容生成结构化总结。

要求：
1. 只输出 JSON，不要输出 Markdown 代码块。
2. 不得编造原文中不存在的信息；缺失的信息填写“未提及”。
3. JSON 必须包含 background、problem、method、experiment、result、innovation、limitation。

论文内容：
{paper_text[:15_000]}
""".strip()
    try:
        return _extract_json(chat_with_deepseek(prompt)), False, settings.ecnu_chat_model
    except (LLMServiceError, ValueError, TypeError, json.JSONDecodeError):
        return _local_fallback(paper_text), True, "local-fallback"


def generate_paper_summary(paper_text: str) -> dict:
    """Backward-compatible helper returning only summary fields."""
    return generate_paper_summary_result(paper_text)[0]
