"""Shared, non-sensitive error model for optional external AI services."""

from __future__ import annotations

from enum import Enum
from typing import TypeVar


class AIErrorReason(str, Enum):
    MISSING_CONFIGURATION = "missing_configuration"
    DEPENDENCY_MISSING = "dependency_missing"
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    EMPTY_RESPONSE = "empty_response"
    MALFORMED_RESPONSE = "malformed_response"


class AIServiceError(RuntimeError):
    """An expected external-service failure safe to expose to callers."""

    def __init__(self, reason: AIErrorReason, message: str):
        super().__init__(message)
        self.reason = reason


ErrorT = TypeVar("ErrorT", bound=AIServiceError)


def provider_error(error_type: type[ErrorT], service_name: str, exc: Exception) -> ErrorT:
    """Map provider exceptions without copying response bodies or credentials."""
    class_name = type(exc).__name__.lower()
    is_timeout = isinstance(exc, TimeoutError) or "timeout" in class_name
    if is_timeout:
        return error_type(AIErrorReason.TIMEOUT, f"{service_name}请求超时")
    return error_type(AIErrorReason.PROVIDER_ERROR, f"{service_name}调用失败")
