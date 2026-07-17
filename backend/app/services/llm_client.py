"""Lazy client for the ECNU OpenAI-compatible chat API."""

from functools import lru_cache

from app.core.config import settings
from app.services.ai_errors import AIErrorReason, AIServiceError, provider_error


class LLMServiceError(AIServiceError):
    """Raised when the optional LLM service cannot be used."""


@lru_cache
def _get_client():
    if not settings.ecnu_api_key:
        raise LLMServiceError(AIErrorReason.MISSING_CONFIGURATION, "未配置 ECNU_API_KEY")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMServiceError(AIErrorReason.DEPENDENCY_MISSING, "未安装 openai 依赖") from exc
    return OpenAI(
        api_key=settings.ecnu_api_key,
        base_url=settings.ecnu_base_url,
        timeout=settings.ai_timeout_seconds,
        max_retries=1,
    )


def chat_with_deepseek(prompt: str) -> str:
    """Send a chat request without making application startup depend on AI."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt 不能为空")
    if not isinstance(settings.ai_max_prompt_chars, int) or not 1 <= settings.ai_max_prompt_chars <= 100_000:
        raise LLMServiceError(AIErrorReason.MISSING_CONFIGURATION, "ai_max_prompt_chars 配置无效")
    bounded_prompt = prompt[: settings.ai_max_prompt_chars]
    try:
        response = _get_client().chat.completions.create(
            model=settings.ecnu_chat_model,
            messages=[
                {"role": "system", "content": "你是一名严谨的科研论文阅读助手。"},
                {"role": "user", "content": bounded_prompt},
            ],
            temperature=0.2,
        )
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise LLMServiceError(
                AIErrorReason.MALFORMED_RESPONSE,
                "模型返回结构不完整",
            ) from exc
        if not isinstance(content, str) or not content.strip():
            raise LLMServiceError(AIErrorReason.EMPTY_RESPONSE, "模型返回了空内容")
        return content.strip()
    except LLMServiceError:
        raise
    except Exception as exc:
        raise provider_error(LLMServiceError, "AI 服务", exc) from None
