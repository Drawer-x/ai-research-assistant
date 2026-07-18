"""Embedding helpers with lazy optional dependency initialization."""

import math
from functools import lru_cache
from typing import Any

from app.core.config import settings
from app.services.ai_errors import AIErrorReason, AIServiceError, provider_error


class EmbeddingServiceError(AIServiceError):
    """Raised when the optional embedding service cannot be used safely."""


@lru_cache
def _get_client():
    if not settings.ecnu_api_key:
        raise EmbeddingServiceError(AIErrorReason.MISSING_CONFIGURATION, "未配置 ECNU_API_KEY")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise EmbeddingServiceError(AIErrorReason.DEPENDENCY_MISSING, "未安装 openai 依赖") from exc
    return OpenAI(
        api_key=settings.ecnu_api_key,
        base_url=settings.ecnu_base_url,
        timeout=settings.ai_timeout_seconds,
        max_retries=1,
    )


def _response_vectors(response: Any, expected_count: int) -> list[list[float]]:
    try:
        items = list(response.data)
    except (AttributeError, TypeError) as exc:
        raise EmbeddingServiceError(
            AIErrorReason.MALFORMED_RESPONSE,
            "向量服务返回结构不完整",
        ) from exc
    if not items and expected_count:
        raise EmbeddingServiceError(AIErrorReason.EMPTY_RESPONSE, "向量服务返回了空内容")
    if len(items) != expected_count:
        raise EmbeddingServiceError(AIErrorReason.MALFORMED_RESPONSE, "向量返回数量与输入不一致")

    indices = [getattr(item, "index", None) for item in items]
    if any(index is not None for index in indices):
        if not all(isinstance(index, int) and not isinstance(index, bool) for index in indices):
            raise EmbeddingServiceError(AIErrorReason.MALFORMED_RESPONSE, "向量返回顺序索引不完整")
        if sorted(indices) != list(range(expected_count)):
            raise EmbeddingServiceError(AIErrorReason.MALFORMED_RESPONSE, "向量返回顺序索引无效")
        items = [item for _, item in sorted(zip(indices, items), key=lambda pair: pair[0])]

    vectors: list[list[float]] = []
    for item in items:
        vector = getattr(item, "embedding", None)
        if not isinstance(vector, (list, tuple)) or not vector:
            raise EmbeddingServiceError(AIErrorReason.MALFORMED_RESPONSE, "向量内容为空或无效")
        try:
            clean_vector = [float(value) for value in vector]
        except (TypeError, ValueError) as exc:
            raise EmbeddingServiceError(AIErrorReason.MALFORMED_RESPONSE, "向量包含非数值内容") from exc
        if not all(math.isfinite(value) for value in clean_vector):
            raise EmbeddingServiceError(AIErrorReason.MALFORMED_RESPONSE, "向量包含非有限数值")
        vectors.append(clean_vector)
    if len({len(vector) for vector in vectors}) != 1:
        raise EmbeddingServiceError(AIErrorReason.MALFORMED_RESPONSE, "向量维度不一致")
    return vectors


def get_embedding(text: str) -> list[float]:
    """Compatibility helper for a single embedding."""
    return get_embeddings([text])[0]


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Embed texts in bounded provider batches while preserving alignment."""
    if not isinstance(texts, list):
        raise TypeError("texts 必须是字符串列表")
    if not texts:
        return []
    invalid = [index for index, text in enumerate(texts) if not isinstance(text, str) or not text.strip()]
    if invalid:
        raise ValueError(f"texts 包含空白或无效文本，位置：{invalid[0]}")
    batch_size = settings.embedding_batch_size
    if not isinstance(batch_size, int) or not 1 <= batch_size <= 256:
        raise EmbeddingServiceError(AIErrorReason.MISSING_CONFIGURATION, "embedding_batch_size 配置无效")
    max_chars = settings.embedding_max_input_chars
    if not isinstance(max_chars, int) or not 1 <= max_chars <= 100_000:
        raise EmbeddingServiceError(AIErrorReason.MISSING_CONFIGURATION, "embedding_max_input_chars 配置无效")
    bounded_texts = [text[:max_chars] for text in texts]

    vectors: list[list[float]] = []
    try:
        client = _get_client()
        for start in range(0, len(bounded_texts), batch_size):
            batch = bounded_texts[start:start + batch_size]
            response = client.embeddings.create(model=settings.ecnu_embedding_model, input=batch)
            batch_vectors = _response_vectors(response, len(batch))
            if vectors and len(batch_vectors[0]) != len(vectors[0]):
                raise EmbeddingServiceError(AIErrorReason.MALFORMED_RESPONSE, "不同批次的向量维度不一致")
            vectors.extend(batch_vectors)
        return vectors
    except EmbeddingServiceError:
        raise
    except Exception as exc:
        raise provider_error(EmbeddingServiceError, "向量服务", exc) from None
