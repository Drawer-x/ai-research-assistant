"""Small shared parser for JSON objects returned by language models."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any

from app.services.ai_errors import AIErrorReason, AIServiceError


class StructuredOutputError(AIServiceError):
    """Raised when an LLM response cannot satisfy a structured contract."""


_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from plain text or a fenced/explanatory response."""
    if not isinstance(text, str) or not text.strip():
        raise StructuredOutputError(AIErrorReason.EMPTY_RESPONSE, "模型返回了空内容")
    cleaned = _FENCE_RE.sub("", text.strip()).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        candidates: list[tuple[int, int, dict[str, Any]]] = []
        for match in re.finditer(r"\{", cleaned):
            try:
                candidate, consumed = decoder.raw_decode(cleaned[match.start():])
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict):
                candidates.append((match.start(), match.start() + consumed, candidate))
        top_level = [
            candidate
            for candidate in candidates
            if not any(
                outer_start <= candidate[0]
                and candidate[1] <= outer_end
                and (outer_start, outer_end) != candidate[:2]
                for outer_start, outer_end, _ in candidates
            )
        ]
        if not top_level:
            raise StructuredOutputError(
                AIErrorReason.MALFORMED_RESPONSE,
                "模型返回的 JSON 无法解析",
            )
        if len(top_level) != 1:
            raise StructuredOutputError(
                AIErrorReason.MALFORMED_RESPONSE,
                "模型返回包含多个 JSON 对象",
            )
        value = top_level[0][2]
    if not isinstance(value, dict):
        raise StructuredOutputError(
            AIErrorReason.MALFORMED_RESPONSE,
            "模型返回值不是 JSON 对象",
        )
    return value


def require_string_fields(data: dict[str, Any], fields: Iterable[str]) -> dict[str, str]:
    """Return required non-empty string fields or reject the whole response."""
    output: dict[str, str] = {}
    for field in fields:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise StructuredOutputError(
                AIErrorReason.MALFORMED_RESPONSE,
                f"模型返回缺少有效字段：{field}",
            )
        output[field] = value.strip()
    return output
