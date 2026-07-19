"""Small, safe client for the ChatECNU chat-completions endpoint."""

from typing import Any
import logging

import requests

from app.core.config import settings
from app.services.ai_errors import AIErrorReason, AIServiceError


class LLMServiceError(AIServiceError):
    """Raised when the optional LLM service cannot be used."""


logger = logging.getLogger(__name__)


def _extract_content(payload: Any) -> str:
    """Accept known ChatECNU/OpenAI-compatible response envelopes."""
    if not isinstance(payload, dict):
        raise LLMServiceError(AIErrorReason.MALFORMED_RESPONSE, "ChatECNU 返回值不是 JSON 对象")
    candidates = [payload, payload.get("data")]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        choices = candidate.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                content = message["content"].strip()
                if content:
                    return content
    content = payload.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    message = payload.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        content = message["content"].strip()
        if content:
            return content
    raise LLMServiceError(AIErrorReason.MALFORMED_RESPONSE, "ChatECNU 返回中缺少文本内容")


def chat_completion(messages: list[dict], model: str | None = None) -> str:
    """Call ChatECNU without exposing credentials, prompts, or raw responses."""
    logger.info("ECNU_API_KEY configured: %s", bool(settings.ecnu_api_key))
    if not settings.ecnu_api_key:
        raise LLMServiceError(AIErrorReason.MISSING_CONFIGURATION, "未配置 ECNU_API_KEY")
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages 不能为空")
    normalized: list[dict[str, str]] = []
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("message 结构无效")
        role, content = message.get("role"), message.get("content")
        if role not in {"system", "user", "assistant"} or not isinstance(content, str) or not content.strip():
            raise ValueError("message 缺少有效 role 或 content")
        normalized.append({"role": role, "content": content})
    try:
        response = requests.post(
            settings.ecnu_api_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.ecnu_api_key}",
            },
            json={"messages": normalized, "stream": False, "model": model or settings.ecnu_model},
            timeout=settings.ecnu_api_timeout_seconds,
        )
    except requests.Timeout as exc:
        raise LLMServiceError(AIErrorReason.TIMEOUT, "ChatECNU 请求超时") from exc
    except requests.RequestException as exc:
        raise LLMServiceError(AIErrorReason.PROVIDER_ERROR, "ChatECNU 连接失败") from exc
    if not response.ok:
        logger.warning("ChatECNU HTTP 请求失败（status=%s）", response.status_code)
        raise LLMServiceError(AIErrorReason.PROVIDER_ERROR, f"ChatECNU 返回 HTTP {response.status_code}")
    try:
        payload = response.json()
    except (ValueError, requests.JSONDecodeError) as exc:
        raise LLMServiceError(AIErrorReason.MALFORMED_RESPONSE, "ChatECNU 返回非 JSON 内容") from exc
    content = _extract_content(payload)
    logger.info(
        "ChatECNU HTTP 成功（model=%s, content_type=%s, content_chars=%s）",
        model or settings.ecnu_model,
        type(content).__name__,
        len(content),
    )
    return content


def chat_with_deepseek(prompt: str) -> str:
    """Backward-compatible prompt helper used by existing AI services."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt 不能为空")
    if not isinstance(settings.ai_max_prompt_chars, int) or not 1 <= settings.ai_max_prompt_chars <= 100_000:
        raise LLMServiceError(AIErrorReason.MISSING_CONFIGURATION, "ai_max_prompt_chars 配置无效")
    bounded_prompt = prompt[: settings.ai_max_prompt_chars]
    return chat_completion([
        {"role": "system", "content": (
            "你是一名严谨的科研论文阅读助手，只按任务要求返回内容。"
            "Return only one valid JSON object. Do not wrap the JSON in Markdown code fences. "
            "Do not include explanatory text before or after the JSON."
        )},
        {"role": "user", "content": bounded_prompt},
    ])
