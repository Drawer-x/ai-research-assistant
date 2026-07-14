"""Lazy client for the ECNU OpenAI-compatible chat API."""

from functools import lru_cache

from app.core.config import settings


class LLMServiceError(RuntimeError):
    """Raised when the optional LLM service cannot be used."""


@lru_cache
def _get_client():
    if not settings.ecnu_api_key:
        raise LLMServiceError("未配置 ECNU_API_KEY")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMServiceError("未安装 openai 依赖") from exc
    return OpenAI(
        api_key=settings.ecnu_api_key,
        base_url=settings.ecnu_base_url,
        timeout=settings.ai_timeout_seconds,
        max_retries=1,
    )


def chat_with_deepseek(prompt: str) -> str:
    """Send a chat request without making application startup depend on AI."""
    try:
        response = _get_client().chat.completions.create(
            model=settings.ecnu_chat_model,
            messages=[
                {"role": "system", "content": "你是一名严谨的科研论文阅读助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            raise LLMServiceError("模型返回了空内容")
        return content
    except LLMServiceError:
        raise
    except Exception as exc:
        raise LLMServiceError(f"AI 服务调用失败：{exc}") from exc
