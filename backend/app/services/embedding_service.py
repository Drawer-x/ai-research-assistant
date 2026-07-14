"""Embedding helpers with lazy optional dependency initialization."""

from functools import lru_cache

from app.core.config import settings


class EmbeddingServiceError(RuntimeError):
    pass


@lru_cache
def _get_client():
    if not settings.ecnu_api_key:
        raise EmbeddingServiceError("未配置 ECNU_API_KEY")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise EmbeddingServiceError("未安装 openai 依赖") from exc
    return OpenAI(
        api_key=settings.ecnu_api_key,
        base_url=settings.ecnu_base_url,
        timeout=settings.ai_timeout_seconds,
        max_retries=1,
    )


def get_embedding(text: str) -> list[float]:
    if not text.strip():
        raise EmbeddingServiceError("不能为纯空白文本生成向量")
    try:
        response = _get_client().embeddings.create(
            model=settings.ecnu_embedding_model,
            input=text,
        )
        return response.data[0].embedding
    except EmbeddingServiceError:
        raise
    except Exception as exc:
        raise EmbeddingServiceError(f"向量服务调用失败：{exc}") from exc


def get_embeddings(texts: list[str]) -> list[list[float]]:
    clean_texts = [text for text in texts if text.strip()]
    if not clean_texts:
        return []
    return [get_embedding(text) for text in clean_texts]
